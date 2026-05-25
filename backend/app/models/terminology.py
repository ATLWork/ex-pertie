"""
Terminology database models.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TerminologyCategory(str, enum.Enum):
    """Terminology category enum."""

    HOTEL = "hotel"  # Hotel related terms
    ROOM = "room"  # Room related terms
    AMENITY = "amenity"  # Amenity related terms
    GENERAL = "general"  # General terms


class Terminology(Base):
    """
    Terminology model.
    Stores terminology entries with source and target language translations.
    """

    __tablename__ = "terminologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Terminology entry name"
    )
    source_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Original/source text"
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
    domain: Mapped[TerminologyCategory] = mapped_column(
        Enum(TerminologyCategory),
        nullable=False,
        default=TerminologyCategory.GENERAL,
        comment="Domain category",
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
        return f"<Terminology {self.name}: {self.translated_text}>"