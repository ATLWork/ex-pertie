"""
Hotel batch operation service.

Provides bulk operations for hotels including batch create, update, delete, and status changes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Hotel, HotelStatus
from app.schemas.hotel import HotelCreate, HotelUpdate
from app.services.hotel_service import HotelService, hotel_service as default_hotel_service


class HotelBatchService:
    """
    Service for hotel batch operations.

    Provides functionality to:
    - Batch create hotels
    - Batch update hotels
    - Batch delete hotels
    - Batch update hotel status
    """

    def __init__(self, hotel_service: Optional[HotelService] = None):
        self.hotel_service = hotel_service or default_hotel_service

    async def batch_create_hotels(
        self,
        db: AsyncSession,
        hotels_data: List[Dict[str, Any]],
    ) -> Tuple[List[Hotel], List[Dict[str, Any]]]:
        """Create multiple hotels in batch."""
        created_hotels: List[Hotel] = []
        errors: List[Dict[str, Any]] = []

        for idx, hotel_data in enumerate(hotels_data):
            try:
                if not hotel_data.get("name_cn"):
                    errors.append({"index": idx, "data": hotel_data, "error": "name_cn is required"})
                    continue
                if not hotel_data.get("province"):
                    errors.append({"index": idx, "data": hotel_data, "error": "province is required"})
                    continue
                if not hotel_data.get("city"):
                    errors.append({"index": idx, "data": hotel_data, "error": "city is required"})
                    continue
                if not hotel_data.get("address_cn"):
                    errors.append({"index": idx, "data": hotel_data, "error": "address_cn is required"})
                    continue

                expedia_hotel_id = hotel_data.get("expedia_hotel_id")
                if expedia_hotel_id:
                    exists = await self.hotel_service.exists_by_expedia_id(db, expedia_hotel_id=expedia_hotel_id)
                    if exists:
                        errors.append({"index": idx, "data": hotel_data, "error": f"Hotel with Expedia ID {expedia_hotel_id} already exists"})
                        continue

                hotel_create = HotelCreate(**hotel_data)
                hotel = await self.hotel_service.create_hotel(db, hotel_in=hotel_create)
                created_hotels.append(hotel)

            except Exception as e:
                errors.append({"index": idx, "data": hotel_data, "error": str(e)})

        return created_hotels, errors

    async def batch_update_hotels(
        self,
        db: AsyncSession,
        updates: List[Dict[str, Any]],
    ) -> Tuple[List[Hotel], List[Dict[str, Any]]]:
        """Update multiple hotels in batch."""
        updated_hotels: List[Hotel] = []
        errors: List[Dict[str, Any]] = []

        for idx, update_item in enumerate(updates):
            try:
                hotel_id = update_item.get("hotel_id")
                update_data = update_item.get("data", {})

                if not hotel_id:
                    errors.append({"index": idx, "data": update_item, "error": "hotel_id is required"})
                    continue
                if not update_data:
                    errors.append({"index": idx, "data": update_item, "error": "update data is required"})
                    continue

                hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
                if not hotel:
                    errors.append({"index": idx, "data": update_item, "error": f"Hotel {hotel_id} not found"})
                    continue

                new_expedia_id = update_data.get("expedia_hotel_id")
                if new_expedia_id and new_expedia_id != hotel.expedia_hotel_id:
                    exists = await self.hotel_service.exists_by_expedia_id(db, expedia_hotel_id=new_expedia_id)
                    if exists:
                        errors.append({"index": idx, "data": update_item, "error": f"Hotel with Expedia ID {new_expedia_id} already exists"})
                        continue

                hotel_update = HotelUpdate(**update_data)
                updated = await self.hotel_service.update_hotel(db, hotel_id=hotel_id, hotel_in=hotel_update)
                if updated:
                    updated_hotels.append(updated)
                else:
                    errors.append({"index": idx, "data": update_item, "error": "Failed to update hotel"})

            except Exception as e:
                errors.append({"index": idx, "data": update_item, "error": str(e)})

        return updated_hotels, errors

    async def batch_delete_hotels(
        self,
        db: AsyncSession,
        hotel_ids: List[str],
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Delete multiple hotels in batch. Note: rooms will be cascade deleted."""
        deleted_ids: List[str] = []
        errors: List[Dict[str, Any]] = []

        for idx, hotel_id in enumerate(hotel_ids):
            try:
                hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
                if not hotel:
                    errors.append({"index": idx, "hotel_id": hotel_id, "error": f"Hotel {hotel_id} not found"})
                    continue

                deleted = await self.hotel_service.delete_hotel(db, hotel_id=hotel_id)
                if deleted:
                    deleted_ids.append(hotel_id)
                else:
                    errors.append({"index": idx, "hotel_id": hotel_id, "error": "Failed to delete hotel"})

            except Exception as e:
                errors.append({"index": idx, "hotel_id": hotel_id, "error": str(e)})

        return deleted_ids, errors

    async def batch_update_status(
        self,
        db: AsyncSession,
        hotel_ids: List[str],
        new_status: HotelStatus,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Update status for multiple hotels in batch."""
        updated_ids: List[str] = []
        errors: List[Dict[str, Any]] = []

        for idx, hotel_id in enumerate(hotel_ids):
            try:
                hotel = await self.hotel_service.get_hotel(db, hotel_id=hotel_id)
                if not hotel:
                    errors.append({"index": idx, "hotel_id": hotel_id, "error": f"Hotel {hotel_id} not found"})
                    continue

                hotel_update = HotelUpdate(status=new_status)
                updated = await self.hotel_service.update_hotel(db, hotel_id=hotel_id, hotel_in=hotel_update)
                if updated:
                    updated_ids.append(hotel_id)
                else:
                    errors.append({"index": idx, "hotel_id": hotel_id, "error": "Failed to update hotel status"})

            except Exception as e:
                errors.append({"index": idx, "hotel_id": hotel_id, "error": str(e)})

        return updated_ids, errors

    async def batch_publish_hotels(self, db: AsyncSession, hotel_ids: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Publish multiple hotels (set status to PUBLISHED)."""
        return await self.batch_update_status(db, hotel_ids, HotelStatus.PUBLISHED)

    async def batch_suspend_hotels(self, db: AsyncSession, hotel_ids: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Suspend multiple hotels (set status to SUSPENDED)."""
        return await self.batch_update_status(db, hotel_ids, HotelStatus.SUSPENDED)


_hotel_batch_service: Optional[HotelBatchService] = None


def get_hotel_batch_service() -> HotelBatchService:
    """Get hotel batch service singleton."""
    global _hotel_batch_service
    if _hotel_batch_service is None:
        _hotel_batch_service = HotelBatchService()
    return _hotel_batch_service
