"""
Translation cache database model.
Stores cached translations for faster retrieval with TTL expiration.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Float, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TranslationCache(Base):
    """
    Translation cache model.
    Stores cached translation results with TTL-based expiration.
    """

    __tablename__ = "translation_cache"

    cache_key: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
        comment="Unique cache key (translation:{src}:{tgt}:{ai|mt}:{hash})",
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original source text",
    )
    source_lang: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Source language (e.g. zh)",
    )
    target_lang: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Target language (e.g. en)",
    )
    translated_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cached translated text",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="MACHINE/AI_ENHANCED/CACHE/N/A",
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0.0-1.0)",
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON metadata string",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="Creation time",
    )
    ttl_expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Expiry time",
    )

    __table_args__ = (
        Index("ix_translation_cache_lang_pair", "source_lang", "target_lang"),
    )

    def __repr__(self) -> str:
        return f"<TranslationCache {self.cache_key}>"
