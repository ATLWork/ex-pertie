"""
CRUD service for BookingRoom model.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.booking import BookingRoom, BookingRoomExtension
from app.schemas.booking import (
    BookingRoomCreate,
    BookingRoomUpdate,
    BookingRoomQuery,
)
from app.services.base import CRUDBase


class CRUDBookingRoom(CRUDBase[BookingRoom, BookingRoomCreate, BookingRoomUpdate]):
    """
    CRUD operations for BookingRoom model.
    """

    async def get_by_source_id(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        source: str,
        source_room_id: str,
    ) -> Optional[BookingRoom]:
        """
        Get a booking room by source and source_room_id.

        Args:
            db: Database session
            hotel_id: Parent hotel ID
            source: Data source (e.g., 'booking_com')
            source_room_id: Room ID in source system

        Returns:
            BookingRoom or None
        """
        result = await db.execute(
            select(BookingRoom).where(
                and_(
                    BookingRoom.hotel_id == hotel_id,
                    BookingRoom.source == source,
                    BookingRoom.source_room_id == source_room_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hotel(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingRoom]:
        """
        Get all rooms for a specific hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of BookingRoom instances
        """
        query = select(BookingRoom).where(
            BookingRoom.hotel_id == hotel_id
        ).order_by(BookingRoom.room_name)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_hotel(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
    ) -> int:
        """
        Count rooms for a specific hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Count of rooms
        """
        query = select(func.count()).select_from(BookingRoom).where(
            BookingRoom.hotel_id == hotel_id
        )
        result = await db.execute(query)
        return result.scalar_one()

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: BookingRoomQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingRoom]:
        """
        Search booking rooms with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of BookingRoom instances
        """
        query = select(BookingRoom)

        if query_params.source:
            query = query.where(BookingRoom.source == query_params.source)
        if query_params.source_room_id:
            query = query.where(BookingRoom.source_room_id == query_params.source_room_id)
        if query_params.hotel_id:
            query = query.where(BookingRoom.hotel_id == query_params.hotel_id)
        if query_params.room_name:
            search_term = f"%{query_params.room_name}%"
            query = query.where(
                or_(
                    BookingRoom.room_name.ilike(search_term),
                    BookingRoom.room_name_cn.ilike(search_term),
                )
            )
        if query_params.room_type:
            query = query.where(BookingRoom.room_type == query_params.room_type)
        if query_params.bed_type:
            query = query.where(BookingRoom.bed_type == query_params.bed_type)
        if query_params.is_active is not None:
            query = query.where(BookingRoom.is_active == query_params.is_active)
        if query_params.internal_room_id:
            query = query.where(BookingRoom.internal_room_id == query_params.internal_room_id)

        query = query.order_by(BookingRoom.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: BookingRoomQuery,
    ) -> int:
        """
        Count booking rooms matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(BookingRoom)

        if query_params.source:
            query = query.where(BookingRoom.source == query_params.source)
        if query_params.source_room_id:
            query = query.where(BookingRoom.source_room_id == query_params.source_room_id)
        if query_params.hotel_id:
            query = query.where(BookingRoom.hotel_id == query_params.hotel_id)
        if query_params.room_name:
            search_term = f"%{query_params.room_name}%"
            query = query.where(
                or_(
                    BookingRoom.room_name.ilike(search_term),
                    BookingRoom.room_name_cn.ilike(search_term),
                )
            )
        if query_params.room_type:
            query = query.where(BookingRoom.room_type == query_params.room_type)
        if query_params.bed_type:
            query = query.where(BookingRoom.bed_type == query_params.bed_type)
        if query_params.is_active is not None:
            query = query.where(BookingRoom.is_active == query_params.is_active)
        if query_params.internal_room_id:
            query = query.where(BookingRoom.internal_room_id == query_params.internal_room_id)

        result = await db.execute(query)
        return result.scalar_one()

    async def get_with_extension(
        self,
        db: AsyncSession,
        *,
        id: str,
    ) -> Optional[Tuple[BookingRoom, Optional[BookingRoomExtension]]]:
        """
        Get a booking room with its extension.

        Args:
            db: Database session
            id: Room ID

        Returns:
            Tuple of (BookingRoom, BookingRoomExtension) or None
        """
        result = await db.execute(
            select(BookingRoom).where(BookingRoom.id == id)
        )
        room = result.scalar_one_or_none()
        if not room:
            return None

        ext_result = await db.execute(
            select(BookingRoomExtension).where(BookingRoomExtension.room_id == id)
        )
        extension = ext_result.scalar_one_or_none()

        return room, extension

    async def get_extension(
        self,
        db: AsyncSession,
        *,
        room_id: str,
    ) -> Optional[BookingRoomExtension]:
        """
        Get booking room extension by room_id.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            BookingRoomExtension or None
        """
        result = await db.execute(
            select(BookingRoomExtension).where(BookingRoomExtension.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def create_with_extension(
        self,
        db: AsyncSession,
        *,
        obj_in: BookingRoomCreate,
        extension_data: Optional[Dict[str, Any]] = None,
    ) -> BookingRoom:
        """
        Create a booking room with optional extension.

        Args:
            db: Database session
            obj_in: Room create data
            extension_data: Optional extension data

        Returns:
            Created BookingRoom
        """
        room_data = obj_in.model_dump()
        hotel_id = room_data.pop("hotel_id")
        room = BookingRoom(hotel_id=hotel_id, **room_data)
        db.add(room)
        await db.flush()
        await db.refresh(room)

        if extension_data:
            extension = BookingRoomExtension(room_id=room.id, **extension_data)
            db.add(extension)
            await db.flush()

        return room

    async def update_extension(
        self,
        db: AsyncSession,
        *,
        room_id: str,
        obj_in: Dict[str, Any],
    ) -> Optional[BookingRoomExtension]:
        """
        Update or create booking room extension.

        Args:
            db: Database session
            room_id: Room ID
            obj_in: Extension update data

        Returns:
            Updated or created BookingRoomExtension
        """
        ext = await self.get_extension(db, room_id=room_id)
        if ext:
            for field, value in obj_in.items():
                if hasattr(ext, field) and value is not None:
                    setattr(ext, field, value)
            db.add(ext)
            await db.flush()
            await db.refresh(ext)
            return ext
        else:
            ext = BookingRoomExtension(room_id=room_id, **obj_in)
            db.add(ext)
            await db.flush()
            await db.refresh(ext)
            return ext

    async def bulk_upsert(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        items: List[Dict[str, Any]],
        source: str,
    ) -> Tuple[int, int]:
        """
        Bulk upsert booking rooms for a hotel.

        Args:
            db: Database session
            hotel_id: Parent hotel ID
            items: List of room data to upsert
            source: Data source

        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0

        for item in items:
            source_room_id = item.get("source_room_id")
            if not source_room_id:
                continue

            existing = await self.get_by_source_id(
                db, hotel_id=hotel_id, source=source, source_room_id=source_room_id
            )

            if existing:
                # Update existing
                for field, value in item.items():
                    if hasattr(existing, field) and value is not None:
                        setattr(existing, field, value)
                db.add(existing)
                updated_count += 1
            else:
                # Create new
                room = BookingRoom(hotel_id=hotel_id, source=source, **item)
                db.add(room)
                created_count += 1

        await db.flush()
        return created_count, updated_count


# Global instance
booking_room = CRUDBookingRoom(BookingRoom)
