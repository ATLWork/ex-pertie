"""
CRUD service for TranslationReference model.
"""

from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.translation import ReferenceSource, TranslationReference
from app.schemas.translation import (
    TranslationReferenceCreate,
    TranslationReferenceUpdate,
    TranslationReferenceQuery,
    TranslationReferenceBulkCreate,
)
from app.services.base import CRUDBase


class CRUDTranslationReference(
    CRUDBase[TranslationReference, TranslationReferenceCreate, TranslationReferenceUpdate]
):
    """
    CRUD operations for TranslationReference model.
    """

    async def find_match(
        self,
        db: AsyncSession,
        *,
        source_text: str,
        source_lang: str,
        target_lang: str,
        min_confidence: float = 0.8,
    ) -> Optional[TranslationReference]:
        """
        Find the best matching reference for a source text.

        Args:
            db: Database session
            source_text: Source text to match
            source_lang: Source language code
            target_lang: Target language code
            min_confidence: Minimum confidence threshold

        Returns:
            Best matching TranslationReference or None
        """
        result = await db.execute(
            select(TranslationReference)
            .where(
                and_(
                    TranslationReference.source_text == source_text,
                    TranslationReference.source_lang == source_lang,
                    TranslationReference.target_lang == target_lang,
                    TranslationReference.confidence >= min_confidence,
                )
            )
            .order_by(TranslationReference.confidence.desc())
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
    ) -> List[TranslationReference]:
        """
        Find similar references (contains search).

        Args:
            db: Database session
            source_text: Source text to search
            source_lang: Source language code
            target_lang: Target language code
            limit: Maximum results to return

        Returns:
            List of similar TranslationReference instances
        """
        result = await db.execute(
            select(TranslationReference)
            .where(
                and_(
                    TranslationReference.source_text.contains(source_text),
                    TranslationReference.source_lang == source_lang,
                    TranslationReference.target_lang == target_lang,
                )
            )
            .order_by(TranslationReference.confidence.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_languages(
        self,
        db: AsyncSession,
        *,
        source_lang: str,
        target_lang: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TranslationReference]:
        """
        Get all references for a language pair.

        Args:
            db: Database session
            source_lang: Source language code
            target_lang: Target language code
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of TranslationReference instances
        """
        result = await db.execute(
            select(TranslationReference)
            .where(
                and_(
                    TranslationReference.source_lang == source_lang,
                    TranslationReference.target_lang == target_lang,
                )
            )
            .order_by(TranslationReference.confidence.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: TranslationReferenceQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TranslationReference]:
        """
        Search translation references with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of TranslationReference instances
        """
        query = select(TranslationReference)

        if query_params.source_lang:
            query = query.where(TranslationReference.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(TranslationReference.target_lang == query_params.target_lang)
        if query_params.source:
            query = query.where(TranslationReference.source == query_params.source)
        if query_params.min_confidence is not None:
            query = query.where(TranslationReference.confidence >= query_params.min_confidence)

        query = query.order_by(TranslationReference.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: TranslationReferenceQuery,
    ) -> int:
        """
        Count translation references matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(TranslationReference)

        if query_params.source_lang:
            query = query.where(TranslationReference.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(TranslationReference.target_lang == query_params.target_lang)
        if query_params.source:
            query = query.where(TranslationReference.source == query_params.source)
        if query_params.min_confidence is not None:
            query = query.where(TranslationReference.confidence >= query_params.min_confidence)

        result = await db.execute(query)
        return result.scalar_one()

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        obj_in: TranslationReferenceBulkCreate,
    ) -> List[TranslationReference]:
        """
        Bulk create translation references.

        Args:
            db: Database session
            obj_in: Bulk create schema with list of items

        Returns:
            List of created TranslationReference instances
        """
        created = []
        for item in obj_in.items:
            db_obj = TranslationReference(**item.model_dump())
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def update_confidence(
        self,
        db: AsyncSession,
        *,
        id: int,
        confidence: float,
    ) -> Optional[TranslationReference]:
        """
        Update confidence score for a reference.

        Args:
            db: Database session
            id: Reference ID
            confidence: New confidence score

        Returns:
            Updated TranslationReference or None
        """
        ref = await self.get(db, id)
        if ref:
            ref.confidence = confidence
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
        Get statistics for translation references.

        Args:
            db: Database session
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Dictionary with statistics
        """
        base_query = select(TranslationReference)

        if source_lang:
            base_query = base_query.where(TranslationReference.source_lang == source_lang)
        if target_lang:
            base_query = base_query.where(TranslationReference.target_lang == target_lang)

        # Total count
        total_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar_one()

        # Count by source
        source_result = await db.execute(
            select(
                TranslationReference.source,
                func.count().label("count"),
            )
            .select_from(base_query.subquery())
            .group_by(TranslationReference.source)
        )
        by_source = {row.source: row.count for row in source_result.all()}

        # Average confidence
        avg_result = await db.execute(
            select(func.avg(TranslationReference.confidence)).select_from(base_query.subquery())
        )
        avg_confidence = avg_result.scalar_one() or 0.0

        return {
            "total": total,
            "by_source": by_source,
            "average_confidence": round(avg_confidence, 3),
        }


# Global instance
translation_reference = CRUDTranslationReference(TranslationReference)
