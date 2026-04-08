"""
CRUD service for Glossary model.
"""

from typing import List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.translation import Glossary, GlossaryCategory
from app.schemas.translation import (
    GlossaryCreate,
    GlossaryUpdate,
    GlossaryQuery,
    GlossaryBulkCreate,
)
from app.services.base import CRUDBase


class CRUDGlossary(CRUDBase[Glossary, GlossaryCreate, GlossaryUpdate]):
    """
    CRUD operations for Glossary model.
    """

    async def get_by_term(
        self,
        db: AsyncSession,
        *,
        term: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[Glossary]:
        """
        Get a glossary entry by term and language pair.

        Args:
            db: Database session
            term: Term to search
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Glossary entry or None
        """
        result = await db.execute(
            select(Glossary).where(
                and_(
                    Glossary.term == term,
                    Glossary.source_lang == source_lang,
                    Glossary.target_lang == target_lang,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_terms(
        self,
        db: AsyncSession,
        *,
        source_lang: str,
        target_lang: str,
        category: Optional[GlossaryCategory] = None,
    ) -> List[Glossary]:
        """
        Get all active terms for a language pair.

        Args:
            db: Database session
            source_lang: Source language code
            target_lang: Target language code
            category: Optional category filter

        Returns:
            List of active Glossary entries
        """
        query = select(Glossary).where(
            and_(
                Glossary.source_lang == source_lang,
                Glossary.target_lang == target_lang,
                Glossary.is_active == True,
            )
        )

        if category:
            query = query.where(Glossary.category == category)

        result = await db.execute(query.order_by(Glossary.term))
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: GlossaryQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Glossary]:
        """
        Search glossary entries with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of Glossary entries
        """
        query = select(Glossary)

        if query_params.source_lang:
            query = query.where(Glossary.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(Glossary.target_lang == query_params.target_lang)
        if query_params.category:
            query = query.where(Glossary.category == query_params.category)
        if query_params.is_active is not None:
            query = query.where(Glossary.is_active == query_params.is_active)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    Glossary.term.ilike(search_term),
                    Glossary.translation.ilike(search_term),
                )
            )

        query = query.order_by(Glossary.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: GlossaryQuery,
    ) -> int:
        """
        Count glossary entries matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(Glossary)

        if query_params.source_lang:
            query = query.where(Glossary.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(Glossary.target_lang == query_params.target_lang)
        if query_params.category:
            query = query.where(Glossary.category == query_params.category)
        if query_params.is_active is not None:
            query = query.where(Glossary.is_active == query_params.is_active)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    Glossary.term.ilike(search_term),
                    Glossary.translation.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar_one()

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        obj_in: GlossaryBulkCreate,
    ) -> List[Glossary]:
        """
        Bulk create glossary entries.

        Args:
            db: Database session
            obj_in: Bulk create schema with list of items

        Returns:
            List of created Glossary entries
        """
        created = []
        for item in obj_in.items:
            db_obj = Glossary(**item.model_dump())
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def lookup_term(
        self,
        db: AsyncSession,
        *,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[Glossary]:
        """
        Look up a term in the glossary.

        Args:
            db: Database session
            text: Text to look up
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Glossary entry if found, None otherwise
        """
        result = await db.execute(
            select(Glossary).where(
                and_(
                    Glossary.term == text,
                    Glossary.source_lang == source_lang,
                    Glossary.target_lang == target_lang,
                    Glossary.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def lookup_in_text(
        self,
        db: AsyncSession,
        *,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> List[Glossary]:
        """
        Find all glossary terms that appear in the given text.

        Args:
            db: Database session
            text: Text to search in
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of matching Glossary entries
        """
        result = await db.execute(
            select(Glossary).where(
                and_(
                    Glossary.source_lang == source_lang,
                    Glossary.target_lang == target_lang,
                    Glossary.is_active == True,
                    text.contains(Glossary.term),
                )
            )
        )
        return list(result.scalars().all())

    async def activate(self, db: AsyncSession, *, id: int) -> Optional[Glossary]:
        """
        Activate a glossary entry.

        Args:
            db: Database session
            id: Glossary ID

        Returns:
            Updated Glossary or None
        """
        entry = await self.get(db, id)
        if entry:
            entry.is_active = True
            db.add(entry)
            await db.flush()
            await db.refresh(entry)
            return entry
        return None

    async def deactivate(self, db: AsyncSession, *, id: int) -> Optional[Glossary]:
        """
        Deactivate a glossary entry.

        Args:
            db: Database session
            id: Glossary ID

        Returns:
            Updated Glossary or None
        """
        entry = await self.get(db, id)
        if entry:
            entry.is_active = False
            db.add(entry)
            await db.flush()
            await db.refresh(entry)
            return entry
        return None

    async def get_categories(
        self,
        db: AsyncSession,
        *,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> dict:
        """
        Get count of terms by category.

        Args:
            db: Database session
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Dictionary with category counts
        """
        query = select(
            Glossary.category,
            func.count().label("count"),
        ).where(Glossary.is_active == True)

        if source_lang:
            query = query.where(Glossary.source_lang == source_lang)
        if target_lang:
            query = query.where(Glossary.target_lang == target_lang)

        query = query.group_by(Glossary.category)

        result = await db.execute(query)
        return {row.category.value: row.count for row in result.all()}


# Global instance
glossary = CRUDGlossary(Glossary)
