"""
Booking.com API endpoints for hotel and room management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.exception import BadRequestError, NotFoundError
from app.schemas.booking import (
    BookingHotelCreate,
    BookingHotelUpdate,
    BookingHotelResponse,
    BookingHotelWithExtension,
    BookingHotelQuery,
    BookingHotelListResponse,
    BookingHotelExtensionCreate,
    BookingHotelExtensionUpdate,
    BookingRoomCreate,
    BookingRoomUpdate,
    BookingRoomResponse,
    BookingRoomWithExtension,
    BookingRoomQuery,
    BookingRoomListResponse,
    BookingRoomExtensionCreate,
    BookingRoomExtensionUpdate,
)
from app.schemas.response import ApiResponse, paged_response
from app.services.booking_hotel_service import booking_hotel
from app.services.booking_room_service import booking_room

router = APIRouter()


# ============== Booking Hotel Endpoints ==============


@router.get("", response_model=ApiResponse[BookingHotelListResponse])
async def list_booking_hotels(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    source_hotel_id: Optional[str] = Query(None, description="Filter by source hotel ID"),
    name: Optional[str] = Query(None, description="Search by hotel name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List booking hotels with pagination and filtering.
    """
    query_params = BookingHotelQuery(
        source=source,
        source_hotel_id=source_hotel_id,
        name=name,
        city=city,
        province=province,
        country_code=country_code,
        brand=brand,
        is_active=is_active,
    )

    skip = (page - 1) * page_size
    items = await booking_hotel.search(db, query_params=query_params, skip=skip, limit=page_size)
    total = await booking_hotel.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[BookingHotelResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[BookingHotelResponse], status_code=status.HTTP_201_CREATED)
async def create_booking_hotel(
    hotel_in: BookingHotelCreate,
    extension_in: Optional[BookingHotelExtensionCreate] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking hotel.
    """
    hotel = await booking_hotel.create_with_extension(
        db,
        obj_in=hotel_in,
        extension_data=extension_in.model_dump() if extension_in else None,
    )
    return ApiResponse(
        code=201,
        message="Booking hotel created successfully",
        data=BookingHotelResponse.model_validate(hotel),
    )


@router.get("/active", response_model=ApiResponse[list[BookingHotelResponse]])
async def get_active_booking_hotels(
    city: Optional[str] = Query(None, description="Filter by city"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active booking hotels.
    """
    query_params = BookingHotelQuery(is_active=True, city=city, brand=brand)
    items = await booking_hotel.search(db, query_params=query_params, skip=0, limit=1000)
    return ApiResponse(
        code=200,
        message="success",
        data=[BookingHotelResponse.model_validate(item) for item in items],
    )


@router.get("/{hotel_id}", response_model=ApiResponse[BookingHotelWithExtension])
async def get_booking_hotel(
    hotel_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific booking hotel by ID with extension data.
    """
    result = await booking_hotel.get_with_extension(db, id=hotel_id)
    if not result:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": hotel_id},
        )

    hotel, extension = result
    response = BookingHotelWithExtension(
        **BookingHotelResponse.model_validate(hotel).model_dump(),
        extension=extension,
    )
    return ApiResponse(
        code=200,
        message="success",
        data=response,
    )


@router.put("/{hotel_id}", response_model=ApiResponse[BookingHotelResponse])
async def update_booking_hotel(
    hotel_id: str,
    hotel_in: BookingHotelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a booking hotel.
    """
    hotel = await booking_hotel.get(db, id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": hotel_id},
        )

    updated = await booking_hotel.update(db, db_obj=hotel, obj_in=hotel_in)
    return ApiResponse(
        code=200,
        message="Booking hotel updated successfully",
        data=BookingHotelResponse.model_validate(updated),
    )


@router.delete("/{hotel_id}", response_model=ApiResponse[dict])
async def delete_booking_hotel(
    hotel_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a booking hotel.
    """
    deleted = await booking_hotel.delete(db, id=hotel_id)
    if not deleted:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": hotel_id},
        )

    return ApiResponse(
        code=200,
        message="Booking hotel deleted successfully",
        data={"id": hotel_id},
    )


@router.get("/{hotel_id}/extension", response_model=ApiResponse[BookingHotelExtensionCreate])
async def get_booking_hotel_extension(
    hotel_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking hotel extension.
    """
    hotel = await booking_hotel.get(db, id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": hotel_id},
        )

    extension = await booking_hotel.get_extension(db, hotel_id=hotel_id)
    if not extension:
        raise NotFoundError(
            message="Booking hotel extension not found",
            details={"hotel_id": hotel_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=extension,
    )


@router.put("/{hotel_id}/extension", response_model=ApiResponse[dict])
async def update_booking_hotel_extension(
    hotel_id: str,
    extension_in: BookingHotelExtensionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update or create booking hotel extension.
    """
    hotel = await booking_hotel.get(db, id=hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": hotel_id},
        )

    extension = await booking_hotel.update_extension(
        db,
        hotel_id=hotel_id,
        obj_in=extension_in.model_dump(exclude_unset=True),
    )

    return ApiResponse(
        code=200,
        message="Booking hotel extension updated successfully",
        data=extension,
    )


# ============== Booking Room Endpoints ==============


@router.get("/rooms", response_model=ApiResponse[BookingRoomListResponse])
async def list_booking_rooms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    hotel_id: Optional[str] = Query(None, description="Filter by hotel ID"),
    source: Optional[str] = Query(None, description="Filter by source"),
    source_room_id: Optional[str] = Query(None, description="Filter by source room ID"),
    room_name: Optional[str] = Query(None, description="Search by room name"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    bed_type: Optional[str] = Query(None, description="Filter by bed type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List booking rooms with pagination and filtering.
    """
    query_params = BookingRoomQuery(
        source=source,
        source_room_id=source_room_id,
        hotel_id=hotel_id,
        room_name=room_name,
        room_type=room_type,
        bed_type=bed_type,
        is_active=is_active,
    )

    skip = (page - 1) * page_size
    items = await booking_room.search(db, query_params=query_params, skip=skip, limit=page_size)
    total = await booking_room.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[BookingRoomResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/rooms", response_model=ApiResponse[BookingRoomResponse], status_code=status.HTTP_201_CREATED)
async def create_booking_room(
    room_in: BookingRoomCreate,
    extension_in: Optional[BookingRoomExtensionCreate] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking room.
    """
    # Verify hotel exists
    hotel = await booking_hotel.get(db, id=room_in.hotel_id)
    if not hotel:
        raise NotFoundError(
            message="Booking hotel not found",
            details={"hotel_id": room_in.hotel_id},
        )

    room = await booking_room.create_with_extension(
        db,
        obj_in=room_in,
        extension_data=extension_in.model_dump() if extension_in else None,
    )
    return ApiResponse(
        code=201,
        message="Booking room created successfully",
        data=BookingRoomResponse.model_validate(room),
    )


@router.get("/rooms/by-hotel/{hotel_id}", response_model=ApiResponse[list[BookingRoomResponse]])
async def list_booking_rooms_by_hotel(
    hotel_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all rooms for a specific hotel.
    """
    items = await booking_room.get_by_hotel(db, hotel_id=hotel_id, skip=skip, limit=limit)
    return ApiResponse(
        code=200,
        message="success",
        data=[BookingRoomResponse.model_validate(item) for item in items],
    )


@router.get("/rooms/{room_id}", response_model=ApiResponse[BookingRoomWithExtension])
async def get_booking_room(
    room_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific booking room by ID with extension data.
    """
    result = await booking_room.get_with_extension(db, id=room_id)
    if not result:
        raise NotFoundError(
            message="Booking room not found",
            details={"room_id": room_id},
        )

    room, extension = result
    response = BookingRoomWithExtension(
        **BookingRoomResponse.model_validate(room).model_dump(),
        extension=extension,
    )
    return ApiResponse(
        code=200,
        message="success",
        data=response,
    )


@router.put("/rooms/{room_id}", response_model=ApiResponse[BookingRoomResponse])
async def update_booking_room(
    room_id: str,
    room_in: BookingRoomUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a booking room.
    """
    room = await booking_room.get(db, id=room_id)
    if not room:
        raise NotFoundError(
            message="Booking room not found",
            details={"room_id": room_id},
        )

    updated = await booking_room.update(db, db_obj=room, obj_in=room_in)
    return ApiResponse(
        code=200,
        message="Booking room updated successfully",
        data=BookingRoomResponse.model_validate(updated),
    )


@router.delete("/rooms/{room_id}", response_model=ApiResponse[dict])
async def delete_booking_room(
    room_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a booking room.
    """
    deleted = await booking_room.delete(db, id=room_id)
    if not deleted:
        raise NotFoundError(
            message="Booking room not found",
            details={"room_id": room_id},
        )

    return ApiResponse(
        code=200,
        message="Booking room deleted successfully",
        data={"id": room_id},
    )


@router.get("/rooms/{room_id}/extension", response_model=ApiResponse[BookingRoomExtensionCreate])
async def get_booking_room_extension(
    room_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking room extension.
    """
    room = await booking_room.get(db, id=room_id)
    if not room:
        raise NotFoundError(
            message="Booking room not found",
            details={"room_id": room_id},
        )

    extension = await booking_room.get_extension(db, room_id=room_id)
    if not extension:
        raise NotFoundError(
            message="Booking room extension not found",
            details={"room_id": room_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=extension,
    )


@router.put("/rooms/{room_id}/extension", response_model=ApiResponse[dict])
async def update_booking_room_extension(
    room_id: str,
    extension_in: BookingRoomExtensionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update or create booking room extension.
    """
    room = await booking_room.get(db, id=room_id)
    if not room:
        raise NotFoundError(
            message="Booking room not found",
            details={"room_id": room_id},
        )

    extension = await booking_room.update_extension(
        db,
        room_id=room_id,
        obj_in=extension_in.model_dump(exclude_unset=True),
    )

    return ApiResponse(
        code=200,
        message="Booking room extension updated successfully",
        data=extension,
    )
