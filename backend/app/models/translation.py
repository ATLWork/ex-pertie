"""
Translation related database models.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RuleType(str, enum.Enum):
    """Translation rule type enum."""

    DIRECT = "direct"  # Direct mapping
    GLOSSARY = "glossary"  # Use glossary
    AI = "ai"  # AI translation


class ReferenceSource(str, enum.Enum):
    """Translation reference source enum."""

    MANUAL = "manual"  # Manually added
    IMPORTED = "imported"  # Imported from external
    AI = "ai"  # AI generated


class GlossaryCategory(str, enum.Enum):
    """Glossary category enum."""

    HOTEL = "hotel"  # Hotel related terms
    ROOM = "room"  # Room related terms
    AMENITY = "amenity"  # Amenity related terms
    GENERAL = "general"  # General terms


class TranslationType(str, enum.Enum):
    """Translation type enum."""

    MACHINE = "machine"  # Machine translation
    AI = "ai"  # AI translation
    HYBRID = "hybrid"  # Hybrid translation


class TranslationRule(Base):
    """
    Translation rule model.
    Defines rules for translating specific fields.
    """

    __tablename__ = "translation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Rule name")
    source_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Source language code (e.g., zh-CN)"
    )
    target_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Target language code (e.g., en-US)"
    )
    field_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Field name to apply rule"
    )
    rule_type: Mapped[RuleType] = mapped_column(
        Enum(RuleType), nullable=False, default=RuleType.AI, comment="Rule type"
    )
    rule_value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Rule value/mapping JSON"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Whether rule is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<TranslationRule {self.name}>"


class TranslationReference(Base):
    """
    Translation reference library model.
    Stores historical translations for reuse.
    """

    __tablename__ = "translation_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Original text"
    )
    translated_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Translated text"
    )
    source_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Source language code"
    )
    target_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Target language code"
    )
    context: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Context information"
    )
    confidence: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False, comment="Confidence score (0-1)"
    )
    source: Mapped[ReferenceSource] = mapped_column(
        Enum(ReferenceSource), nullable=False, default=ReferenceSource.MANUAL, comment="Reference source"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<TranslationReference {self.id}: {self.source_text[:30]}...>"


class Glossary(Base):
    """
    Glossary model.
    Stores standardized term translations.
    """

    __tablename__ = "glossaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Term in source language"
    )
    translation: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Standard translation"
    )
    source_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Source language code"
    )
    target_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Target language code"
    )
    category: Mapped[GlossaryCategory] = mapped_column(
        Enum(GlossaryCategory), nullable=False, default=GlossaryCategory.GENERAL, comment="Term category"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional notes"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Whether term is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Glossary {self.term}: {self.translation}>"


class TranslationHistory(Base):
    """
    Translation history model.
    Records all translation operations for audit and improvement.
    """

    __tablename__ = "translation_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Original text"
    )
    translated_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Translated text"
    )
    source_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Source language code"
    )
    target_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Target language code"
    )
    translation_type: Mapped[TranslationType] = mapped_column(
        Enum(TranslationType), nullable=False, comment="Translation type"
    )
    reference_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Whether reference library was used"
    )
    glossary_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Whether glossary was used"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Confidence score (0-1)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<TranslationHistory {self.id}: {self.source_text[:30]}...>"
