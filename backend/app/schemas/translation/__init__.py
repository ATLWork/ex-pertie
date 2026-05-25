"""
Translation module schemas.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.terminology import TerminologyCategory


class TranslationSource(str, Enum):
    """Translation source type."""

    MACHINE = "machine"  # Machine translation only
    AI_ENHANCED = "ai_enhanced"  # Machine + AI enhancement
    CACHE = "cache"  # From cache


class TranslationStatus(str, Enum):
    """Translation task status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslateRequest(BaseModel):
    """Single translation request."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    source_lang: str = Field(default="zh", description="Source language code")
    target_lang: str = Field(default="en", description="Target language code")
    use_cache: bool = Field(default=True, description="Whether to use cache")
    use_ai_enhance: bool = Field(default=True, description="Whether to use AI enhancement")
    context: Optional[str] = Field(
        default=None, max_length=500, description="Additional context for translation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "豪华大床房",
                    "source_lang": "zh",
                    "target_lang": "en",
                    "use_cache": True,
                    "use_ai_enhance": True,
                    "context": "hotel room type",
                }
            ]
        }
    }


class BatchTranslateRequest(BaseModel):
    """Batch translation request."""

    texts: List[str] = Field(
        ..., min_length=1, max_length=100, description="List of texts to translate"
    )
    source_lang: str = Field(default="zh", description="Source language code")
    target_lang: str = Field(default="en", description="Target language code")
    use_cache: bool = Field(default=True, description="Whether to use cache")
    use_ai_enhance: bool = Field(default=True, description="Whether to use AI enhancement")


class TranslationResult(BaseModel):
    """Single translation result."""

    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    source: TranslationSource = Field(..., description="Translation source")
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Confidence score")
    cached: bool = Field(default=False, description="Whether result is from cache")


class BatchTranslationResult(BaseModel):
    """Batch translation result."""

    results: List[TranslationResult] = Field(..., description="Translation results")
    total: int = Field(..., description="Total number of translations")
    cached_count: int = Field(default=0, description="Number of cached results")
    failed_count: int = Field(default=0, description="Number of failed translations")


class TranslationHistoryItem(BaseModel):
    """Translation history item."""

    id: int = Field(..., description="History record ID")
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language")
    target_lang: str = Field(..., description="Target language")
    source: TranslationSource = Field(..., description="Translation source")
    created_at: str = Field(..., description="Creation timestamp")


class TranslationHistoryResponse(BaseModel):
    """Translation history response."""

    items: List[TranslationHistoryItem] = Field(..., description="History items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class TerminologyMatch(BaseModel):
    """Terminology match result."""

    term: str = Field(..., description="Original term")
    translation: str = Field(..., description="Translated term")
    position: int = Field(..., description="Position in text")
    confidence: float = Field(..., ge=0, le=1, description="Match confidence")


class ReferenceMatch(BaseModel):
    """Reference library match result."""

    original: str = Field(..., description="Original reference text")
    translation: str = Field(..., description="Reference translation")
    similarity: float = Field(..., ge=0, le=1, description="Similarity score")


# Import enums from models
from app.models.translation import (
    GlossaryCategory,
    ReferenceSource,
    RuleType,
    TranslationType,
)
from app.models.terminology import TerminologyCategory


# Terminology Schemas
class TerminologyBase(BaseModel):
    """Base schema for terminology."""

    name: str = Field(..., max_length=255, description="Terminology entry name")
    source_text: str = Field(..., description="Original/source text")
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    domain: TerminologyCategory = Field(
        default=TerminologyCategory.GENERAL, description="Domain category"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: bool = Field(default=True, description="Whether term is active")


class TerminologyCreate(TerminologyBase):
    """Schema for creating terminology."""

    pass


class TerminologyUpdate(BaseModel):
    """Schema for updating terminology."""

    name: Optional[str] = Field(None, max_length=255, description="Terminology entry name")
    source_text: Optional[str] = Field(None, description="Original/source text")
    translated_text: Optional[str] = Field(None, description="Translated text")
    source_lang: Optional[str] = Field(None, max_length=10, description="Source language code")
    target_lang: Optional[str] = Field(None, max_length=10, description="Target language code")
    domain: Optional[TerminologyCategory] = Field(None, description="Domain category")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: Optional[bool] = Field(None, description="Whether term is active")


class TerminologyResponse(TerminologyBase):
    """Schema for terminology response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Terminology ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class TerminologyQuery(BaseModel):
    """Query parameters for terminology."""

    source_lang: Optional[str] = Field(None, description="Filter by source language")
    target_lang: Optional[str] = Field(None, description="Filter by target language")
    domain: Optional[TerminologyCategory] = Field(None, description="Filter by domain")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search term in name or source_text")

# Import schemas from main translation module
from app.schemas._translation import (
    TranslationRuleBase,
    TranslationRuleCreate,
    TranslationRuleUpdate,
    TranslationRuleResponse,
    TranslationRuleQuery,
    TranslationReferenceBase,
    TranslationReferenceCreate,
    TranslationReferenceUpdate,
    TranslationReferenceResponse,
    TranslationReferenceQuery,
    GlossaryBase,
    GlossaryCreate,
    GlossaryUpdate,
    GlossaryResponse,
    GlossaryQuery,
    GlossaryBulkCreate,
    TranslationHistoryBase,
    TranslationHistoryCreate,
    TranslationHistoryResponse,
    TranslationReferenceBulkCreate,
)

__all__ = [
    # Enums
    "TranslationSource",
    "TranslationStatus",
    "GlossaryCategory",
    "TerminologyCategory",
    "ReferenceSource",
    "RuleType",
    "TranslationType",
    # Request/Response
    "TranslateRequest",
    "BatchTranslateRequest",
    "TranslationResult",
    "BatchTranslationResult",
    "TranslationHistoryItem",
    "TranslationHistoryResponse",
    "TerminologyMatch",
    "ReferenceMatch",
    # Translation Rule Schemas
    "TranslationRuleBase",
    "TranslationRuleCreate",
    "TranslationRuleUpdate",
    "TranslationRuleResponse",
    "TranslationRuleQuery",
    # Translation Reference Schemas
    "TranslationReferenceBase",
    "TranslationReferenceCreate",
    "TranslationReferenceUpdate",
    "TranslationReferenceResponse",
    "TranslationReferenceQuery",
    # Glossary Schemas
    "GlossaryBase",
    "GlossaryCreate",
    "GlossaryUpdate",
    "GlossaryResponse",
    "GlossaryQuery",
    "GlossaryBulkCreate",
    # Translation History Schemas
    "TranslationHistoryBase",
    "TranslationHistoryCreate",
    "TranslationHistoryResponse",
    # Bulk Operations
    "TranslationReferenceBulkCreate",
    # Terminology Schemas
    "TerminologyBase",
    "TerminologyCreate",
    "TerminologyUpdate",
    "TerminologyResponse",
    "TerminologyQuery",
]
