"""
Room management API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.exception import NotFoundError
from app.schemas.response import ApiResponse, PagedData, PagedResponse
from app.schemas.room import (
    RoomCreate,
    RoomDetailResponse,
    RoomExtensionCreate,
    RoomListResponse,
    RoomResponse,
    RoomUpdate,
)
from app.services.room_service import RoomService, get_room_service

router = APIRouter()


@router.post("", response_model=ApiResponse[RoomResponse])
async def create_room(
    room_in: RoomCreate,
    extension_in: Optional[RoomExtensionCreate] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new room.

    - **room_in**: Room creation data (required)
    - **extension_in**: Optional room extension data
    """
    room_service: RoomService = get_room_service()
    room = await room_service.create_room(db, room_in=room_in, extension_in=extension_in)
    return ApiResponse(
        code=200,
        message="Room created successfully",
        data=RoomResponse.model_validate(room),
    )


@router.get("", response_model=PagedResponse[RoomResponse])
async def list_rooms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    hotel_id: Optional[str] = Query(None, description="Filter by hotel ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    expedia_room_id: Optional[str] = Query(None, description="Filter by Expedia Room ID"),
    search: Optional[str] = Query(None, description="Search in name_cn, name_en, room_type_code"),
    db: AsyncSession = Depends(get_db),
):
    """
    List rooms with pagination and filters.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **hotel_id**: Filter by hotel ID
    - **is_active**: Filter by active status
    - **expedia_room_id**: Filter by Expedia Room ID
    - **search**: Search in name_cn, name_en, room_type_code
    """
    room_service: RoomService = get_room_service()
    rooms, total = await room_service.list_rooms(
        db,
        page=page,
        page_size=page_size,
        hotel_id=hotel_id,
        is_active=is_active,
        expedia_room_id=expedia_room_id,
        search=search,
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


@router.get("/hotels/{hotel_id}/rooms", response_model=RoomListResponse)
async def get_hotel_rooms(
    hotel_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all rooms for a specific hotel.

    - **hotel_id**: Hotel ID (required)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    - **is_active**: Filter by active status
    """
    room_service: RoomService = get_room_service()
    rooms, total = await room_service.get_rooms_by_hotel(
        db,
        hotel_id=hotel_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    return RoomListResponse(
        rooms=[RoomResponse.model_validate(r) for r in rooms],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{room_id}", response_model=ApiResponse[RoomDetailResponse])
async def get_room(
    room_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single room by ID with its extension details.

    - **room_id**: Room ID (required)
    """
    room_service: RoomService = get_room_service()
    room, extension = await room_service.get_room_with_extension(db, room_id=room_id)

    if not room:
        raise NotFoundError(message="Room not found")

    return ApiResponse(
        code=200,
        message="success",
        data=RoomDetailResponse.model_validate(room),
    )


@router.put("/{room_id}", response_model=ApiResponse[RoomResponse])
async def update_room(
    room_id: str,
    room_in: RoomUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a room.

    - **room_id**: Room ID (required)
    - **room_in**: Room update data
    """
    room_service: RoomService = get_room_service()
    room = await room_service.update_room(db, room_id=room_id, room_in=room_in)

    if not room:
        raise NotFoundError(message="Room not found")

    return ApiResponse(
        code=200,
        message="Room updated successfully",
        data=RoomResponse.model_validate(room),
    )


@router.delete("/{room_id}", response_model=ApiResponse[RoomResponse])
async def delete_room(
    room_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a room.

    - **room_id**: Room ID (required)
    """
    room_service: RoomService = get_room_service()
    deleted = await room_service.delete_room(db, room_id=room_id)

    if not deleted:
        raise NotFoundError(message="Room not found")

    return ApiResponse(
        code=200,
        message="Room deleted successfully",
        data=None,
    )
