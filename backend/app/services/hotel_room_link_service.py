"""
Hotel-Room link service.

Provides linkage operations between hotels and rooms including:
- Getting hotel with all its rooms
- Room migration between hotels
- Cascading operations when hotel is deleted
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Hotel, Room
from app.models.room import RoomExtension
from app.services.hotel_service import HotelService, hotel_service
from app.services.room_service import RoomService, get_room_service


class HotelRoomLinkService:
    """
    Service for hotel-room linkage operations.

    Provides functionality to:
    - Get hotel with all its rooms
    - Migrate rooms between hotels
    - Handle cascading operations
    """

    def __init__(
        self,
        hotel_service: Optional[HotelService] = None,
        room_service: Optional[RoomService] = None,
    ):
        self.hotel_service = hotel_service or hotel_service
        self.room_service = room_service or get_room_service()

    async def get_hotel_with_rooms(
        self,
        db: AsyncSession,
        hotel_id: str,
        include_inactive: bool = False,
    ) -> Tuple[Optional[Hotel], List[Room], int]:
        """
        Get a hotel with all its rooms.

        Args:
            db: Database session
            hotel_id: Hotel ID
            include_inactive: Whether to include inactive rooms

        Returns:
            Tuple of (Hotel, list of Rooms, total room count)
        """
        hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
        if not hotel:
            return None, [], 0

        rooms, total = await self.room_service.get_rooms_by_hotel(
            db,
            hotel_id=hotel_id,
            is_active=None if include_inactive else True,
        )

        return hotel, rooms, total

    async def get_room_count_by_hotel(
        self,
        db: AsyncSession,
        hotel_id: str,
        is_active: Optional[bool] = None,
    ) -> int:
        """Get room count for a hotel."""
        return await self.room_service.get_room_count_by_hotel(
            db, hotel_id=hotel_id, is_active=is_active
        )

    async def migrate_rooms(
        self,
        db: AsyncSession,
        room_ids: List[str],
        source_hotel_id: str,
        target_hotel_id: str,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Migrate rooms from one hotel to another.

        Args:
            db: Database session
            room_ids: List of room IDs to migrate
            source_hotel_id: Current hotel ID
            target_hotel_id: Target hotel ID

        Returns:
            Tuple of (migrated room IDs, errors)
        """
        migrated_ids: List[str] = []
        errors: List[Dict[str, Any]] = []

        # Verify target hotel exists
        target_hotel = await self.hotel_service.get_hotel(db, hotel_id=target_hotel_id)
        if not target_hotel:
            return [], [{"error": f"Target hotel {target_hotel_id} not found"}]

        for idx, room_id in enumerate(room_ids):
            try:
                room = await self.room_service.get_room(db, room_id=room_id)
                if not room:
                    errors.append({"index": idx, "room_id": room_id, "error": f"Room {room_id} not found"})
                    continue

                if room.hotel_id != source_hotel_id:
                    errors.append({"index": idx, "room_id": room_id, "error": f"Room {room_id} does not belong to source hotel"})
                    continue

                from app.schemas.room import RoomUpdate
                room_update = RoomUpdate(hotel_id=target_hotel_id)
                updated = await self.room_service.update_room(db, room_id=room_id, room_in=room_update)
                if updated:
                    migrated_ids.append(room_id)
                else:
                    errors.append({"index": idx, "room_id": room_id, "error": "Failed to migrate room"})

            except Exception as e:
                errors.append({"index": idx, "room_id": room_id, "error": str(e)})

        return migrated_ids, errors

    async def deactivate_hotel_rooms(
        self,
        db: AsyncSession,
        hotel_id: str,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Deactivate all rooms for a hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Tuple of (count of deactivated rooms, errors)
        """
        from app.schemas.room import RoomUpdate

        errors: List[Dict[str, Any]] = []

        hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
        if not hotel:
            return 0, [{"error": f"Hotel {hotel_id} not found"}]

        rooms, total = await self.room_service.get_rooms_by_hotel(
            db, hotel_id=hotel_id, is_active=None
        )

        deactivated_count = 0
        for room in rooms:
            if room.is_active:
                try:
                    room_update = RoomUpdate(is_active=False)
                    updated = await self.room_service.update_room(db, room_id=room.id, room_in=room_update)
                    if updated:
                        deactivated_count += 1
                except Exception as e:
                    errors.append({"room_id": room.id, "error": str(e)})

        return deactivated_count, errors

    async def check_room_assignment(
        self,
        db: AsyncSession,
        hotel_id: str,
    ) -> Dict[str, Any]:
        """
        Check room assignment status for a hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Dictionary with assignment statistics
        """
        hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
        if not hotel:
            return {"error": f"Hotel {hotel_id} not found"}

        rooms, total = await self.room_service.get_rooms_by_hotel(
            db, hotel_id=hotel_id, is_active=None
        )

        active_rooms = [r for r in rooms if r.is_active]
        inactive_rooms = [r for r in rooms if not r.is_active]

        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel.name_cn,
            "total_rooms": total,
            "active_rooms": len(active_rooms),
            "inactive_rooms": len(inactive_rooms),
            "room_details": [
                {
                    "room_id": r.id,
                    "name_cn": r.name_cn,
                    "is_active": r.is_active,
                    "room_type_code": r.room_type_code,
                }
                for r in rooms
            ],
        }


_hotel_room_link_service: Optional[HotelRoomLinkService] = None


def get_hotel_room_link_service() -> HotelRoomLinkService:
    """Get hotel-room link service singleton."""
    global _hotel_room_link_service
    if _hotel_room_link_service is None:
        _hotel_room_link_service = HotelRoomLinkService()
    return _hotel_room_link_service
