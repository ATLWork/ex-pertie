"""
CRUD service for TranslationRule model.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.translation import RuleType, TranslationRule
from app.schemas.translation import TranslationRuleCreate, TranslationRuleUpdate, TranslationRuleQuery
from app.services.base import CRUDBase


class CRUDTranslationRule(CRUDBase[TranslationRule, TranslationRuleCreate, TranslationRuleUpdate]):
    """
    CRUD operations for TranslationRule model.
    """

    async def get_by_name(
        self, db: AsyncSession, *, name: str
    ) -> Optional[TranslationRule]:
        """
        Get a translation rule by name.

        Args:
            db: Database session
            name: Rule name

        Returns:
            TranslationRule or None
        """
        result = await db.execute(
            select(TranslationRule).where(TranslationRule.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active_rules(
        self,
        db: AsyncSession,
        *,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> List[TranslationRule]:
        """
        Get all active rules with optional filtering.

        Args:
            db: Database session
            source_lang: Filter by source language
            target_lang: Filter by target language
            field_name: Filter by field name

        Returns:
            List of active TranslationRule instances
        """
        query = select(TranslationRule).where(TranslationRule.is_active == True)

        if source_lang:
            query = query.where(TranslationRule.source_lang == source_lang)
        if target_lang:
            query = query.where(TranslationRule.target_lang == target_lang)
        if field_name:
            query = query.where(TranslationRule.field_name == field_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_rules_by_type(
        self,
        db: AsyncSession,
        *,
        rule_type: RuleType,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> List[TranslationRule]:
        """
        Get rules by type with optional language filtering.

        Args:
            db: Database session
            rule_type: Rule type filter
            source_lang: Filter by source language
            target_lang: Filter by target language

        Returns:
            List of TranslationRule instances
        """
        query = select(TranslationRule).where(
            and_(
                TranslationRule.rule_type == rule_type,
                TranslationRule.is_active == True,
            )
        )

        if source_lang:
            query = query.where(TranslationRule.source_lang == source_lang)
        if target_lang:
            query = query.where(TranslationRule.target_lang == target_lang)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: TranslationRuleQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TranslationRule]:
        """
        Search translation rules with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of TranslationRule instances
        """
        query = select(TranslationRule)

        if query_params.source_lang:
            query = query.where(TranslationRule.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(TranslationRule.target_lang == query_params.target_lang)
        if query_params.field_name:
            query = query.where(TranslationRule.field_name == query_params.field_name)
        if query_params.rule_type:
            query = query.where(TranslationRule.rule_type == query_params.rule_type)
        if query_params.is_active is not None:
            query = query.where(TranslationRule.is_active == query_params.is_active)

        query = query.order_by(TranslationRule.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: TranslationRuleQuery,
    ) -> int:
        """
        Count translation rules matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(TranslationRule)

        if query_params.source_lang:
            query = query.where(TranslationRule.source_lang == query_params.source_lang)
        if query_params.target_lang:
            query = query.where(TranslationRule.target_lang == query_params.target_lang)
        if query_params.field_name:
            query = query.where(TranslationRule.field_name == query_params.field_name)
        if query_params.rule_type:
            query = query.where(TranslationRule.rule_type == query_params.rule_type)
        if query_params.is_active is not None:
            query = query.where(TranslationRule.is_active == query_params.is_active)

        result = await db.execute(query)
        return result.scalar_one()

    async def activate(self, db: AsyncSession, *, id: int) -> Optional[TranslationRule]:
        """
        Activate a translation rule.

        Args:
            db: Database session
            id: Rule ID

        Returns:
            Updated TranslationRule or None
        """
        rule = await self.get(db, id)
        if rule:
            rule.is_active = True
            db.add(rule)
            await db.flush()
            await db.refresh(rule)
            return rule
        return None

    async def deactivate(self, db: AsyncSession, *, id: int) -> Optional[TranslationRule]:
        """
        Deactivate a translation rule.

        Args:
            db: Database session
            id: Rule ID

        Returns:
            Updated TranslationRule or None
        """
        rule = await self.get(db, id)
        if rule:
            rule.is_active = False
            db.add(rule)
            await db.flush()
            await db.refresh(rule)
            return rule
        return None


# Global instance
translation_rule = CRUDTranslationRule(TranslationRule)
