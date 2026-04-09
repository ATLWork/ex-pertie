"""
Room batch operation service.

Provides bulk operations for rooms including batch create, update, delete, and linking.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Room
from app.models.room import RoomExtension
from app.schemas.room import RoomCreate, RoomUpdate, RoomExtensionCreate
from app.services.room_service import RoomService, get_room_service
from app.services.hotel_service import HotelService, hotel_service


class RoomBatchService:
    """
    Service for room batch operations.

    Provides functionality to:
    - Batch create rooms
    - Batch update rooms
    - Batch delete rooms
    - Batch link rooms to hotels
    """

    def __init__(
        self,
        room_service: Optional[RoomService] = None,
        hotel_service: Optional[HotelService] = None,
    ):
        self.room_service = room_service or get_room_service()
        self.hotel_service = hotel_service or hotel_service

    async def batch_create_rooms(
        self,
        db: AsyncSession,
        rooms_data: List[Dict[str, Any]],
    ) -> Tuple[List[Room], List[Dict[str, Any]]]:
        """Create multiple rooms in batch."""
        created_rooms: List[Room] = []
        errors: List[Dict[str, Any]] = []

        for idx, room_data in enumerate(rooms_data):
            try:
                if not room_data.get("hotel_id"):
                    errors.append({"index": idx, "data": room_data, "error": "hotel_id is required"})
                    continue
                if not room_data.get("room_type_code"):
                    errors.append({"index": idx, "data": room_data, "error": "room_type_code is required"})
                    continue
                if not room_data.get("name_cn"):
                    errors.append({"index": idx, "data": room_data, "error": "name_cn is required"})
                    continue

                # Verify hotel exists
                hotel = await self.hotel_service.get_hotel(db, hotel_id=room_data["hotel_id"])
                if not hotel:
                    errors.append({"index": idx, "data": room_data, "error": f"Hotel {room_data['hotel_id']} not found"})
                    continue

                room_create = RoomCreate(**room_data)
                room = await self.room_service.create_room(db, room_in=room_create)
                created_rooms.append(room)

            except Exception as e:
                errors.append({"index": idx, "data": room_data, "error": str(e)})

        return created_rooms, errors

    async def batch_update_rooms(
        self,
        db: AsyncSession,
        updates: List[Dict[str, Any]],
    ) -> Tuple[List[Room], List[Dict[str, Any]]]:
        """Update multiple rooms in batch."""
        updated_rooms: List[Room] = []
        errors: List[Dict[str, Any]] = []

        for idx, update_item in enumerate(updates):
            try:
                room_id = update_item.get("room_id")
                update_data = update_item.get("data", {})

                if not room_id:
                    errors.append({"index": idx, "data": update_item, "error": "room_id is required"})
                    continue
                if not update_data:
                    errors.append({"index": idx, "data": update_item, "error": "update data is required"})
                    continue

                room = await self.room_service.get_room(db, room_id=room_id)
                if not room:
                    errors.append({"index": idx, "data": update_item, "error": f"Room {room_id} not found"})
                    continue

                room_update = RoomUpdate(**update_data)
                updated = await self.room_service.update_room(db, room_id=room_id, room_in=room_update)
                if updated:
                    updated_rooms.append(updated)
                else:
                    errors.append({"index": idx, "data": update_item, "error": "Failed to update room"})

            except Exception as e:
                errors.append({"index": idx, "data": update_item, "error": str(e)})

        return updated_rooms, errors

    async def batch_delete_rooms(
        self,
        db: AsyncSession,
        room_ids: List[str],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Delete multiple rooms in batch."""
        deleted_ids: List[str] = []
        errors: List[Dict[str, Any]] = []

        for idx, room_id in enumerate(room_ids):
            try:
                room = await self.room_service.get_room(db, room_id=room_id)
                if not room:
                    errors.append({"index": idx, "room_id": room_id, "error": f"Room {room_id} not found"})
                    continue

                deleted = await self.room_service.delete_room(db, room_id=room_id)
                if deleted:
                    deleted_ids.append(room_id)
                else:
                    errors.append({"index": idx, "room_id": room_id, "error": "Failed to delete room"})

            except Exception as e:
                errors.append({"index": idx, "room_id": room_id, "error": str(e)})

        return deleted_ids, errors

    async def batch_link_to_hotel(
        self,
        db: AsyncSession,
        room_ids: List[str],
        target_hotel_id: str,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Link multiple rooms to a different hotel."""
        linked_ids: List[str] = []
        errors: List[Dict[str, Any]] = []

        # Verify target hotel exists
        hotel = await self.hotel_service.get_hotel(db, hotel_id=target_hotel_id)
        if not hotel:
            return [], [{"error": f"Target hotel {target_hotel_id} not found"}]

        for idx, room_id in enumerate(room_ids):
            try:
                room = await self.room_service.get_room(db, room_id=room_id)
                if not room:
                    errors.append({"index": idx, "room_id": room_id, "error": f"Room {room_id} not found"})
                    continue

                room_update = RoomUpdate(hotel_id=target_hotel_id)
                updated = await self.room_service.update_room(db, room_id=room_id, room_in=room_update)
                if updated:
                    linked_ids.append(room_id)
                else:
                    errors.append({"index": idx, "room_id": room_id, "error": "Failed to link room to hotel"})

            except Exception as e:
                errors.append({"index": idx, "room_id": room_id, "error": str(e)})

        return linked_ids, errors


_room_batch_service: Optional[RoomBatchService] = None


def get_room_batch_service() -> RoomBatchService:
    """Get room batch service singleton."""
    global _room_batch_service
    if _room_batch_service is None:
        _room_batch_service = RoomBatchService()
    return _room_batch_service
