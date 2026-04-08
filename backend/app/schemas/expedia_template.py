"""
Pydantic schemas for Expedia template and field mapping APIs.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.expedia_template import TemplateStatus, TemplateType, FieldMappingType


class FieldMappingBase(BaseModel):
    """Base schema for FieldMapping."""

    # Reference
    template_id: str = Field(..., description="Template ID")
    field_order: int = Field(..., description="Field order in export")

    # Source field (internal)
    source_field: str = Field(..., max_length=100, description="Source field name")
    source_field_cn: Optional[str] = Field(None, max_length=100, description="Source field Chinese name")
    source_field_type: str = Field(default="string", max_length=50, description="Source field type")
    source_model: str = Field(default="Hotel", max_length=50, description="Source model name")

    # Target field (Expedia)
    target_field: str = Field(..., max_length=100, description="Target field name in Expedia")
    target_field_required: bool = Field(default=False, description="Whether field is required")
    target_field_max_length: Optional[int] = Field(None, description="Max length for target field")

    # Mapping configuration
    mapping_type: FieldMappingType = Field(default=FieldMappingType.DIRECT, description="Mapping type")
    mapping_config: Optional[str] = Field(None, description="Mapping configuration in JSON format")

    # Validation
    validation_rule: Optional[str] = Field(None, description="Validation rule in JSON format")
    default_value: Optional[str] = Field(None, max_length=255, description="Default value if source is null")
    transform_script: Optional[str] = Field(None, description="Transform script (Python)")

    # Status
    is_active: bool = Field(default=True, description="Whether mapping is active")
    is_visible: bool = Field(default=True, description="Whether field is visible in UI")

    # Notes
    description: Optional[str] = Field(None, description="Field description")
    notes: Optional[str] = Field(None, description="Additional notes")


class FieldMappingCreate(FieldMappingBase):
    """Schema for creating a field mapping."""

    pass


class FieldMappingUpdate(BaseModel):
    """Schema for updating a field mapping."""

    # Reference
    field_order: Optional[int] = Field(None, description="Field order in export")

    # Source field (internal)
    source_field: Optional[str] = Field(None, max_length=100, description="Source field name")
    source_field_cn: Optional[str] = Field(None, max_length=100, description="Source field Chinese name")
    source_field_type: Optional[str] = Field(None, max_length=50, description="Source field type")
    source_model: Optional[str] = Field(None, max_length=50, description="Source model name")

    # Target field (Expedia)
    target_field: Optional[str] = Field(None, max_length=100, description="Target field name in Expedia")
    target_field_required: Optional[bool] = Field(None, description="Whether field is required")
    target_field_max_length: Optional[int] = Field(None, description="Max length for target field")

    # Mapping configuration
    mapping_type: Optional[FieldMappingType] = Field(None, description="Mapping type")
    mapping_config: Optional[str] = Field(None, description="Mapping configuration in JSON format")

    # Validation
    validation_rule: Optional[str] = Field(None, description="Validation rule in JSON format")
    default_value: Optional[str] = Field(None, max_length=255, description="Default value if source is null")
    transform_script: Optional[str] = Field(None, description="Transform script (Python)")

    # Status
    is_active: Optional[bool] = Field(None, description="Whether mapping is active")
    is_visible: Optional[bool] = Field(None, description="Whether field is visible in UI")

    # Notes
    description: Optional[str] = Field(None, description="Field description")
    notes: Optional[str] = Field(None, description="Additional notes")


class FieldMappingResponse(FieldMappingBase):
    """Schema for field mapping response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Field mapping ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class FieldMappingQuery(BaseModel):
    """Query parameters for field mappings."""

    template_id: Optional[str] = Field(None, description="Filter by template ID")
    source_field: Optional[str] = Field(None, description="Filter by source field")
    target_field: Optional[str] = Field(None, description="Filter by target field")
    mapping_type: Optional[FieldMappingType] = Field(None, description="Filter by mapping type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_visible: Optional[bool] = Field(None, description="Filter by visibility")
    search: Optional[str] = Field(None, description="Search in source/target field")


class FieldMappingBulkCreate(BaseModel):
    """Schema for bulk creating field mappings."""

    items: List[FieldMappingCreate] = Field(..., description="List of field mappings to create")


class ExpediaTemplateBase(BaseModel):
    """Base schema for ExpediaTemplate."""

    # Template info
    name: str = Field(..., max_length=255, description="Template name")
    code: str = Field(..., max_length=100, description="Template code")
    description: Optional[str] = Field(None, description="Template description")
    template_type: TemplateType = Field(..., description="Template type")
    status: TemplateStatus = Field(default=TemplateStatus.DRAFT, description="Template status")

    # Version info
    version: str = Field(default="1.0", max_length=50, description="Template version")
    parent_template_id: Optional[str] = Field(None, description="Parent template ID for versioning")

    # Expedia specific
    expedia_template_name: Optional[str] = Field(None, max_length=255, description="Expedia official template name")
    expedia_template_id: Optional[str] = Field(None, max_length=100, description="Expedia template ID")
    expedia_version: Optional[str] = Field(None, max_length=50, description="Expedia template version")

    # Template content
    header_row: int = Field(default=1, ge=1, description="Header row number in Excel")
    data_start_row: int = Field(default=2, ge=1, description="Data start row number")
    sheet_name: Optional[str] = Field(None, max_length=100, description="Sheet name in Excel")

    # Configuration
    config: Optional[str] = Field(None, description="Template configuration in JSON format")
    sample_file_path: Optional[str] = Field(None, max_length=500, description="Sample file path")


class ExpediaTemplateCreate(ExpediaTemplateBase):
    """Schema for creating an Expedia template."""

    pass


class ExpediaTemplateUpdate(BaseModel):
    """Schema for updating an Expedia template."""

    # Template info
    name: Optional[str] = Field(None, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    status: Optional[TemplateStatus] = Field(None, description="Template status")

    # Version info
    version: Optional[str] = Field(None, max_length=50, description="Template version")
    parent_template_id: Optional[str] = Field(None, description="Parent template ID for versioning")

    # Expedia specific
    expedia_template_name: Optional[str] = Field(None, max_length=255, description="Expedia official template name")
    expedia_template_id: Optional[str] = Field(None, max_length=100, description="Expedia template ID")
    expedia_version: Optional[str] = Field(None, max_length=50, description="Expedia template version")

    # Template content
    header_row: Optional[int] = Field(None, ge=1, description="Header row number in Excel")
    data_start_row: Optional[int] = Field(None, ge=1, description="Data start row number")
    sheet_name: Optional[str] = Field(None, max_length=100, description="Sheet name in Excel")

    # Configuration
    config: Optional[str] = Field(None, description="Template configuration in JSON format")
    sample_file_path: Optional[str] = Field(None, max_length=500, description="Sample file path")


class ExpediaTemplateResponse(ExpediaTemplateBase):
    """Schema for Expedia template response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Template ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class ExpediaTemplateWithMappings(ExpediaTemplateResponse):
    """Schema for Expedia template response with field mappings."""

    field_mappings: List[FieldMappingResponse] = Field(default=[], description="Field mappings")


class ExpediaTemplateQuery(BaseModel):
    """Query parameters for Expedia templates."""

    name: Optional[str] = Field(None, description="Search by template name")
    code: Optional[str] = Field(None, description="Filter by template code")
    template_type: Optional[TemplateType] = Field(None, description="Filter by template type")
    status: Optional[TemplateStatus] = Field(None, description="Filter by status")
    is_active: Optional[bool] = Field(None, description="Filter by active status (via status=ACTIVE)")
    search: Optional[str] = Field(None, description="Search in name/code")
