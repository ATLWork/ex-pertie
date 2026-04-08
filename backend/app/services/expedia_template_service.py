"""
CRUD service for ExpediaTemplate model.
"""

from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expedia_template import ExpediaTemplate, TemplateStatus, TemplateType
from app.schemas.expedia_template import (
    ExpediaTemplateCreate,
    ExpediaTemplateUpdate,
    ExpediaTemplateQuery,
)
from app.services.base import CRUDBase


class CRUDExpediaTemplate(CRUDBase[ExpediaTemplate, ExpediaTemplateCreate, ExpediaTemplateUpdate]):
    """
    CRUD operations for ExpediaTemplate model.
    """

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Optional[ExpediaTemplate]:
        """
        Get a template by its code.

        Args:
            db: Database session
            code: Template code

        Returns:
            ExpediaTemplate instance or None
        """
        result = await db.execute(
            select(ExpediaTemplate).where(ExpediaTemplate.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_code_with_mappings(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Optional[ExpediaTemplate]:
        """
        Get a template by its code with field mappings loaded.

        Args:
            db: Database session
            code: Template code

        Returns:
            ExpediaTemplate instance with field_mappings or None
        """
        result = await db.execute(
            select(ExpediaTemplate)
            .where(ExpediaTemplate.code == code)
            .options(selectinload(ExpediaTemplate.field_mappings))
        )
        return result.scalar_one_or_none()

    async def get_active_templates(
        self,
        db: AsyncSession,
        *,
        template_type: Optional[TemplateType] = None,
    ) -> List[ExpediaTemplate]:
        """
        Get all active templates.

        Args:
            db: Database session
            template_type: Optional template type filter

        Returns:
            List of active ExpediaTemplate instances
        """
        query = select(ExpediaTemplate).where(
            ExpediaTemplate.status == TemplateStatus.ACTIVE
        )

        if template_type:
            query = query.where(ExpediaTemplate.template_type == template_type)

        query = query.order_by(ExpediaTemplate.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        db: AsyncSession,
        *,
        template_type: TemplateType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ExpediaTemplate]:
        """
        Get templates by type.

        Args:
            db: Database session
            template_type: Template type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ExpediaTemplate instances
        """
        result = await db.execute(
            select(ExpediaTemplate)
            .where(ExpediaTemplate.template_type == template_type)
            .order_by(ExpediaTemplate.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_mappings(
        self,
        db: AsyncSession,
        *,
        id: int,
    ) -> Optional[ExpediaTemplate]:
        """
        Get a template by ID with field mappings loaded.

        Args:
            db: Database session
            id: Template ID

        Returns:
            ExpediaTemplate instance with field_mappings or None
        """
        result = await db.execute(
            select(ExpediaTemplate)
            .where(ExpediaTemplate.id == id)
            .options(selectinload(ExpediaTemplate.field_mappings))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: ExpediaTemplateQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ExpediaTemplate]:
        """
        Search templates with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of ExpediaTemplate instances
        """
        query = select(ExpediaTemplate)

        if query_params.code:
            query = query.where(ExpediaTemplate.code == query_params.code)
        if query_params.template_type:
            query = query.where(ExpediaTemplate.template_type == query_params.template_type)
        if query_params.status:
            query = query.where(ExpediaTemplate.status == query_params.status)
        if query_params.is_active is not None:
            if query_params.is_active:
                query = query.where(ExpediaTemplate.status == TemplateStatus.ACTIVE)
            else:
                query = query.where(ExpediaTemplate.status != TemplateStatus.ACTIVE)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    ExpediaTemplate.name.ilike(search_term),
                    ExpediaTemplate.code.ilike(search_term),
                    ExpediaTemplate.description.ilike(search_term),
                )
            )

        query = query.order_by(ExpediaTemplate.updated_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: ExpediaTemplateQuery,
    ) -> int:
        """
        Count templates matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(ExpediaTemplate)

        if query_params.code:
            query = query.where(ExpediaTemplate.code == query_params.code)
        if query_params.template_type:
            query = query.where(ExpediaTemplate.template_type == query_params.template_type)
        if query_params.status:
            query = query.where(ExpediaTemplate.status == query_params.status)
        if query_params.is_active is not None:
            if query_params.is_active:
                query = query.where(ExpediaTemplate.status == TemplateStatus.ACTIVE)
            else:
                query = query.where(ExpediaTemplate.status != TemplateStatus.ACTIVE)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    ExpediaTemplate.name.ilike(search_term),
                    ExpediaTemplate.code.ilike(search_term),
                    ExpediaTemplate.description.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar_one()

    async def get_by_expedia_id(
        self,
        db: AsyncSession,
        *,
        expedia_template_id: str,
    ) -> Optional[ExpediaTemplate]:
        """
        Get a template by Expedia template ID.

        Args:
            db: Database session
            expedia_template_id: Expedia template ID

        Returns:
            ExpediaTemplate instance or None
        """
        result = await db.execute(
            select(ExpediaTemplate).where(
                ExpediaTemplate.expedia_template_id == expedia_template_id
            )
        )
        return result.scalar_one_or_none()

    async def activate(self, db: AsyncSession, *, id: int) -> Optional[ExpediaTemplate]:
        """
        Activate a template.

        Args:
            db: Database session
            id: Template ID

        Returns:
            Updated ExpediaTemplate or None
        """
        obj = await self.get(db, id)
        if obj:
            obj.status = TemplateStatus.ACTIVE
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
        return obj

    async def deactivate(self, db: AsyncSession, *, id: int) -> Optional[ExpediaTemplate]:
        """
        Deactivate a template.

        Args:
            db: Database session
            id: Template ID

        Returns:
            Updated ExpediaTemplate or None
        """
        obj = await self.get(db, id)
        if obj:
            obj.status = TemplateStatus.DEPRECATED
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
        return obj

    async def archive(self, db: AsyncSession, *, id: int) -> Optional[ExpediaTemplate]:
        """
        Archive a template.

        Args:
            db: Database session
            id: Template ID

        Returns:
            Updated ExpediaTemplate or None
        """
        obj = await self.get(db, id)
        if obj:
            obj.status = TemplateStatus.ARCHIVED
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
        return obj

    async def create_version(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        new_version: str,
    ) -> Optional[ExpediaTemplate]:
        """
        Create a new version of a template.

        Args:
            db: Database session
            template_id: Original template ID
            new_version: New version string

        Returns:
            New ExpediaTemplate instance or None
        """
        original = await self.get(db, int(template_id))
        if not original:
            return None

        # Create new template as a copy
        new_template = ExpediaTemplate(
            name=original.name,
            code=f"{original.code}_v{new_version.replace('.', '_')}",
            description=original.description,
            template_type=original.template_type,
            status=TemplateStatus.DRAFT,
            version=new_version,
            parent_template_id=original.id,
            expedia_template_name=original.expedia_template_name,
            expedia_template_id=original.expedia_template_id,
            expedia_version=original.expedia_version,
            header_row=original.header_row,
            data_start_row=original.data_start_row,
            sheet_name=original.sheet_name,
            config=original.config,
            sample_file_path=original.sample_file_path,
        )

        db.add(new_template)
        await db.flush()
        await db.refresh(new_template)
        return new_template

    async def get_statistics(
        self,
        db: AsyncSession,
    ) -> dict:
        """
        Get template statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with template statistics
        """
        # Count by status
        status_query = select(
            ExpediaTemplate.status,
            func.count().label("count"),
        ).group_by(ExpediaTemplate.status)

        status_result = await db.execute(status_query)
        status_counts = {row.status.value: row.count for row in status_result.all()}

        # Count by type
        type_query = select(
            ExpediaTemplate.template_type,
            func.count().label("count"),
        ).group_by(ExpediaTemplate.template_type)

        type_result = await db.execute(type_query)
        type_counts = {row.template_type.value: row.count for row in type_result.all()}

        # Total count
        total_result = await db.execute(select(func.count()).select_from(ExpediaTemplate))
        total = total_result.scalar_one()

        return {
            "total": total,
            "by_status": status_counts,
            "by_type": type_counts,
        }


class ExpediaTemplateService:
    """
    Service class for Expedia template operations.
    Wraps CRUDExpediaTemplate with additional business logic.
    """

    def __init__(self):
        self.crud = CRUDExpediaTemplate(ExpediaTemplate)

    async def get_template_by_code(
        self,
        db: AsyncSession,
        code: str,
        *,
        include_mappings: bool = False,
    ) -> Optional[ExpediaTemplate]:
        """
        Get a template by code.

        Args:
            db: Database session
            code: Template code
            include_mappings: Whether to load field mappings

        Returns:
            ExpediaTemplate instance or None
        """
        if include_mappings:
            return await self.crud.get_by_code_with_mappings(db, code=code)
        return await self.crud.get_by_code(db, code=code)

    async def get_active_templates(
        self,
        db: AsyncSession,
        *,
        template_type: Optional[TemplateType] = None,
    ) -> List[ExpediaTemplate]:
        """
        Get all active templates.

        Args:
            db: Database session
            template_type: Optional template type filter

        Returns:
            List of active ExpediaTemplate instances
        """
        return await self.crud.get_active_templates(db, template_type=template_type)


# Global instance
expedia_template_service = ExpediaTemplateService()


# Keep CRUDExpediaTemplate accessible for direct use
expedia_template = CRUDExpediaTemplate(ExpediaTemplate)
