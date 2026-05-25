"""
CRUD service for Terminology model.
"""

from typing import List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.terminology import Terminology, TerminologyCategory
from app.schemas.translation import (
    TerminologyCreate,
    TerminologyUpdate,
    TerminologyQuery,
)
from app.services.base import CRUDBase


class CRUDTerminology(CRUDBase[Terminology, TerminologyCreate, TerminologyUpdate]):
    """
    CRUD operations for Terminology model.
    """

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> Optional[Terminology]:
        """
        Get a terminology entry by name.

        Args:
            db: Database session
            name: Terminology name
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Terminology entry or None
        """
        query = select(Terminology).where(Terminology.name == name)

        if source_lang:
            query = query.where(Terminology.source_lang == source_lang)
        if target_lang:
            query = query.where(Terminology.target_lang == target_lang)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_source_text(
        self,
        db: AsyncSession,
        *,
        source_text: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[Terminology]:
        """
        Get a terminology entry by source text and language pair.

        Args:
            db: Database session
            source_text: Source text to search
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Terminology entry or None
        """
        result = await db.execute(
            select(Terminology).where(
                and_(
                    Terminology.source_text == source_text,
                    Terminology.source_lang == source_lang,
                    Terminology.target_lang == target_lang,
                )
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: TerminologyQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Terminology]:
        """
        Search terminology entries with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of Terminology entries
        """
        query = select(Terminology)

        if query_params.source_lang:
            query = query.where(Terminology.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(Terminology.target_lang == query_params.target_lang)
        if query_params.domain:
            query = query.where(Terminology.domain == query_params.domain)
        if query_params.is_active is not None:
            query = query.where(Terminology.is_active == query_params.is_active)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    Terminology.name.ilike(search_term),
                    Terminology.source_text.ilike(search_term),
                )
            )

        query = query.order_by(Terminology.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: TerminologyQuery,
    ) -> int:
        """
        Count terminology entries matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(Terminology)

        if query_params.source_lang:
            query = query.where(Terminology.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(Terminology.target_lang == query_params.target_lang)
        if query_params.domain:
            query = query.where(Terminology.domain == query_params.domain)
        if query_params.is_active is not None:
            query = query.where(Terminology.is_active == query_params.is_active)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    Terminology.name.ilike(search_term),
                    Terminology.source_text.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar_one()

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        items: List[TerminologyCreate],
    ) -> List[Terminology]:
        """
        Bulk create terminology entries.

        Args:
            db: Database session
            items: List of terminology items to create

        Returns:
            List of created Terminology entries
        """
        created = []
        for item in items:
            db_obj = Terminology(**item.model_dump())
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def get_active_terms(
        self,
        db: AsyncSession,
        *,
        source_lang: str,
        target_lang: str,
        domain: Optional[TerminologyCategory] = None,
    ) -> List[Terminology]:
        """
        Get all active terms for a language pair.

        Args:
            db: Database session
            source_lang: Source language code
            target_lang: Target language code
            domain: Optional domain filter

        Returns:
            List of active Terminology entries
        """
        query = select(Terminology).where(
            and_(
                Terminology.source_lang == source_lang,
                Terminology.target_lang == target_lang,
                Terminology.is_active == True,
            )
        )

        if domain:
            query = query.where(Terminology.domain == domain)

        result = await db.execute(query.order_by(Terminology.name))
        return list(result.scalars().all())

    async def lookup_in_text(
        self,
        db: AsyncSession,
        *,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> List[Terminology]:
        """
        Find all terminology entries that appear in the given text.

        Args:
            db: Database session
            text: Text to search in
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of matching Terminology entries
        """
        result = await db.execute(
            select(Terminology).where(
                and_(
                    Terminology.source_lang == source_lang,
                    Terminology.target_lang == target_lang,
                    Terminology.is_active == True,
                    text.contains(Terminology.source_text),
                )
            )
        )
        return list(result.scalars().all())

    async def activate(self, db: AsyncSession, *, id: int) -> Optional[Terminology]:
        """
        Activate a terminology entry.

        Args:
            db: Database session
            id: Terminology ID

        Returns:
            Updated Terminology or None
        """
        entry = await self.get(db, id)
        if entry:
            entry.is_active = True
            db.add(entry)
            await db.flush()
            await db.refresh(entry)
            return entry
        return None

    async def deactivate(self, db: AsyncSession, *, id: int) -> Optional[Terminology]:
        """
        Deactivate a terminology entry.

        Args:
            db: Database session
            id: Terminology ID

        Returns:
            Updated Terminology or None
        """
        entry = await self.get(db, id)
        if entry:
            entry.is_active = False
            db.add(entry)
            await db.flush()
            await db.refresh(entry)
            return entry
        return None

    async def get_domains(
        self,
        db: AsyncSession,
        *,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> dict:
        """
        Get count of terms by domain.

        Args:
            db: Database session
            source_lang: Optional source language filter
            target_lang: Optional target language filter

        Returns:
            Dictionary with domain counts
        """
        query = select(
            Terminology.domain,
            func.count().label("count"),
        ).where(Terminology.is_active == True)

        if source_lang:
            query = query.where(Terminology.source_lang == source_lang)
        if target_lang:
            query = query.where(Terminology.target_lang == target_lang)

        query = query.group_by(Terminology.domain)

        result = await db.execute(query)
        return {row.domain.value: row.count for row in result.all()}


# Global instance
terminology = CRUDTerminology(Terminology)