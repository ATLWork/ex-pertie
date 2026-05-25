"""
Hotel and Room management API endpoints.

This module provides two sets of endpoints:
1. Hotel CRUD: /api/v1/hotels
2. Room CRUD (nested under hotels): /api/v1/hotels/{hotel_id}/rooms
"""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.middleware.exception import BadRequestError, NotFoundError
from app.models.hotel import Hotel, HotelBrand, HotelStatus
from app.models.user import User
from app.schemas.hotel import (
    HotelCreate,
    HotelQuery,
    HotelResponse,
    HotelUpdate,
)
from app.schemas.response import ApiResponse, PagedData, PagedResponse
from app.schemas.room import (
    RoomCreate,
    RoomDetailResponse,
    RoomExtensionCreate,
    RoomExtensionUpdate,
    RoomListResponse,
    RoomResponse,
    RoomUpdate,
)
from app.services.hotel_service import hotel_service
from app.services.hotel_search_service import hotel_search
from app.services.hotel_room_link_service import get_hotel_room_link_service
from app.services.room_service import RoomService, get_room_service

router = APIRouter()


# ==================== Hotel CRUD Endpoints ====================

@router.post("", response_model=ApiResponse[HotelResponse], status_code=201)
async def create_hotel(
    hotel_in: HotelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new hotel.

    - **name_cn**: Hotel name in Chinese (required)
    - **brand**: Hotel brand (default: atour)
    - **status**: Hotel status (default: draft)
    - **province**: Province/State (required)
    - **city**: City (required)
    - **address_cn**: Address in Chinese (required)
    - **expedia_hotel_id**: Expedia Hotel ID (optional, unique)
    """
    # Check if expedia_hotel_id already exists
    if hotel_in.expedia_hotel_id:
        exists = await hotel_service.exists_by_expedia_id(
            db, expedia_hotel_id=hotel_in.expedia_hotel_id
        )
        if exists:
            raise BadRequestError(
                message="Hotel with this Expedia ID already exists",
                details={"expedia_hotel_id": hotel_in.expedia_hotel_id},
            )

    hotel = await hotel_service.create_hotel(db, hotel_in=hotel_in)
    return ApiResponse(
        code=201,
        message="Hotel created successfully",
        data=HotelResponse.model_validate(hotel),
    )


@router.get("", response_model=PagedResponse[HotelResponse])
async def list_hotels(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    brand: Optional[HotelBrand] = Query(None, description="Filter by hotel brand"),
    status: Optional[HotelStatus] = Query(None, description="Filter by hotel status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    name: Optional[str] = Query(None, description="Search by hotel name"),
    expedia_hotel_id: Optional[str] = Query(None, description="Filter by Expedia Hotel ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List hotels with pagination and filtering.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **brand**: Filter by hotel brand
    - **status**: Filter by hotel status
    - **city**: Filter by city
    - **province**: Filter by province
    - **name**: Search by hotel name
    - **expedia_hotel_id**: Filter by Expedia Hotel ID
    """
    query = HotelQuery(
        name=name,
        brand=brand,
        status=status,
        city=city,
        province=province,
        expedia_hotel_id=expedia_hotel_id,
    )

    hotels, total = await hotel_service.list_hotels(
        db, query=query, page=page, page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[HotelResponse.model_validate(h) for h in hotels],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/search", response_model=PagedResponse[HotelResponse])
async def search_hotels(
    keyword: Optional[str] = Query(None, description="Keyword to search in hotel names"),
    brand: Optional[HotelBrand] = Query(None, description="Filter by hotel brand"),
    status: Optional[HotelStatus] = Query(None, description="Filter by hotel status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    order_by: str = Query("updated_at", description="Field to order by"),
    order_desc: bool = Query(True, description="Whether to order in descending order"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Comprehensive hotel search with multiple conditions.

    - **keyword**: Keyword to search in hotel names (fuzzy match)
    - **brand**: Filter by hotel brand
    - **status**: Filter by hotel status
    - **city**: Filter by city
    - **province**: Filter by province
    - **is_active**: Filter by active status
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **order_by**: Field to order by (default: updated_at)
    - **order_desc**: Whether to order in descending order (default: True)
    """
    skip = (page - 1) * page_size

    hotels, total = await hotel_search.search_hotels(
        db,
        keyword=keyword,
        brand=brand,
        status=status,
        city=city,
        province=province,
        is_active=is_active,
        skip=skip,
        limit=page_size,
        order_by=order_by,
        order_desc=order_desc,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[HotelResponse.model_validate(h) for h in hotels],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{hotel_id}", response_model=ApiResponse[HotelResponse])
async def get_hotel(
    hotel_id: str = Path(..., description="Hotel ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a hotel by ID.

    - **hotel_id**: Hotel ID (required)
    """
    hotel = await hotel_service.get_hotel(db, hotel_id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Hotel not found",
            details={"hotel_id": hotel_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=HotelResponse.model_validate(hotel),
    )


@router.put("/{hotel_id}", response_model=ApiResponse[HotelResponse])
async def update_hotel(
    hotel_id: str = Path(..., description="Hotel ID"),
    hotel_in: HotelUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing hotel.

    - **hotel_id**: Hotel ID (required)
    - All fields are optional for partial update
    """
    # Check if hotel exists
    hotel = await hotel_service.get_hotel(db, hotel_id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Hotel not found",
            details={"hotel_id": hotel_id},
        )

    # Check if expedia_hotel_id is being changed to an existing one
    if hotel_in.expedia_hotel_id and hotel_in.expedia_hotel_id != hotel.expedia_hotel_id:
        exists = await hotel_service.exists_by_expedia_id(
            db, expedia_hotel_id=hotel_in.expedia_hotel_id
        )
        if exists:
            raise BadRequestError(
                message="Hotel with this Expedia ID already exists",
                details={"expedia_hotel_id": hotel_in.expedia_hotel_id},
            )

    updated_hotel = await hotel_service.update_hotel(db, hotel_id=hotel_id, hotel_in=hotel_in)
    return ApiResponse(
        code=200,
        message="Hotel updated successfully",
        data=HotelResponse.model_validate(updated_hotel),
    )


@router.delete("/{hotel_id}", response_model=ApiResponse[HotelResponse])
async def delete_hotel(
    hotel_id: str = Path(..., description="Hotel ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a hotel by ID.

    - **hotel_id**: Hotel ID (required)
    """
    # Check if hotel exists
    hotel = await hotel_service.get_hotel(db, hotel_id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Hotel not found",
            details={"hotel_id": hotel_id},
        )

    deleted = await hotel_service.delete_hotel(db, hotel_id=hotel_id)
    if not deleted:
        raise BadRequestError(
            message="Failed to delete hotel",
            details={"hotel_id": hotel_id},
        )

    return ApiResponse(
        code=200,
        message="Hotel deleted successfully",
        data=HotelResponse.model_validate(hotel),
    )


# ==================== Room CRUD Endpoints (Nested under Hotels) ====================

@router.post("/{hotel_id}/rooms", response_model=ApiResponse[RoomResponse], status_code=201)
async def create_hotel_room(
    hotel_id: str = Path(..., description="Hotel ID"),
    room_in: RoomCreate = ...,
    extension_in: Optional[RoomExtensionCreate] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new room for a hotel.

    - **hotel_id**: Hotel ID (required)
    - **room_in**: Room creation data (required)
    - **extension_in**: Optional room extension data
    """
    # Verify hotel exists
    hotel = await hotel_service.get_hotel(db, hotel_id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Hotel not found",
            details={"hotel_id": hotel_id},
        )

    # Ensure room is linked to the correct hotel
    if room_in.hotel_id != hotel_id:
        raise BadRequestError(
            message="Room hotel_id does not match the path parameter",
            details={"expected_hotel_id": hotel_id, "provided_hotel_id": room_in.hotel_id},
        )

    room_service: RoomService = get_room_service()
    room = await room_service.create_room(db, room_in=room_in, extension_in=extension_in)
    return ApiResponse(
        code=201,
        message="Room created successfully",
        data=RoomResponse.model_validate(room),
    )


@router.get("/{hotel_id}/rooms", response_model=PagedResponse[RoomResponse])
async def list_hotel_rooms(
    hotel_id: str = Path(..., description="Hotel ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name_cn, name_en, room_type_code"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List rooms for a specific hotel with pagination and filters.

    - **hotel_id**: Hotel ID (required)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **is_active**: Filter by active status
    - **search**: Search in name_cn, name_en, room_type_code
    """
    # Verify hotel exists
    hotel = await hotel_service.get_hotel(db, hotel_id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Hotel not found",
            details={"hotel_id": hotel_id},
        )

    room_service: RoomService = get_room_service()
    skip = (page - 1) * page_size
    rooms, total = await room_service.get_rooms_by_hotel(
        db,
        hotel_id=hotel_id,
        skip=skip,
        limit=page_size,
        is_active=is_active,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[RoomResponse.model_validate(r) for r in rooms],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{hotel_id}/rooms/{room_id}", response_model=ApiResponse[RoomDetailResponse])
async def get_hotel_room(
    hotel_id: str = Path(..., description="Hotel ID"),
    room_id: str = Path(..., description="Room ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single room by ID with its extension details.

    - **hotel_id**: Hotel ID (required)
    - **room_id**: Room ID (required)
    """
    room_service: RoomService = get_room_service()
    room, extension = await room_service.get_room_with_extension(db, room_id=room_id)

    if not room:
        raise NotFoundError(
            message="Room not found",
            details={"room_id": room_id},
        )

    # Verify room belongs to the hotel
    if room.hotel_id != hotel_id:
        raise NotFoundError(
            message="Room not found in this hotel",
            details={"room_id": room_id, "hotel_id": hotel_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=RoomDetailResponse.model_validate(room),
    )


@router.put("/{hotel_id}/rooms/{room_id}", response_model=ApiResponse[RoomResponse])
async def update_hotel_room(
    hotel_id: str = Path(..., description="Hotel ID"),
    room_id: str = Path(..., description="Room ID"),
    room_in: RoomUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a room.

    - **hotel_id**: Hotel ID (required)
    - **room_id**: Room ID (required)
    - **room_in**: Room update data
    """
    room_service: RoomService = get_room_service()

    # First verify room exists
    room = await room_service.get_room(db, room_id=room_id)
    if not room:
        raise NotFoundError(
            message="Room not found",
            details={"room_id": room_id},
        )

    # Verify room belongs to the hotel
    if room.hotel_id != hotel_id:
        raise NotFoundError(
            message="Room not found in this hotel",
            details={"room_id": room_id, "hotel_id": hotel_id},
        )

    # If updating hotel_id, verify target hotel exists
    if room_in.hotel_id and room_in.hotel_id != hotel_id:
        target_hotel = await hotel_service.get_hotel(db, hotel_id=room_in.hotel_id)
        if not target_hotel:
            raise NotFoundError(
                message="Target hotel not found",
                details={"hotel_id": room_in.hotel_id},
            )

    updated_room = await room_service.update_room(db, room_id=room_id, room_in=room_in)
    return ApiResponse(
        code=200,
        message="Room updated successfully",
        data=RoomResponse.model_validate(updated_room),
    )


@router.delete("/{hotel_id}/rooms/{room_id}", response_model=ApiResponse[RoomResponse])
async def delete_hotel_room(
    hotel_id: str = Path(..., description="Hotel ID"),
    room_id: str = Path(..., description="Room ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a room.

    - **hotel_id**: Hotel ID (required)
    - **room_id**: Room ID (required)
    """
    room_service: RoomService = get_room_service()

    # First verify room exists
    room = await room_service.get_room(db, room_id=room_id)
    if not room:
        raise NotFoundError(
            message="Room not found",
            details={"room_id": room_id},
        )

    # Verify room belongs to the hotel
    if room.hotel_id != hotel_id:
        raise NotFoundError(
            message="Room not found in this hotel",
            details={"room_id": room_id, "hotel_id": hotel_id},
        )

    deleted = await room_service.delete_room(db, room_id=room_id)
    if not deleted:
        raise BadRequestError(
            message="Failed to delete room",
            details={"room_id": room_id},
        )

    return ApiResponse(
        code=200,
        message="Room deleted successfully",
        data=RoomResponse.model_validate(room),
    )


@router.put("/{hotel_id}/rooms/{room_id}/extension", response_model=ApiResponse[RoomDetailResponse])
async def update_hotel_room_extension(
    hotel_id: str = Path(..., description="Hotel ID"),
    room_id: str = Path(..., description="Room ID"),
    extension_in: RoomExtensionUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update room extension details.

    - **hotel_id**: Hotel ID (required)
    - **room_id**: Room ID (required)
    - **extension_in**: Room extension update data
    """
    room_service: RoomService = get_room_service()

    # First verify room exists
    room = await room_service.get_room(db, room_id=room_id)
    if not room:
        raise NotFoundError(
            message="Room not found",
            details={"room_id": room_id},
        )

    # Verify room belongs to the hotel
    if room.hotel_id != hotel_id:
        raise NotFoundError(
            message="Room not found in this hotel",
            details={"room_id": room_id, "hotel_id": hotel_id},
        )

    updated_extension = await room_service.update_room_extension(
        db, room_id=room_id, extension_in=extension_in
    )
    updated_room = await room_service.get_room(db, room_id=room_id)

    return ApiResponse(
        code=200,
        message="Room extension updated successfully",
        data=RoomDetailResponse.model_validate(updated_room),
    )