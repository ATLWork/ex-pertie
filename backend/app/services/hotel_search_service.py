"""
Hotel search and filter service.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Hotel, HotelBrand, HotelStatus
from app.services.base import CRUDBase


class HotelSearchService:
    """
    Service for hotel search and filtering operations.
    """

    async def search_hotels(
        self,
        db: AsyncSession,
        *,
        keyword: Optional[str] = None,
        brand: Optional[HotelBrand] = None,
        status: Optional[HotelStatus] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "updated_at",
        order_desc: bool = True,
    ) -> Tuple[List[Hotel], int]:
        """
        Comprehensive hotel search with multiple conditions.

        Args:
            db: Database session
            keyword: Keyword to search in hotel names (fuzzy match)
            brand: Filter by hotel brand
            status: Filter by hotel status
            city: Filter by city
            province: Filter by province
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by (default: updated_at)
            order_desc: Whether to order in descending order (default: True)

        Returns:
            Tuple of (list of Hotel instances, total count)
        """
        query = select(Hotel)
        count_query = select(func.count()).select_from(Hotel)

        # Build filter conditions
        filters = []
        if keyword:
            keyword_filter = or_(
                Hotel.name_cn.ilike(f"%{keyword}%"),
                Hotel.name_en.ilike(f"%{keyword}%") if Hotel.name_en is not None else False,
                Hotel.address_cn.ilike(f"%{keyword}%") if Hotel.address_cn is not None else False,
            )
            filters.append(keyword_filter)
        if brand:
            filters.append(Hotel.brand == brand)
        if status:
            filters.append(Hotel.status == status)
        if city:
            filters.append(Hotel.city == city)
        if province:
            filters.append(Hotel.province == province)
        if is_active is not None:
            filters.append(Hotel.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply ordering
        if hasattr(Hotel, order_by):
            order_column = getattr(Hotel, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        hotels = list(result.scalars().all())

        return hotels, total

    async def filter_hotels_by_brand(
        self,
        db: AsyncSession,
        *,
        brand: HotelBrand,
        status: Optional[HotelStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Hotel], int]:
        """
        Filter hotels by brand.

        Args:
            db: Database session
            brand: Hotel brand to filter by
            status: Optional status filter
            is_active: Optional active status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Hotel instances, total count)
        """
        return await self.search_hotels(
            db,
            brand=brand,
            status=status,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    async def filter_hotels_by_status(
        self,
        db: AsyncSession,
        *,
        status: HotelStatus,
        brand: Optional[HotelBrand] = None,
        city: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Hotel], int]:
        """
        Filter hotels by status.

        Args:
            db: Database session
            status: Hotel status to filter by
            brand: Optional brand filter
            city: Optional city filter
            is_active: Optional active status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Hotel instances, total count)
        """
        return await self.search_hotels(
            db,
            status=status,
            brand=brand,
            city=city,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    async def filter_hotels_by_city(
        self,
        db: AsyncSession,
        *,
        city: str,
        brand: Optional[HotelBrand] = None,
        status: Optional[HotelStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Hotel], int]:
        """
        Filter hotels by city.

        Args:
            db: Database session
            city: City to filter by
            brand: Optional brand filter
            status: Optional status filter
            is_active: Optional active status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Hotel instances, total count)
        """
        return await self.search_hotels(
            db,
            city=city,
            brand=brand,
            status=status,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    async def get_hotels_paginated(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        brand: Optional[HotelBrand] = None,
        status: Optional[HotelStatus] = None,
        city: Optional[str] = None,
        is_active: Optional[bool] = None,
        order_by: str = "updated_at",
        order_desc: bool = True,
    ) -> Dict[str, Any]:
        """
        Get hotels with pagination information.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of records per page
            brand: Optional brand filter
            status: Optional status filter
            city: Optional city filter
            is_active: Optional active status filter
            order_by: Field to order by
            order_desc: Whether to order in descending order

        Returns:
            Dictionary with hotels, pagination info, and total count
        """
        skip = (page - 1) * page_size

        hotels, total = await self.search_hotels(
            db,
            brand=brand,
            status=status,
            city=city,
            is_active=is_active,
            skip=skip,
            limit=page_size,
            order_by=order_by,
            order_desc=order_desc,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "items": hotels,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    async def get_all_cities(
        self,
        db: AsyncSession,
        *,
        brand: Optional[HotelBrand] = None,
        status: Optional[HotelStatus] = None,
    ) -> List[str]:
        """
        Get all unique cities from hotels.

        Args:
            db: Database session
            brand: Optional brand filter
            status: Optional status filter

        Returns:
            List of unique city names
        """
        query = select(Hotel.city).distinct()

        filters = []
        if brand:
            filters.append(Hotel.brand == brand)
        if status:
            filters.append(Hotel.status == status)

        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query)
        return [row[0] for row in result.fetchall()]

    async def get_all_brands(
        self,
        db: AsyncSession,
        *,
        city: Optional[str] = None,
        status: Optional[HotelStatus] = None,
    ) -> List[HotelBrand]:
        """
        Get all unique brands from hotels.

        Args:
            db: Database session
            city: Optional city filter
            status: Optional status filter

        Returns:
            List of unique hotel brands
        """
        query = select(Hotel.brand).distinct()

        filters = []
        if city:
            filters.append(Hotel.city == city)
        if status:
            filters.append(Hotel.status == status)

        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query)
        return [row[0] for row in result.fetchall()]


# Global instance
hotel_search = HotelSearchService()
