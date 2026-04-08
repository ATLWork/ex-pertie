"""
Room extension model for additional room details.
"""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class RoomExtension(BaseModel):
    """
    Room extension model.
    Stores additional room details like amenities, images, etc.
    """

    __tablename__ = "room_extensions"

    # Reference to room
    room_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Amenities
    amenities_cn: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Room amenities in Chinese (comma separated)"
    )
    amenities_en: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Room amenities in English (comma separated)"
    )
    amenity_details: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Detailed amenities in JSON format"
    )

    # Media
    image_urls: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Room image URLs in JSON format"
    )
    thumbnail_url: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="Thumbnail image URL"
    )

    # Physical Features
    view_type: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="View type (e.g., City, Sea, Garden)"
    )
    balcony: Mapped[bool] = mapped_column(
        Boolean, nullable=True, default=False, comment="Has balcony"
    )
    smoking_policy: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="Smoking policy (smoking/non-smoking)"
    )
    floor: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="Floor information"
    )

    # Bathroom
    bathroom_type: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="Bathroom type (e.g., Shared, Private, Ensuite)"
    )
    bathroom_amenities_cn: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Bathroom amenities in Chinese"
    )
    bathroom_amenities_en: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Bathroom amenities in English"
    )

    # Accessibility
    accessibility_features: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Accessibility features in JSON format"
    )

    # Relationships
    # room: Mapped["Room"] = relationship("Room", back_populates="extension")

    def __repr__(self) -> str:
        return f"<RoomExtension room_id={self.room_id}>"
