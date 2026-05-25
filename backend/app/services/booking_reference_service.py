"""
CRUD service for BookingReference model.
"""

from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.booking_reference import BookingReference
from app.schemas.booking_reference import (
    BookingReferenceCreate,
    BookingReferenceUpdate,
    BookingReferenceQuery,
    BookingReferenceBulkCreate,
)
from app.services.base import CRUDBase


class CRUDBookingReference(
    CRUDBase[BookingReference, BookingReferenceCreate, BookingReferenceUpdate]
):
    """
    CRUD operations for BookingReference model.
    """

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: BookingReferenceQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingReference]:
        """
        Search booking references with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of BookingReference instances
        """
        query = select(BookingReference)

        if query_params.source_lang:
            query = query.where(BookingReference.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(BookingReference.target_lang == query_params.target_lang)
        if query_params.hotel_name:
            query = query.where(BookingReference.hotel_name.ilike(f"%{query_params.hotel_name}%"))
        if query_params.hotel_address:
            query = query.where(BookingReference.hotel_address.ilike(f"%{query_params.hotel_address}%"))
        if query_params.source_text:
            query = query.where(BookingReference.source_text.ilike(f"%{query_params.source_text}%"))
        if query_params.is_active is not None:
            query = query.where(BookingReference.is_active == query_params.is_active)

        query = query.order_by(BookingReference.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: BookingReferenceQuery,
    ) -> int:
        """
        Count booking references matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(BookingReference)

        if query_params.source_lang:
            query = query.where(BookingReference.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(BookingReference.target_lang == query_params.target_lang)
        if query_params.hotel_name:
            query = query.where(BookingReference.hotel_name.ilike(f"%{query_params.hotel_name}%"))
        if query_params.hotel_address:
            query = query.where(BookingReference.hotel_address.ilike(f"%{query_params.hotel_address}%"))
        if query_params.source_text:
            query = query.where(BookingReference.source_text.ilike(f"%{query_params.source_text}%"))
        if query_params.is_active is not None:
            query = query.where(BookingReference.is_active == query_params.is_active)

        result = await db.execute(query)
        return result.scalar_one()

    async def find_by_source_text(
        self,
        db: AsyncSession,
        *,
        source_text: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[BookingReference]:
        """
        Find a booking reference by source text exact match.

        Args:
            db: Database session
            source_text: Source text to match
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            BookingReference or None
        """
        result = await db.execute(
            select(BookingReference)
            .where(
                and_(
                    BookingReference.source_text == source_text,
                    BookingReference.source_lang == source_lang,
                    BookingReference.target_lang == target_lang,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_similar(
        self,
        db: AsyncSession,
        *,
        source_text: str,
        source_lang: str,
        target_lang: str,
        limit: int = 5,
    ) -> List[BookingReference]:
        """
        Find similar booking references (contains search).

        Args:
            db: Database session
            source_text: Source text to search
            source_lang: Source language code
            target_lang: Target language code
            limit: Maximum results to return

        Returns:
            List of similar BookingReference instances
        """
        result = await db.execute(
            select(BookingReference)
            .where(
                and_(
                    BookingReference.source_text.contains(source_text),
                    BookingReference.source_lang == source_lang,
                    BookingReference.target_lang == target_lang,
                    BookingReference.is_active == True,
                )
            )
            .order_by(BookingReference.usage_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_hotel(
        self,
        db: AsyncSession,
        *,
        hotel_name: str,
        source_lang: str,
        target_lang: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BookingReference]:
        """
        Find all booking references for a specific hotel.

        Args:
            db: Database session
            hotel_name: Hotel name to filter by
            source_lang: Source language code
            target_lang: Target language code
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of BookingReference instances for the hotel
        """
        result = await db.execute(
            select(BookingReference)
            .where(
                and_(
                    BookingReference.hotel_name.ilike(f"%{hotel_name}%"),
                    BookingReference.source_lang == source_lang,
                    BookingReference.target_lang == target_lang,
                    BookingReference.is_active == True,
                )
            )
            .order_by(BookingReference.usage_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        obj_in: BookingReferenceBulkCreate,
    ) -> List[BookingReference]:
        """
        Bulk create booking references.

        Args:
            db: Database session
            obj_in: Bulk create schema with list of items

        Returns:
            List of created BookingReference instances
        """
        created = []
        for item in obj_in.items:
            db_obj = BookingReference(**item.model_dump())
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def bulk_upsert(
        self,
        db: AsyncSession,
        *,
        obj_in: BookingReferenceBulkCreate,
    ) -> List[BookingReference]:
        """
        Bulk upsert booking references (insert or update on conflict).

        Args:
            db: Database session
            obj_in: Bulk create schema with list of items

        Returns:
            List of created or updated BookingReference instances
        """
        results = []
        for item in obj_in.items:
            existing = await self.find_by_source_text(
                db,
                source_text=item.source_text,
                source_lang=item.source_lang,
                target_lang=item.target_lang,
            )
            if existing:
                # Update existing record
                for field, value in item.model_dump(exclude_unset=True).items():
                    if value is not None:
                        setattr(existing, field, value)
                db.add(existing)
                await db.flush()
                await db.refresh(existing)
                results.append(existing)
            else:
                # Create new record
                db_obj = BookingReference(**item.model_dump())
                db.add(db_obj)
                await db.flush()
                await db.refresh(db_obj)
                results.append(db_obj)

        return results

    async def increment_usage(
        self,
        db: AsyncSession,
        *,
        id: int,
    ) -> Optional[BookingReference]:
        """
        Increment usage count for a reference.

        Args:
            db: Database session
            id: Reference ID

        Returns:
            Updated BookingReference or None
        """
        ref = await self.get(db, id)
        if ref:
            ref.usage_count += 1
            db.add(ref)
            await db.flush()
            await db.refresh(ref)
            return ref
        return None

    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> dict:
        """
        Get statistics for booking references.

        Args:
            db: Database session
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Dictionary with statistics
        """
        base_query = select(BookingReference)

        if source_lang:
            base_query = base_query.where(BookingReference.source_lang == source_lang)
        if target_lang:
            base_query = base_query.where(BookingReference.target_lang == target_lang)

        # Total count
        total_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar_one()

        # References with Ctrip translation
        ctrip_result = await db.execute(
            select(func.count())
            .select_from(BookingReference)
            .where(
                and_(
                    BookingReference.ctrip_translation.isnot(None),
                    base_query.whereclause if hasattr(base_query, 'whereclause') else True,
                )
            )
        )
        ctrip_count = ctrip_result.scalar_one()

        # References with Booking.com translation
        booking_result = await db.execute(
            select(func.count())
            .select_from(BookingReference)
            .where(
                and_(
                    BookingReference.booking_translation.isnot(None),
                    base_query.whereclause if hasattr(base_query, 'whereclause') else True,
                )
            )
        )
        booking_count = booking_result.scalar_one()

        # Count by hotel
        hotel_result = await db.execute(
            select(BookingReference.hotel_name, func.count().label("count"))
            .select_from(base_query.subquery())
            .where(BookingReference.hotel_name.isnot(None))
            .group_by(BookingReference.hotel_name)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_hotels = {row.hotel_name: row.count for row in hotel_result.all()}

        # Total usage count
        usage_result = await db.execute(
            select(func.sum(BookingReference.usage_count)).select_from(base_query.subquery())
        )
        total_usage = usage_result.scalar_one() or 0

        return {
            "total": total,
            "ctrip_translations": ctrip_count,
            "booking_translations": booking_count,
            "top_hotels": top_hotels,
            "total_usage_count": total_usage,
        }


# Global instance
booking_reference = CRUDBookingReference(BookingReference)