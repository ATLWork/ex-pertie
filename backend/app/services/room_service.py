"""
Room CRUD service.
"""

from typing import List, Optional, Tuple

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Room
from app.models.room import RoomExtension
from app.schemas.room import (
    RoomCreate,
    RoomExtensionCreate,
    RoomExtensionUpdate,
    RoomUpdate,
)


class RoomService:
    """
    Room CRUD service.
    Provides database operations for Room and RoomExtension models.
    """

    async def create_room(
        self,
        db: AsyncSession,
        *,
        room_in: RoomCreate,
        extension_in: Optional[RoomExtensionCreate] = None,
    ) -> Room:
        """
        Create a new room.

        Args:
            db: Database session
            room_in: Room creation data
            extension_in: Optional room extension data

        Returns:
            Created room instance
        """
        room_data = room_in.model_dump()
        db_room = Room(**room_data)
        db.add(db_room)
        await db.flush()

        if extension_in:
            extension_data = extension_in.model_dump()
            db_extension = RoomExtension(**extension_data)
            db.add(db_extension)
            await db.flush()

        await db.refresh(db_room)
        return db_room

    async def get_room(self, db: AsyncSession, *, room_id: str) -> Optional[Room]:
        """
        Get a single room by ID.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Room instance or None
        """
        result = await db.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()

    async def get_room_with_extension(
        self, db: AsyncSession, *, room_id: str
    ) -> Tuple[Optional[Room], Optional[RoomExtension]]:
        """
        Get a room by ID with its extension.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Tuple of (Room, RoomExtension) or (None, None)
        """
        room = await self.get_room(db, room_id=room_id)
        if not room:
            return None, None

        ext_result = await db.execute(
            select(RoomExtension).where(RoomExtension.room_id == room_id)
        )
        extension = ext_result.scalar_one_or_none()
        return room, extension

    async def get_room_by_expedia_id(
        self, db: AsyncSession, *, expedia_room_id: str
    ) -> Optional[Room]:
        """
        Get a room by Expedia Room ID.

        Args:
            db: Database session
            expedia_room_id: Expedia Room ID

        Returns:
            Room instance or None
        """
        result = await db.execute(
            select(Room).where(Room.expedia_room_id == expedia_room_id)
        )
        return result.scalar_one_or_none()

    async def get_rooms_by_hotel(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Room], int]:
        """
        Get all rooms for a hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Optional filter by active status

        Returns:
            Tuple of (rooms list, total count)
        """
        filters = [Room.hotel_id == hotel_id]
        if is_active is not None:
            filters.append(Room.is_active == is_active)

        # Count query
        count_query = select(Room).where(and_(*filters))
        count_result = await db.execute(count_query)
        total = len(list(count_result.scalars().all()))

        # Data query
        query = (
            select(Room)
            .where(and_(*filters))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        rooms = list(result.scalars().all())

        return rooms, total

    async def update_room(
        self,
        db: AsyncSession,
        *,
        room_id: str,
        room_in: RoomUpdate,
    ) -> Optional[Room]:
        """
        Update a room.

        Args:
            db: Database session
            room_id: Room ID
            room_in: Room update data

        Returns:
            Updated room instance or None
        """
        room = await self.get_room(db, room_id=room_id)
        if not room:
            return None

        update_data = room_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(room, field):
                setattr(room, field, value)

        db.add(room)
        await db.flush()
        await db.refresh(room)
        return room

    async def update_room_extension(
        self,
        db: AsyncSession,
        *,
        room_id: str,
        extension_in: RoomExtensionUpdate,
    ) -> Optional[RoomExtension]:
        """
        Update room extension.

        Args:
            db: Database session
            room_id: Room ID
            extension_in: Extension update data

        Returns:
            Updated extension instance or None
        """
        result = await db.execute(
            select(RoomExtension).where(RoomExtension.room_id == room_id)
        )
        extension = result.scalar_one_or_none()

        if not extension:
            # Create extension if not exists
            extension = RoomExtension(room_id=room_id)
            db.add(extension)

        update_data = extension_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(extension, field):
                setattr(extension, field, value)

        await db.flush()
        await db.refresh(extension)
        return extension

    async def delete_room(self, db: AsyncSession, *, room_id: str) -> bool:
        """
        Delete a room.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            True if deleted, False if not found
        """
        room = await self.get_room(db, room_id=room_id)
        if not room:
            return False

        await db.delete(room)
        await db.flush()
        return True

    async def list_rooms(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        hotel_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        expedia_room_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Room], int]:
        """
        List rooms with pagination and filters.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Items per page
            hotel_id: Filter by hotel ID
            is_active: Filter by active status
            expedia_room_id: Filter by Expedia Room ID
            search: Search in name_cn, name_en, room_type_code

        Returns:
            Tuple of (rooms list, total count)
        """
        filters = []

        if hotel_id is not None:
            filters.append(Room.hotel_id == hotel_id)
        if is_active is not None:
            filters.append(Room.is_active == is_active)
        if expedia_room_id is not None:
            filters.append(Room.expedia_room_id == expedia_room_id)
        if search:
            search_filter = or_(
                Room.name_cn.ilike(f"%{search}%"),
                Room.name_en.ilike(f"%{search}%"),
                Room.room_type_code.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        # Build query
        query = select(Room)
        if filters:
            query = query.where(and_(*filters))

        # Count total
        count_query = select(Room)
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await db.execute(count_query)
        total = len(list(count_result.scalars().all()))

        # Apply pagination
        skip = (page - 1) * page_size
        query = query.offset(skip).limit(page_size)

        result = await db.execute(query)
        rooms = list(result.scalars().all())

        return rooms, total

    async def get_room_count_by_hotel(
        self, db: AsyncSession, *, hotel_id: str, is_active: Optional[bool] = None
    ) -> int:
        """
        Get total room count for a hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID
            is_active: Optional filter by active status

        Returns:
            Total room count
        """
        filters = [Room.hotel_id == hotel_id]
        if is_active is not None:
            filters.append(Room.is_active == is_active)

        query = select(Room).where(and_(*filters))
        result = await db.execute(query)
        return len(list(result.scalars().all()))


# Singleton instance
_room_service: Optional[RoomService] = None


def get_room_service() -> RoomService:
    """Get room service singleton."""
    global _room_service
    if _room_service is None:
        _room_service = RoomService()
    return _room_service
