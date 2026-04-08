"""
CRUD service for TranslationHistory model.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Integer, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.translation import TranslationHistory, TranslationType
from app.schemas.translation import TranslationHistoryCreate
from app.services.base import CRUDBase


class CRUDTranslationHistory(CRUDBase[TranslationHistory, TranslationHistoryCreate, dict]):
    """
    CRUD operations for TranslationHistory model.
    Note: Translation history is typically write-only (no update operations).
    """

    async def get_recent(
        self,
        db: AsyncSession,
        *,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        limit: int = 100,
    ) -> List[TranslationHistory]:
        """
        Get recent translation history.

        Args:
            db: Database session
            source_lang: Optional source language filter
            target_lang: Optional target language filter
            limit: Maximum records to return

        Returns:
            List of TranslationHistory entries
        """
        query = select(TranslationHistory)

        if source_lang:
            query = query.where(TranslationHistory.source_lang == source_lang)
        if target_lang:
            query = query.where(TranslationHistory.target_lang == target_lang)

        query = query.order_by(TranslationHistory.created_at.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TranslationHistory]:
        """
        Get translation history within a date range.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            source_lang: Optional source language filter
            target_lang: Optional target language filter
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of TranslationHistory entries
        """
        query = select(TranslationHistory).where(
            and_(
                TranslationHistory.created_at >= start_date,
                TranslationHistory.created_at <= end_date,
            )
        )

        if source_lang:
            query = query.where(TranslationHistory.source_lang == source_lang)
        if target_lang:
            query = query.where(TranslationHistory.target_lang == target_lang)

        query = query.order_by(TranslationHistory.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> dict:
        """
        Get translation statistics.

        Args:
            db: Database session
            start_date: Optional start date
            end_date: Optional end date
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Dictionary with statistics
        """
        base_conditions = []

        if start_date:
            base_conditions.append(TranslationHistory.created_at >= start_date)
        if end_date:
            base_conditions.append(TranslationHistory.created_at <= end_date)
        if source_lang:
            base_conditions.append(TranslationHistory.source_lang == source_lang)
        if target_lang:
            base_conditions.append(TranslationHistory.target_lang == target_lang)

        # Total count
        total_query = select(func.count()).select_from(TranslationHistory)
        if base_conditions:
            total_query = total_query.where(and_(*base_conditions))
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Count by translation type
        type_query = select(
            TranslationHistory.translation_type,
            func.count().label("count"),
        )
        if base_conditions:
            type_query = type_query.where(and_(*base_conditions))
        type_query = type_query.group_by(TranslationHistory.translation_type)
        type_result = await db.execute(type_query)
        by_type = {row.translation_type.value: row.count for row in type_result.all()}

        # Reference and glossary usage
        ref_query = select(
            func.sum(case((TranslationHistory.reference_used == True, 1), else_=0)).label("reference_count"),
            func.sum(case((TranslationHistory.glossary_used == True, 1), else_=0)).label("glossary_count"),
        )
        if base_conditions:
            ref_query = ref_query.where(and_(*base_conditions))
        ref_result = await db.execute(ref_query)
        ref_row = ref_result.one()
        reference_usage = ref_row.reference_count or 0
        glossary_usage = ref_row.glossary_count or 0

        # Average confidence
        avg_query = select(func.avg(TranslationHistory.confidence_score))
        if base_conditions:
            avg_query = avg_query.where(and_(*base_conditions))
        avg_result = await db.execute(avg_query)
        avg_confidence = avg_result.scalar_one() or 0.0

        return {
            "total": total,
            "by_type": by_type,
            "reference_usage": reference_usage,
            "glossary_usage": glossary_usage,
            "average_confidence": round(avg_confidence, 3),
            "reference_usage_rate": round(reference_usage / total, 3) if total > 0 else 0,
            "glossary_usage_rate": round(glossary_usage / total, 3) if total > 0 else 0,
        }

    async def get_language_pairs(
        self,
        db: AsyncSession,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Get translation counts by language pairs.

        Args:
            db: Database session
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of dictionaries with language pair statistics
        """
        query = select(
            TranslationHistory.source_lang,
            TranslationHistory.target_lang,
            func.count().label("count"),
        )

        conditions = []
        if start_date:
            conditions.append(TranslationHistory.created_at >= start_date)
        if end_date:
            conditions.append(TranslationHistory.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.group_by(
            TranslationHistory.source_lang,
            TranslationHistory.target_lang,
        ).order_by(func.count().desc())

        result = await db.execute(query)
        return [
            {
                "source_lang": row.source_lang,
                "target_lang": row.target_lang,
                "count": row.count,
            }
            for row in result.all()
        ]

    async def get_daily_counts(
        self,
        db: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> List[dict]:
        """
        Get daily translation counts.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            List of dictionaries with daily counts
        """
        # Use date function to extract date from timestamp
        query = select(
            func.date(TranslationHistory.created_at).label("date"),
            func.count().label("count"),
        ).where(
            and_(
                TranslationHistory.created_at >= start_date,
                TranslationHistory.created_at <= end_date,
            )
        )

        if source_lang:
            query = query.where(TranslationHistory.source_lang == source_lang)
        if target_lang:
            query = query.where(TranslationHistory.target_lang == target_lang)

        query = query.group_by(func.date(TranslationHistory.created_at)).order_by(
            func.date(TranslationHistory.created_at)
        )

        result = await db.execute(query)
        return [
            {
                "date": str(row.date),
                "count": row.count,
            }
            for row in result.all()
        ]

    async def cleanup_old(
        self,
        db: AsyncSession,
        *,
        days: int = 90,
    ) -> int:
        """
        Delete translation history older than specified days.

        Args:
            db: Database session
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.now() - __import__("datetime").timedelta(days=days)

        result = await db.execute(
            select(TranslationHistory).where(TranslationHistory.created_at < cutoff_date)
        )
        old_records = list(result.scalars().all())

        for record in old_records:
            await db.delete(record)

        await db.flush()
        return len(old_records)


# Global instance
translation_history = CRUDTranslationHistory(TranslationHistory)
