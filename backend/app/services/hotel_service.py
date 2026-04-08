"""
Service for Hotel business logic.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Hotel
from app.repositories.hotel_repository import HotelRepository, hotel_repository
from app.schemas.hotel import HotelCreate, HotelQuery, HotelResponse, HotelUpdate


class HotelService:
    """
    Service for Hotel operations.
    Provides business logic and orchestration for hotel-related operations.
    """

    def __init__(self, repository: Optional[HotelRepository] = None):
        """
        Initialize HotelService.

        Args:
            repository: Optional HotelRepository instance. Defaults to global instance.
        """
        self.repository = repository or hotel_repository

    async def create_hotel(
        self, db: AsyncSession, *, hotel_in: HotelCreate
    ) -> Hotel:
        """
        Create a new hotel.

        Args:
            db: Database session
            hotel_in: Hotel creation data

        Returns:
            Created Hotel instance
        """
        hotel_data = hotel_in.model_dump()
        return await self.repository.create(db, obj_in=hotel_data)

    async def get_hotel(self, db: AsyncSession, *, hotel_id: str) -> Optional[Hotel]:
        """
        Get a hotel by ID.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            Hotel instance or None
        """
        return await self.repository.get(db, id=hotel_id)

    async def get_hotel_by_expedia_id(
        self, db: AsyncSession, *, expedia_hotel_id: str
    ) -> Optional[Hotel]:
        """
        Get a hotel by Expedia Hotel ID.

        Args:
            db: Database session
            expedia_hotel_id: Expedia Hotel ID

        Returns:
            Hotel instance or None
        """
        return await self.repository.get_by_expedia_id(
            db, expedia_hotel_id=expedia_hotel_id
        )

    async def update_hotel(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        hotel_in: HotelUpdate,
    ) -> Optional[Hotel]:
        """
        Update an existing hotel.

        Args:
            db: Database session
            hotel_id: Hotel ID
            hotel_in: Hotel update data

        Returns:
            Updated Hotel instance or None
        """
        hotel = await self.repository.get(db, id=hotel_id)
        if not hotel:
            return None

        update_data = hotel_in.model_dump(exclude_unset=True)
        return await self.repository.update(db, db_obj=hotel, obj_in=update_data)

    async def delete_hotel(self, db: AsyncSession, *, hotel_id: str) -> bool:
        """
        Delete a hotel by ID.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(db, id=hotel_id)

    async def list_hotels(
        self,
        db: AsyncSession,
        *,
        query: Optional[HotelQuery] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Hotel], int]:
        """
        List hotels with pagination and filtering.

        Args:
            db: Database session
            query: Query parameters for filtering
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of Hotel instances, total count)
        """
        if query is None:
            query = HotelQuery()

        skip = (page - 1) * page_size

        # Search with filters
        hotels = await self.repository.search(
            db,
            name=query.name,
            brand=query.brand,
            status=query.status,
            city=query.city,
            province=query.province,
            expedia_hotel_id=query.expedia_hotel_id,
            skip=skip,
            limit=page_size,
        )

        # Get total count
        total = await self.repository.count_with_filters(
            db,
            name=query.name,
            brand=query.brand,
            status=query.status,
            city=query.city,
            province=query.province,
            expedia_hotel_id=query.expedia_hotel_id,
        )

        return hotels, total

    async def exists_hotel(self, db: AsyncSession, *, hotel_id: str) -> bool:
        """
        Check if a hotel exists by ID.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            True if exists, False otherwise
        """
        return await self.repository.exists(db, id=hotel_id)

    async def exists_by_expedia_id(
        self, db: AsyncSession, *, expedia_hotel_id: str
    ) -> bool:
        """
        Check if a hotel exists by Expedia Hotel ID.

        Args:
            db: Database session
            expedia_hotel_id: Expedia Hotel ID

        Returns:
            True if exists, False otherwise
        """
        return await self.repository.exists_by_expedia_id(
            db, expedia_hotel_id=expedia_hotel_id
        )

    async def count_hotels(
        self,
        db: AsyncSession,
        *,
        query: Optional[HotelQuery] = None,
    ) -> int:
        """
        Count hotels with optional filtering.

        Args:
            db: Database session
            query: Query parameters for filtering

        Returns:
            Total count of matching hotels
        """
        if query is None:
            query = HotelQuery()

        return await self.repository.count_with_filters(
            db,
            name=query.name,
            brand=query.brand,
            status=query.status,
            city=query.city,
            province=query.province,
            expedia_hotel_id=query.expedia_hotel_id,
        )


# Global instance
hotel_service = HotelService()
