"""
Hotel and Room related database models.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.room import Room


class HotelBrand(str, enum.Enum):
    """Hotel brand enum."""

    ATour = "atour"  # 亚朵
    ATourX = "atour_x"  # 亚朵X
    ZHotel = "zhotel"  # ZHotel
    Ahaus = "ahaus"  # Ahaus


class HotelStatus(str, enum.Enum):
    """Hotel status enum."""

    DRAFT = "draft"  # 草稿
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"  # 已审核
    PUBLISHED = "published"  # 已上线
    SUSPENDED = "suspended"  # 已下线


class Hotel(BaseModel):
    """
    Hotel base model.
    Stores core hotel information.
    """

    __tablename__ = "hotels"

    # Basic Info
    name_cn: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Hotel name in Chinese"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Hotel name in English"
    )
    brand: Mapped[HotelBrand] = mapped_column(
        Enum(HotelBrand), nullable=False, default=HotelBrand.ATour, comment="Hotel brand"
    )
    status: Mapped[HotelStatus] = mapped_column(
        Enum(HotelStatus), nullable=False, default=HotelStatus.DRAFT, comment="Hotel status"
    )

    # Location Info
    country_code: Mapped[str] = mapped_column(
        String(10), nullable=False, default="CN", comment="Country code (ISO 3166-1)"
    )
    province: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Province/State"
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="City"
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="District/County"
    )
    address_cn: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Address in Chinese"
    )
    address_en: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Address in English"
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Postal code"
    )

    # Contact Info
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Phone number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Email address"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Website URL"
    )

    # Geolocation
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Latitude"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Longitude"
    )

    # Expedia specific
    expedia_hotel_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True, comment="Expedia Hotel ID"
    )
    expedia_chain_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Expedia Chain Code"
    )
    expedia_property_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Expedia Property Code"
    )

    # Timestamps
    opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Hotel opening date"
    )
    renovated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last renovation date"
    )

    # Relationships
    rooms: Mapped[List["Room"]] = relationship(
        "Room", back_populates="hotel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Hotel {self.name_cn}>"

    @property
    def display_name(self) -> str:
        """Return English name if available, otherwise Chinese name."""
        return self.name_en or self.name_cn


class Room(BaseModel):
    """
    Room base model.
    Stores core room type information.
    """

    __tablename__ = "rooms"

    # Basic Info
    hotel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_type_code: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Room type code (internal)"
    )
    name_cn: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Room name in Chinese"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Room name in English"
    )
    description_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room description in Chinese"
    )
    description_en: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room description in English"
    )

    # Room Configuration
    bed_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Bed type (e.g., King, Twin, Queen)"
    )
    max_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, comment="Maximum occupancy"
    )
    standard_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, comment="Standard occupancy"
    )
    room_size: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Room size in square meters"
    )
    floor_range: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Floor range (e.g., 3-5)"
    )
    total_rooms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Total number of rooms of this type"
    )

    # Expedia specific
    expedia_room_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True, comment="Expedia Room ID"
    )
    expedia_room_type_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Expedia Room Type Code"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether room type is active"
    )

    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="rooms")

    def __repr__(self) -> str:
        return f"<Room {self.name_cn}>"

    @property
    def display_name(self) -> str:
        """Return English name if available, otherwise Chinese name."""
        return self.name_en or self.name_cn
