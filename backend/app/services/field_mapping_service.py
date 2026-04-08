"""
CRUD service for FieldMapping model.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expedia_template import FieldMapping, FieldMappingType, TemplateStatus
from app.schemas.expedia_template import (
    FieldMappingCreate,
    FieldMappingUpdate,
    FieldMappingQuery,
    FieldMappingBulkCreate,
)
from app.services.base import CRUDBase


class ValidationResult(BaseModel):
    """Result of mapping validation."""

    is_valid: bool
    errors: List[str] = []


class CRUDFieldMapping(CRUDBase[FieldMapping, FieldMappingCreate, FieldMappingUpdate]):
    """
    CRUD operations for FieldMapping model.
    """

    async def get_by_template(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FieldMapping]:
        """
        Get all field mappings for a template.

        Args:
            db: Database session
            template_id: Template ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of FieldMapping instances
        """
        result = await db.execute(
            select(FieldMapping)
            .where(FieldMapping.template_id == template_id)
            .order_by(FieldMapping.field_order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_mappings(
        self,
        db: AsyncSession,
        *,
        template_id: Optional[str] = None,
    ) -> List[FieldMapping]:
        """
        Get all active field mappings.

        Args:
            db: Database session
            template_id: Optional template ID to filter by

        Returns:
            List of active FieldMapping instances
        """
        query = select(FieldMapping).where(FieldMapping.is_active == True)

        if template_id:
            query = query.where(FieldMapping.template_id == template_id)

        query = query.order_by(FieldMapping.field_order)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_source_field(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        source_field: str,
    ) -> Optional[FieldMapping]:
        """
        Get a field mapping by template and source field.

        Args:
            db: Database session
            template_id: Template ID
            source_field: Source field name

        Returns:
            FieldMapping instance or None
        """
        result = await db.execute(
            select(FieldMapping).where(
                and_(
                    FieldMapping.template_id == template_id,
                    FieldMapping.source_field == source_field,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_target_field(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        target_field: str,
    ) -> Optional[FieldMapping]:
        """
        Get a field mapping by template and target field.

        Args:
            db: Database session
            template_id: Template ID
            target_field: Target field name

        Returns:
            FieldMapping instance or None
        """
        result = await db.execute(
            select(FieldMapping).where(
                and_(
                    FieldMapping.template_id == template_id,
                    FieldMapping.target_field == target_field,
                )
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        query_params: FieldMappingQuery,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FieldMapping]:
        """
        Search field mappings with query parameters.

        Args:
            db: Database session
            query_params: Query parameters
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of FieldMapping instances
        """
        query = select(FieldMapping)

        if query_params.template_id:
            query = query.where(FieldMapping.template_id == query_params.template_id)
        if query_params.source_field:
            query = query.where(FieldMapping.source_field == query_params.source_field)
        if query_params.target_field:
            query = query.where(FieldMapping.target_field == query_params.target_field)
        if query_params.mapping_type:
            query = query.where(FieldMapping.mapping_type == query_params.mapping_type)
        if query_params.is_active is not None:
            query = query.where(FieldMapping.is_active == query_params.is_active)
        if query_params.is_visible is not None:
            query = query.where(FieldMapping.is_visible == query_params.is_visible)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    FieldMapping.source_field.ilike(search_term),
                    FieldMapping.target_field.ilike(search_term),
                )
            )

        query = query.order_by(FieldMapping.field_order)
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_with_query(
        self,
        db: AsyncSession,
        *,
        query_params: FieldMappingQuery,
    ) -> int:
        """
        Count field mappings matching query parameters.

        Args:
            db: Database session
            query_params: Query parameters

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(FieldMapping)

        if query_params.template_id:
            query = query.where(FieldMapping.template_id == query_params.template_id)
        if query_params.source_field:
            query = query.where(FieldMapping.source_field == query_params.source_field)
        if query_params.target_field:
            query = query.where(FieldMapping.target_field == query_params.target_field)
        if query_params.mapping_type:
            query = query.where(FieldMapping.mapping_type == query_params.mapping_type)
        if query_params.is_active is not None:
            query = query.where(FieldMapping.is_active == query_params.is_active)
        if query_params.is_visible is not None:
            query = query.where(FieldMapping.is_visible == query_params.is_visible)
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.where(
                or_(
                    FieldMapping.source_field.ilike(search_term),
                    FieldMapping.target_field.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar_one()

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        obj_in: FieldMappingBulkCreate,
    ) -> List[FieldMapping]:
        """
        Bulk create field mappings.

        Args:
            db: Database session
            obj_in: Bulk create schema with list of items

        Returns:
            List of created FieldMapping instances
        """
        created = []
        for item in obj_in.items:
            db_obj = FieldMapping(**item.model_dump())
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def bulk_create_for_template(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        mappings: List[Dict[str, Any]],
    ) -> List[FieldMapping]:
        """
        Bulk create field mappings for a template.

        Args:
            db: Database session
            template_id: Template ID
            mappings: List of mapping data dictionaries

        Returns:
            List of created FieldMapping instances
        """
        created = []
        for idx, mapping_data in enumerate(mappings):
            mapping_data["template_id"] = template_id
            mapping_data["field_order"] = mapping_data.get("field_order", idx + 1)
            db_obj = FieldMapping(**mapping_data)
            db.add(db_obj)
            created.append(db_obj)

        await db.flush()
        for obj in created:
            await db.refresh(obj)

        return created

    async def activate(self, db: AsyncSession, *, id: int) -> Optional[FieldMapping]:
        """
        Activate a field mapping.

        Args:
            db: Database session
            id: FieldMapping ID

        Returns:
            Updated FieldMapping or None
        """
        obj = await self.get(db, id)
        if obj:
            obj.is_active = True
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
        return obj

    async def deactivate(self, db: AsyncSession, *, id: int) -> Optional[FieldMapping]:
        """
        Deactivate a field mapping.

        Args:
            db: Database session
            id: FieldMapping ID

        Returns:
            Updated FieldMapping or None
        """
        obj = await self.get(db, id)
        if obj:
            obj.is_active = False
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
        return obj

    async def reorder(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        mapping_orders: Dict[str, int],
    ) -> List[FieldMapping]:
        """
        Reorder field mappings for a template.

        Args:
            db: Database session
            template_id: Template ID
            mapping_orders: Dictionary mapping ID to new order

        Returns:
            List of updated FieldMapping instances
        """
        result = await db.execute(
            select(FieldMapping).where(FieldMapping.template_id == template_id)
        )
        mappings = list(result.scalars().all())

        updated = []
        for mapping in mappings:
            if mapping.id in mapping_orders:
                mapping.field_order = mapping_orders[mapping.id]
                db.add(mapping)
                updated.append(mapping)

        await db.flush()
        for obj in updated:
            await db.refresh(obj)

        return updated

    def validate_mapping(self, mapping: FieldMapping) -> ValidationResult:
        """
        Validate a field mapping configuration.

        Args:
            mapping: FieldMapping instance to validate

        Returns:
            ValidationResult with is_valid and errors
        """
        errors = []

        # Check required fields
        if not mapping.source_field:
            errors.append("Source field is required")

        if not mapping.target_field:
            errors.append("Target field is required")

        # Validate mapping type specific configurations
        if mapping.mapping_type == FieldMappingType.LOOKUP and not mapping.mapping_config:
            errors.append("LOOKUP mapping type requires mapping_config")

        if mapping.mapping_type == FieldMappingType.COMPUTED and not mapping.transform_script:
            errors.append("COMPUTED mapping type requires transform_script")

        if mapping.mapping_type == FieldMappingType.FIXED and not mapping.default_value:
            errors.append("FIXED mapping type requires default_value")

        # Validate target field length if specified
        if mapping.target_field_max_length is not None:
            if mapping.target_field_max_length <= 0:
                errors.append("Target field max length must be positive")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class FieldMappingService:
    """
    Service class for field mapping operations.
    Wraps CRUDFieldMapping with additional business logic.
    """

    def __init__(self):
        self.crud = CRUDFieldMapping(FieldMapping)

    async def get_mappings_by_template(
        self,
        db: AsyncSession,
        template_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FieldMapping]:
        """
        Get all mappings for a template.

        Args:
            db: Database session
            template_id: Template ID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of FieldMapping instances
        """
        return await self.crud.get_by_template(db, template_id=template_id, skip=skip, limit=limit)

    async def get_active_mappings(
        self,
        db: AsyncSession,
        *,
        template_id: Optional[str] = None,
    ) -> List[FieldMapping]:
        """
        Get all active mappings.

        Args:
            db: Database session
            template_id: Optional template ID to filter by

        Returns:
            List of active FieldMapping instances
        """
        return await self.crud.get_active_mappings(db, template_id=template_id)

    async def validate_mapping(self, db: AsyncSession, mapping_id: int) -> ValidationResult:
        """
        Validate a field mapping by ID.

        Args:
            db: Database session
            mapping_id: FieldMapping ID

        Returns:
            ValidationResult with validation status and errors
        """
        mapping = await self.crud.get(db, mapping_id)
        if not mapping:
            return ValidationResult(is_valid=False, errors=[f"Mapping with ID {mapping_id} not found"])

        return self.crud.validate_mapping(mapping)

    async def validate_mapping_direct(self, mapping_data: FieldMappingCreate) -> ValidationResult:
        """
        Validate a field mapping directly from data.

        Args:
            mapping_data: FieldMappingCreate schema

        Returns:
            ValidationResult with validation status and errors
        """
        mapping = FieldMapping(**mapping_data.model_dump())
        return self.crud.validate_mapping(mapping)


# Global instance
field_mapping_service = FieldMappingService()


# Keep CRUDFieldMapping accessible for direct use
field_mapping = CRUDFieldMapping(FieldMapping)
