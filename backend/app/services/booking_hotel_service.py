"""
CRUD service for BookingHotel model.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.booking import BookingHotel, BookingHotelExtension
from app.schemas.booking import (
    BookingHotelCreate,
    BookingHotelUpdate,
    BookingHotelQuery,
)
from app.services.base import CRUDBase


class CRUDBookingHotel(CRUDBase[BookingHotel, BookingHotelCreate, BookingHotelUpdate]):
    """
    CRUD operations for BookingHotel model.
    """

    async def get_by_source_id(
        self,
        db: AsyncSession,
        *,
        source: str,
        source_hotel_id: str,
    ) -> Optional[BookingHotel]:
        """
        Get a booking hotel by source and source_hotel_id.

        Args:
            db: Database session
            source: Data source (e.g., 'booking_com')
            source_hotel_id: Hotel ID in source system

        Returns:
            BookingHotel or None
        """
        result = await db.execute(
            select(BookingHotel).where(
                and_(
                    BookingHotel.source == source,
                    BookingHotel.source_hotel_id == source_hotel_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: BookingHotelQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingHotel]:
        """
        Search booking hotels with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of BookingHotel instances
        """
        query = select(BookingHotel)

        if query_params.source:
            query = query.where(BookingHotel.source == query_params.source)
        if query_params.source_hotel_id:
            query = query.where(BookingHotel.source_hotel_id == query_params.source_hotel_id)
        if query_params.name:
            search_term = f"%{query_params.name}%"
            query = query.where(
                or_(
                    BookingHotel.name_en.ilike(search_term),
                    BookingHotel.name_cn.ilike(search_term),
                    BookingHotel.display_name.ilike(search_term),
                )
            )
        if query_params.city:
            query = query.where(BookingHotel.city == query_params.city)
        if query_params.province:
            query = query.where(BookingHotel.province == query_params.province)
        if query_params.country_code:
            query = query.where(BookingHotel.country_code == query_params.country_code)
        if query_params.brand:
            query = query.where(BookingHotel.brand == query_params.brand)
        if query_params.is_active is not None:
            query = query.where(BookingHotel.is_active == query_params.is_active)
        if query_params.internal_hotel_id:
            query = query.where(BookingHotel.internal_hotel_id == query_params.internal_hotel_id)

        query = query.order_by(BookingHotel.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: BookingHotelQuery,
    ) -> int:
        """
        Count booking hotels matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(BookingHotel)

        if query_params.source:
            query = query.where(BookingHotel.source == query_params.source)
        if query_params.source_hotel_id:
            query = query.where(BookingHotel.source_hotel_id == query_params.source_hotel_id)
        if query_params.name:
            search_term = f"%{query_params.name}%"
            query = query.where(
                or_(
                    BookingHotel.name_en.ilike(search_term),
                    BookingHotel.name_cn.ilike(search_term),
                    BookingHotel.display_name.ilike(search_term),
                )
            )
        if query_params.city:
            query = query.where(BookingHotel.city == query_params.city)
        if query_params.province:
            query = query.where(BookingHotel.province == query_params.province)
        if query_params.country_code:
            query = query.where(BookingHotel.country_code == query_params.country_code)
        if query_params.brand:
            query = query.where(BookingHotel.brand == query_params.brand)
        if query_params.is_active is not None:
            query = query.where(BookingHotel.is_active == query_params.is_active)
        if query_params.internal_hotel_id:
            query = query.where(BookingHotel.internal_hotel_id == query_params.internal_hotel_id)

        result = await db.execute(query)
        return result.scalar_one()

    async def get_with_extension(
        self,
        db: AsyncSession,
        *,
        id: str,
    ) -> Optional[Tuple[BookingHotel, Optional[BookingHotelExtension]]]:
        """
        Get a booking hotel with its extension.

        Args:
            db: Database session
            id: Hotel ID

        Returns:
            Tuple of (BookingHotel, BookingHotelExtension) or None
        """
        result = await db.execute(
            select(BookingHotel).where(BookingHotel.id == id)
        )
        hotel = result.scalar_one_or_none()
        if not hotel:
            return None

        ext_result = await db.execute(
            select(BookingHotelExtension).where(BookingHotelExtension.hotel_id == id)
        )
        extension = ext_result.scalar_one_or_none()

        return hotel, extension

    async def get_extension(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
    ) -> Optional[BookingHotelExtension]:
        """
        Get booking hotel extension by hotel_id.

        Args:
            db: Database session
            hotel_id: Hotel ID

        Returns:
            BookingHotelExtension or None
        """
        result = await db.execute(
            select(BookingHotelExtension).where(BookingHotelExtension.hotel_id == hotel_id)
        )
        return result.scalar_one_or_none()

    async def create_with_extension(
        self,
        db: AsyncSession,
        *,
        obj_in: BookingHotelCreate,
        extension_data: Optional[Dict[str, Any]] = None,
    ) -> BookingHotel:
        """
        Create a booking hotel with optional extension.

        Args:
            db: Database session
            obj_in: Hotel create data
            extension_data: Optional extension data

        Returns:
            Created BookingHotel
        """
        hotel = BookingHotel(**obj_in.model_dump())
        db.add(hotel)
        await db.flush()
        await db.refresh(hotel)

        if extension_data:
            extension = BookingHotelExtension(hotel_id=hotel.id, **extension_data)
            db.add(extension)
            await db.flush()

        return hotel

    async def update_extension(
        self,
        db: AsyncSession,
        *,
        hotel_id: str,
        obj_in: Dict[str, Any],
    ) -> Optional[BookingHotelExtension]:
        """
        Update or create booking hotel extension.

        Args:
            db: Database session
            hotel_id: Hotel ID
            obj_in: Extension update data

        Returns:
            Updated or created BookingHotelExtension
        """
        ext = await self.get_extension(db, hotel_id=hotel_id)
        if ext:
            for field, value in obj_in.items():
                if hasattr(ext, field) and value is not None:
                    setattr(ext, field, value)
            db.add(ext)
            await db.flush()
            await db.refresh(ext)
            return ext
        else:
            ext = BookingHotelExtension(hotel_id=hotel_id, **obj_in)
            db.add(ext)
            await db.flush()
            await db.refresh(ext)
            return ext

    async def bulk_upsert(
        self,
        db: AsyncSession,
        *,
        items: List[Dict[str, Any]],
        source: str,
    ) -> Tuple[int, int]:
        """
        Bulk upsert booking hotels.

        Args:
            db: Database session
            items: List of hotel data to upsert
            source: Data source

        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0

        for item in items:
            source_hotel_id = item.get("source_hotel_id")
            if not source_hotel_id:
                continue

            existing = await self.get_by_source_id(
                db, source=source, source_hotel_id=source_hotel_id
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
                hotel = BookingHotel(source=source, **item)
                db.add(hotel)
                created_count += 1

        await db.flush()
        return created_count, updated_count


# Global instance
booking_hotel = CRUDBookingHotel(BookingHotel)
