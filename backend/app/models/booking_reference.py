"""
Booking Reference database model.
Stores booking reference translations with Ctrip and Booking.com sources.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BookingReference(Base):
    """
    Booking reference library model.
    Stores original text with reference translations from multiple sources
    (Ctrip, Booking.com) for hotel and accommodation related content.
    """

    __tablename__ = "booking_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Original text
    source_text: Mapped[str] = mapped_column(
        Text, nullable=False, index=True, comment="Original text in source language"
    )

    # Reference translations from different sources
    ctrip_translation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Translation from Ctrip"
    )
    booking_translation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Translation from Booking.com"
    )

    # Source and target languages
    source_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Source language code"
    )
    target_lang: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="Target language code"
    )

    # Hotel context
    hotel_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Associated hotel name"
    )
    hotel_address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Associated hotel address"
    )

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of times this reference was used"
    )

    # Active status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Whether reference is active"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<BookingReference {self.id}: {self.source_text[:30]}...>"