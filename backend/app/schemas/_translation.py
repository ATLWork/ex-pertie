"""
Pydantic schemas for translation related APIs.
"""

import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.translation import (
    GlossaryCategory,
    ReferenceSource,
    RuleType,
    TranslationType,
)


class TranslationSource(str, enum.Enum):
    """Translation source type."""

    MACHINE = "machine"  # Machine translation only
    AI_ENHANCED = "ai_enhanced"  # Machine + AI enhancement
    CACHE = "cache"  # From cache


class TranslationStatus(str, enum.Enum):
    """Translation task status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== Translation Rule Schemas ==============


class TranslationRuleBase(BaseModel):
    """Base schema for translation rule."""

    name: str = Field(..., max_length=100, description="Rule name")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    field_name: str = Field(..., max_length=100, description="Field name to apply rule")
    rule_type: RuleType = Field(default=RuleType.AI, description="Rule type")
    rule_value: str = Field(..., description="Rule value/mapping JSON")
    is_active: bool = Field(default=True, description="Whether rule is active")


class TranslationRuleCreate(TranslationRuleBase):
    """Schema for creating translation rule."""

    pass


class TranslationRuleUpdate(BaseModel):
    """Schema for updating translation rule."""

    name: Optional[str] = Field(None, max_length=100, description="Rule name")
    source_lang: Optional[str] = Field(None, max_length=10, description="Source language code")
    target_lang: Optional[str] = Field(None, max_length=10, description="Target language code")
    field_name: Optional[str] = Field(None, max_length=100, description="Field name to apply rule")
    rule_type: Optional[RuleType] = Field(None, description="Rule type")
    rule_value: Optional[str] = Field(None, description="Rule value/mapping JSON")
    is_active: Optional[bool] = Field(None, description="Whether rule is active")


class TranslationRuleResponse(TranslationRuleBase):
    """Schema for translation rule response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Rule ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


# ============== Translation Reference Schemas ==============


class TranslationReferenceBase(BaseModel):
    """Base schema for translation reference."""

    source_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    context: Optional[str] = Field(None, description="Context information")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    source: ReferenceSource = Field(default=ReferenceSource.MANUAL, description="Reference source")


class TranslationReferenceCreate(TranslationReferenceBase):
    """Schema for creating translation reference."""

    pass


class TranslationReferenceUpdate(BaseModel):
    """Schema for updating translation reference."""

    source_text: Optional[str] = Field(None, description="Original text")
    translated_text: Optional[str] = Field(None, description="Translated text")
    source_lang: Optional[str] = Field(None, max_length=10, description="Source language code")
    target_lang: Optional[str] = Field(None, max_length=10, description="Target language code")
    context: Optional[str] = Field(None, description="Context information")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0-1)")
    source: Optional[ReferenceSource] = Field(None, description="Reference source")


class TranslationReferenceResponse(TranslationReferenceBase):
    """Schema for translation reference response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Reference ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


# ============== Glossary Schemas ==============


class GlossaryBase(BaseModel):
    """Base schema for glossary."""

    term: str = Field(..., max_length=255, description="Term in source language")
    translation: str = Field(..., max_length=255, description="Standard translation")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    category: GlossaryCategory = Field(default=GlossaryCategory.GENERAL, description="Term category")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: bool = Field(default=True, description="Whether term is active")


class GlossaryCreate(GlossaryBase):
    """Schema for creating glossary."""

    pass


class GlossaryUpdate(BaseModel):
    """Schema for updating glossary."""

    term: Optional[str] = Field(None, max_length=255, description="Term in source language")
    translation: Optional[str] = Field(None, max_length=255, description="Standard translation")
    source_lang: Optional[str] = Field(None, max_length=10, description="Source language code")
    target_lang: Optional[str] = Field(None, max_length=10, description="Target language code")
    category: Optional[GlossaryCategory] = Field(None, description="Term category")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: Optional[bool] = Field(None, description="Whether term is active")


class GlossaryResponse(GlossaryBase):
    """Schema for glossary response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Glossary ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


# ============== Translation History Schemas ==============


class TranslationHistoryBase(BaseModel):
    """Base schema for translation history."""

    source_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    translation_type: TranslationType = Field(..., description="Translation type")
    reference_used: bool = Field(default=False, description="Whether reference library was used")
    glossary_used: bool = Field(default=False, description="Whether glossary was used")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0-1)")


class TranslationHistoryCreate(TranslationHistoryBase):
    """Schema for creating translation history."""

    pass


class TranslationHistoryResponse(TranslationHistoryBase):
    """Schema for translation history response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="History ID")
    created_at: datetime = Field(..., description="Created at")


# ============== Bulk Operations Schemas ==============


class GlossaryBulkCreate(BaseModel):
    """Schema for bulk creating glossaries."""

    items: List[GlossaryCreate] = Field(..., description="List of glossary items to create")


class TranslationReferenceBulkCreate(BaseModel):
    """Schema for bulk creating translation references."""

    items: List[TranslationReferenceCreate] = Field(..., description="List of reference items to create")


# ============== Query Schemas ==============


class TranslationRuleQuery(BaseModel):
    """Query parameters for translation rules."""

    source_lang: Optional[str] = Field(None, description="Filter by source language")
    target_lang: Optional[str] = Field(None, description="Filter by target language")
    field_name: Optional[str] = Field(None, description="Filter by field name")
    rule_type: Optional[RuleType] = Field(None, description="Filter by rule type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


class TranslationReferenceQuery(BaseModel):
    """Query parameters for translation references."""

    source_lang: Optional[str] = Field(None, description="Filter by source language")
    target_lang: Optional[str] = Field(None, description="Filter by target language")
    source: Optional[ReferenceSource] = Field(None, description="Filter by source")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")


class GlossaryQuery(BaseModel):
    """Query parameters for glossaries."""

    source_lang: Optional[str] = Field(None, description="Filter by source language")
    target_lang: Optional[str] = Field(None, description="Filter by target language")
    category: Optional[GlossaryCategory] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search term")
