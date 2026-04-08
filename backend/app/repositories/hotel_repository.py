"""
Repository for Hotel database operations.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.models.hotel import Hotel
from app.services.base import CRUDBase

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class for database operations.
    Provides common CRUD operations and query methods.
    """

    async def get_by_field(
        self,
        db: AsyncSession,
        *,
        field_name: str,
        field_value: Any,
    ) -> Optional[ModelType]:
        """
        Get a single record by a specific field.

        Args:
            db: Database session
            field_name: Name of the field to filter by
            field_value: Value to match

        Returns:
            Model instance or None
        """
        if not hasattr(self.model, field_name):
            return None
        result = await db.execute(
            select(self.model).where(getattr(self.model, field_name) == field_value)
        )
        return result.scalar_one_or_none()


class HotelRepository(BaseRepository[Hotel, Any, Any]):
    """
    Repository for Hotel model operations.
    """

    def __init__(self):
        super().__init__(Hotel)

    async def get_by_expedia_id(
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
        return await self.get_by_field(
            db, field_name="expedia_hotel_id", field_value=expedia_hotel_id
        )

    async def get_by_expedia_property_code(
        self, db: AsyncSession, *, expedia_property_code: str
    ) -> Optional[Hotel]:
        """
        Get a hotel by Expedia Property Code.

        Args:
            db: Database session
            expedia_property_code: Expedia Property Code

        Returns:
            Hotel instance or None
        """
        return await self.get_by_field(
            db, field_name="expedia_property_code", field_value=expedia_property_code
        )

    async def search(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        expedia_hotel_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Hotel]:
        """
        Search hotels with various filters.

        Args:
            db: Database session
            name: Search by hotel name (partial match)
            brand: Filter by brand
            status: Filter by status
            city: Filter by city
            province: Filter by province
            expedia_hotel_id: Filter by Expedia Hotel ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Hotel instances
        """
        query = select(Hotel)

        if name:
            query = query.where(Hotel.name_cn.ilike(f"%{name}%"))
        if brand:
            query = query.where(Hotel.brand == brand)
        if status:
            query = query.where(Hotel.status == status)
        if city:
            query = query.where(Hotel.city == city)
        if province:
            query = query.where(Hotel.province == province)
        if expedia_hotel_id:
            query = query.where(Hotel.expedia_hotel_id == expedia_hotel_id)

        query = query.order_by(Hotel.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        expedia_hotel_id: Optional[str] = None,
    ) -> int:
        """
        Count hotels with various filters.

        Args:
            db: Database session
            name: Search by hotel name (partial match)
            brand: Filter by brand
            status: Filter by status
            city: Filter by city
            province: Filter by province
            expedia_hotel_id: Filter by Expedia Hotel ID

        Returns:
            Count of matching hotels
        """
        query = select(func.count()).select_from(Hotel)

        if name:
            query = query.where(Hotel.name_cn.ilike(f"%{name}%"))
        if brand:
            query = query.where(Hotel.brand == brand)
        if status:
            query = query.where(Hotel.status == status)
        if city:
            query = query.where(Hotel.city == city)
        if province:
            query = query.where(Hotel.province == province)
        if expedia_hotel_id:
            query = query.where(Hotel.expedia_hotel_id == expedia_hotel_id)

        result = await db.execute(query)
        return result.scalar_one()

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
        result = await db.execute(
            select(func.count())
            .select_from(Hotel)
            .where(Hotel.expedia_hotel_id == expedia_hotel_id)
        )
        return result.scalar_one() > 0

    async def get_by_city(
        self, db: AsyncSession, *, city: str, skip: int = 0, limit: int = 100
    ) -> List[Hotel]:
        """
        Get hotels by city.

        Args:
            db: Database session
            city: City name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Hotel instances
        """
        return await self.get_multi(
            db, skip=skip, limit=limit, filters={"city": city}
        )

    async def get_by_province(
        self, db: AsyncSession, *, province: str, skip: int = 0, limit: int = 100
    ) -> List[Hotel]:
        """
        Get hotels by province.

        Args:
            db: Database session
            province: Province name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Hotel instances
        """
        return await self.get_multi(
            db, skip=skip, limit=limit, filters={"province": province}
        )


# Global instance
hotel_repository = HotelRepository()
