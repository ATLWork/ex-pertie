"""
Expedia template and field mapping models.
"""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TemplateType(str, enum.Enum):
    """Template type enum."""

    HOTEL = "hotel"  # Hotel template
    ROOM = "room"  # Room template
    RATE = "rate"  # Rate template
    INVENTORY = "inventory"  # Inventory template


class TemplateStatus(str, enum.Enum):
    """Template status enum."""

    DRAFT = "draft"  # Draft
    ACTIVE = "active"  # Active
    DEPRECATED = "deprecated"  # Deprecated
    ARCHIVED = "archived"  # Archived


class FieldMappingType(str, enum.Enum):
    """Field mapping type enum."""

    DIRECT = "direct"  # Direct mapping
    TRANSFORM = "transform"  # Transform required
    LOOKUP = "lookup"  # Lookup from dictionary
    COMPUTED = "computed"  # Computed value
    FIXED = "fixed"  # Fixed value
    NULL = "null"  # Always null


class ExpediaTemplate(BaseModel):
    """
    Expedia template model.
    Defines template configurations for Expedia data exports.
    """

    __tablename__ = "expedia_templates"

    # Template info
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Template name"
    )
    code: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True, comment="Template code"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Template description"
    )
    template_type: Mapped[TemplateType] = mapped_column(
        Enum(TemplateType), nullable=False, comment="Template type"
    )
    status: Mapped[TemplateStatus] = mapped_column(
        Enum(TemplateStatus), nullable=False, default=TemplateStatus.DRAFT, comment="Template status"
    )

    # Version info
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1.0", comment="Template version"
    )
    parent_template_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="Parent template ID for versioning"
    )

    # Expedia specific
    expedia_template_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Expedia official template name"
    )
    expedia_template_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Expedia template ID"
    )
    expedia_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Expedia template version"
    )

    # Template content
    header_row: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Header row number in Excel"
    )
    data_start_row: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, comment="Data start row number"
    )
    sheet_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Sheet name in Excel"
    )

    # Configuration
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Template configuration in JSON format"
    )
    sample_file_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Sample file path"
    )

    # Relationships
    field_mappings: Mapped[List["FieldMapping"]] = relationship(
        "FieldMapping", back_populates="template", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ExpediaTemplate {self.code} v{self.version}>"


class FieldMapping(BaseModel):
    """
    Field mapping model.
    Defines how internal fields map to Expedia fields.
    """

    __tablename__ = "field_mappings"

    # Reference
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("expedia_templates.id", ondelete="CASCADE"), nullable=False, index=True, comment="Template ID"
    )
    field_order: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Field order in export"
    )

    # Source field (internal)
    source_field: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Source field name"
    )
    source_field_cn: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Source field Chinese name"
    )
    source_field_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="string", comment="Source field type"
    )
    source_model: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Hotel", comment="Source model name"
    )

    # Target field (Expedia)
    target_field: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Target field name in Expedia"
    )
    target_field_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether field is required"
    )
    target_field_max_length: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Max length for target field"
    )

    # Mapping configuration
    mapping_type: Mapped[FieldMappingType] = mapped_column(
        Enum(FieldMappingType), nullable=False, default=FieldMappingType.DIRECT, comment="Mapping type"
    )
    mapping_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Mapping configuration in JSON format"
    )

    # Validation
    validation_rule: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Validation rule in JSON format"
    )
    default_value: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Default value if source is null"
    )
    transform_script: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Transform script (Python)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether mapping is active"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether field is visible in UI"
    )

    # Notes
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Field description"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional notes"
    )

    # Relationships
    template: Mapped["ExpediaTemplate"] = relationship(
        "ExpediaTemplate", back_populates="field_mappings"
    )

    def __repr__(self) -> str:
        return f"<FieldMapping {self.source_field} -> {self.target_field}>"
