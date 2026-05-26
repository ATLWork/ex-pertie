"""
Hotel-Room linkage service for Booking data.
"""

from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingHotel, BookingRoom
from app.services.booking_hotel_service import booking_hotel
from app.services.booking_room_service import booking_room


class BookingLinkageService:
    """
    Service for managing hotel-room relationships and linkage operations.
    """

    async def get_hotel_with_rooms(
        self,
        db: AsyncSession,
        hotel_id: str,
    ) -> Tuple[Optional[BookingHotel], List[BookingRoom], Dict]:
        """
        Get a hotel with all its rooms.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Tuple of (hotel, rooms, statistics)
        """
        hotel = await booking_hotel.get(db, id=hotel_id)
        if not hotel:
            return None, [], {}

        rooms = await booking_room.get_by_hotel(db, hotel_id=hotel_id, skip=0, limit=1000)
        total_count = await booking_room.count_by_hotel(db, hotel_id=hotel_id)

        # Calculate statistics
        stats = {
            "total_rooms": total_count,
            "active_rooms": sum(1 for r in rooms if r.is_active),
            "inactive_rooms": sum(1 for r in rooms if not r.is_active),
            "room_types": list(set(r.room_type for r in rooms if r.room_type)),
            "bed_types": list(set(r.bed_type for r in rooms if r.bed_type)),
        }

        return hotel, rooms, stats

    async def get_room_with_hotel(
        self,
        db: AsyncSession,
        room_id: str,
    ) -> Tuple[Optional[BookingRoom], Optional[BookingHotel]]:
        """
        Get a room with its parent hotel.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Tuple of (room, hotel)
        """
        room = await booking_room.get(db, id=room_id)
        if not room:
            return None, None

        hotel = await booking_hotel.get(db, id=room.hotel_id)
        return room, hotel

    async def link_room_to_internal(
        self,
        db: AsyncSession,
        room_id: str,
        internal_room_id: str,
    ) -> Optional[BookingRoom]:
        """
        Link a booking room to an internal room.

        Args:
            db: Database session
            room_id: Booking room ID
            internal_room_id: Internal room ID

        Returns:
            Updated booking room
        """
        room = await booking_room.get(db, id=room_id)
        if not room:
            return None

        room.internal_room_id = internal_room_id
        db.add(room)
        await db.flush()
        await db.refresh(room)
        return room

    async def link_hotel_to_internal(
        self,
        db: AsyncSession,
        hotel_id: str,
        internal_hotel_id: str,
    ) -> Optional[BookingHotel]:
        """
        Link a booking hotel to an internal hotel.

        Args:
            db: Database session
            hotel_id: Booking hotel ID
            internal_hotel_id: Internal hotel ID

        Returns:
            Updated booking hotel
        """
        hotel = await booking_hotel.get(db, id=hotel_id)
        if not hotel:
            return None

        hotel.internal_hotel_id = internal_hotel_id
        db.add(hotel)
        await db.flush()
        await db.refresh(hotel)
        return hotel

    async def bulk_link_rooms_to_internal(
        self,
        db: AsyncSession,
        room_mappings: Dict[str, str],
    ) -> Tuple[int, int]:
        """
        Bulk link booking rooms to internal rooms.

        Args:
            db: Database session
            room_mappings: Dict of {booking_room_id: internal_room_id}

        Returns:
            Tuple of (success_count, fail_count)
        """
        success = 0
        failed = 0

        for booking_room_id, internal_room_id in room_mappings.items():
            result = await self.link_room_to_internal(
                db, booking_room_id, internal_room_id
            )
            if result:
                success += 1
            else:
                failed += 1

        return success, failed

    async def get_unlinked_hotels(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingHotel]:
        """
        Get hotels that are not linked to internal hotels.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of unlinked hotels
        """
        from sqlalchemy import select, is_

        query = select(BookingHotel).where(
            is_(BookingHotel.internal_hotel_id, None)
        ).order_by(BookingHotel.updated_at.desc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_unlinked_rooms(
        self,
        db: AsyncSession,
        hotel_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingRoom]:
        """
        Get rooms that are not linked to internal rooms.

        Args:
            db: Database session
            hotel_id: Optional hotel ID to filter by
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of unlinked rooms
        """
        from sqlalchemy import select, is_

        query = select(BookingRoom).where(
            is_(BookingRoom.internal_room_id, None)
        )

        if hotel_id:
            query = query.where(BookingRoom.hotel_id == hotel_id)

        query = query.order_by(BookingRoom.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_linkage_statistics(
        self,
        db: AsyncSession,
    ) -> Dict:
        """
        Get overall linkage statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import select, func, is_

        # Count total hotels
        hotel_count = await db.execute(
            select(func.count()).select_from(BookingHotel)
        )
        total_hotels = hotel_count.scalar_one()

        # Count linked hotels
        linked_hotels_count = await db.execute(
            select(func.count()).select_from(BookingHotel).where(
                BookingHotel.internal_hotel_id.isnot(None)
            )
        )
        linked_hotels = linked_hotels_count.scalar_one()

        # Count total rooms
        room_count = await db.execute(
            select(func.count()).select_from(BookingRoom)
        )
        total_rooms = room_count.scalar_one()

        # Count linked rooms
        linked_rooms_count = await db.execute(
            select(func.count()).select_from(BookingRoom).where(
                BookingRoom.internal_room_id.isnot(None)
            )
        )
        linked_rooms = linked_rooms_count.scalar_one()

        return {
            "total_hotels": total_hotels,
            "linked_hotels": linked_hotels,
            "unlinked_hotels": total_hotels - linked_hotels,
            "hotel_linkage_rate": round(linked_hotels / total_hotels * 100, 2) if total_hotels > 0 else 0,
            "total_rooms": total_rooms,
            "linked_rooms": linked_rooms,
            "unlinked_rooms": total_rooms - linked_rooms,
            "room_linkage_rate": round(linked_rooms / total_rooms * 100, 2) if total_rooms > 0 else 0,
        }

    async def transfer_rooms_to_hotel(
        self,
        db: AsyncSession,
        source_hotel_id: str,
        target_hotel_id: str,
    ) -> Tuple[int, List[str]]:
        """
        Transfer all rooms from one hotel to another.

        Args:
            db: Database session
            source_hotel_id: Source hotel ID
            target_hotel_id: Target hotel ID

        Returns:
            Tuple of (transferred_count, error_messages)
        """
        # Verify target hotel exists
        target_hotel = await booking_hotel.get(db, id=target_hotel_id)
        if not target_hotel:
            return 0, [f"Target hotel {target_hotel_id} not found"]

        # Get all rooms from source hotel
        rooms = await booking_room.get_by_hotel(
            db, hotel_id=source_hotel_id, skip=0, limit=10000
        )

        transferred = 0
        errors = []

        for room in rooms:
            try:
                room.hotel_id = target_hotel_id
                db.add(room)
                transferred += 1
            except Exception as e:
                errors.append(f"Failed to transfer room {room.id}: {str(e)}")

        await db.flush()
        return transferred, errors

    async def delete_hotel_with_rooms(
        self,
        db: AsyncSession,
        hotel_id: str,
    ) -> Tuple[bool, List[str]]:
        """
        Delete a hotel and all its rooms.

        Args:
            db: Database session
            hotel_id: Hotel ID to delete

        Returns:
            Tuple of (success, error_messages)
        """
        hotel = await booking_hotel.get(db, id=hotel_id)
        if not hotel:
            return False, ["Hotel not found"]

        try:
            # Delete will cascade to rooms due to relationship
            await db.delete(hotel)
            await db.flush()
            return True, []
        except Exception as e:
            return False, [f"Failed to delete hotel: {str(e)}"]


# Singleton instance
_booking_linkage: Optional[BookingLinkageService] = None


def get_booking_linkage_service() -> BookingLinkageService:
    """Get or create booking linkage service instance."""
    global _booking_linkage
    if _booking_linkage is None:
        _booking_linkage = BookingLinkageService()
    return _booking_linkage
