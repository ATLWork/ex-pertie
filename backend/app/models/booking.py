"""
Booking hotel and room database models.
These models store hotel/room data imported from Booking.com.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class BookingSource(str, enum.Enum):
    """Booking data source enum."""

    BOOKING_COM = "booking_com"  # Booking.com
    CTRIP = "ctrip"  # Ctrip
    EXPEDIA = "expedia"  # Expedia
    OTHER = "other"  # Other sources


class BookingHotel(BaseModel):
    """
    Booking hotel model.
    Stores hotel basic information imported from Booking.com.
    """

    __tablename__ = "booking_hotels"

    # Basic Info
    source: Mapped[BookingSource] = mapped_column(
        Enum(BookingSource), nullable=False, default=BookingSource.BOOKING_COM, comment="Data source"
    )
    source_hotel_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Hotel ID in source system"
    )
    name_cn: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Hotel name in Chinese"
    )
    name_en: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Hotel name in English"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Display name"
    )

    # Brand and Chain
    brand: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Hotel brand"
    )
    chain_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Hotel chain name"
    )

    # Star Rating
    star_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Star rating (e.g., 3.5, 4.0, 5.0)"
    )

    # Location Info
    country_code: Mapped[str] = mapped_column(
        String(10), nullable=False, default="CN", comment="Country code (ISO 3166-1)"
    )
    country_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Country name"
    )
    province: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Province/State"
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="City"
    )
    city_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="City ID in source system"
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="District/County"
    )
    address: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Street address"
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Postal code"
    )

    # Geolocation
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Latitude"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Longitude"
    )

    # Contact Info
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Phone number"
    )
    fax: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Fax number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Email address"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Website URL"
    )

    # Hotel Features
    check_in_time: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Check-in time (e.g., 14:00)"
    )
    check_out_time: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Check-out time (e.g., 12:00)"
    )
    built_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Year hotel was built"
    )
    renovated_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Last renovation year"
    )
    floor_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of floors"
    )
    room_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Total number of rooms"
    )

    # URL
    booking_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL on Booking.com"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether hotel is active"
    )

    # Mapping to internal hotel
    internal_hotel_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("hotels.id", ondelete="SET NULL"), nullable=True, index=True, comment="Mapped internal hotel ID"
    )

    # Relationships
    rooms: Mapped[List["BookingRoom"]] = relationship(
        "BookingRoom", back_populates="hotel", cascade="all, delete-orphan"
    )
    extension: Mapped[Optional["BookingHotelExtension"]] = relationship(
        "BookingHotelExtension", back_populates="hotel", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<BookingHotel {self.name_en}>"


class BookingHotelExtension(BaseModel):
    """
    Booking hotel extension model.
    Stores additional hotel details like policies, services, facilities, etc.
    """

    __tablename__ = "booking_hotel_extensions"

    # Reference to hotel
    hotel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("booking_hotels.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Hotel Description
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel description"
    )
    description_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel description in Chinese"
    )

    # Policies
    cancellation_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cancellation policy"
    )
    cancellation_policy_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cancellation policy in Chinese"
    )
    prepayment_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Prepayment policy"
    )
    prepayment_policy_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Prepayment policy in Chinese"
    )
    kid_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Child policy"
    )
    pet_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Pet policy"
    )

    # Services
    services: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel services (comma separated)"
    )
    services_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel services in Chinese"
    )
    service_details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Service details in JSON format"
    )

    # Facilities
    facilities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel facilities (comma separated)"
    )
    facilities_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel facilities in Chinese"
    )
    facility_details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Facility details in JSON format"
    )

    # Room Facilities
    room_facilities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room facilities (comma separated)"
    )
    room_facilities_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room facilities in Chinese"
    )

    # Photos
    photo_urls: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Hotel photo URLs in JSON format"
    )
    cover_photo_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Cover photo URL"
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Thumbnail photo URL"
    )

    # Reviews Summary
    review_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Review score (e.g., 8.5)"
    )
    review_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Total review count"
    )
    review_score_breakdown: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Review score breakdown in JSON format"
    )

    # Awards/Certifications
    awards: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Awards and certifications"
    )

    # Nearby Attractions
    nearby_attractions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Nearby attractions in JSON format"
    )

    # Important Notes
    important_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Important notes for guests"
    )

    # Relationships
    hotel: Mapped["BookingHotel"] = relationship("BookingHotel", back_populates="extension")

    def __repr__(self) -> str:
        return f"<BookingHotelExtension hotel_id={self.hotel_id}>"


class BookingRoom(BaseModel):
    """
    Booking room model.
    Stores room type information imported from Booking.com.
    """

    __tablename__ = "booking_rooms"

    # Reference to hotel
    hotel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("booking_hotels.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Basic Info
    source: Mapped[BookingSource] = mapped_column(
        Enum(BookingSource), nullable=False, default=BookingSource.BOOKING_COM, comment="Data source"
    )
    source_room_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Room ID in source system"
    )
    room_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Room name on Booking.com"
    )
    room_name_cn: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Room name in Chinese"
    )
    room_type_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Room type code"
    )

    # Room Configuration
    room_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Room type category"
    )
    bed_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Bed type (e.g., King, Twin, Queen)"
    )
    bed_configuration: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Bed configuration details"
    )
    max_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, comment="Maximum occupancy"
    )
    standard_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, comment="Standard occupancy"
    )
    extra_bed_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Extra bed count available"
    )
    room_size: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Room size in square meters"
    )
    floor: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Floor information"
    )

    # Room View
    view_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="View type (e.g., City, Sea, Garden)"
    )
    window_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Window type (e.g., Window, No Window)"
    )

    # Amenities
    amenities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room amenities (comma separated)"
    )
    amenities_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room amenities in Chinese"
    )
    amenity_details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Amenity details in JSON format"
    )

    # Bathroom
    bathroom_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Bathroom type (e.g., Shared, Private, Ensuite)"
    )
    bathroom_amenities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Bathroom amenities"
    )
    bathroom_amenities_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Bathroom amenities in Chinese"
    )

    # Media
    photo_urls: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room photo URLs in JSON format"
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Thumbnail photo URL"
    )

    # Smoking Policy
    smoking_policy: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Smoking policy (smoking/non-smoking)"
    )

    # Booking URL
    booking_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL on Booking.com"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether room is active"
    )

    # Mapping to internal room
    internal_room_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True, comment="Mapped internal room ID"
    )

    # Relationships
    hotel: Mapped["BookingHotel"] = relationship("BookingHotel", back_populates="rooms")
    extension: Mapped[Optional["BookingRoomExtension"]] = relationship(
        "BookingRoomExtension", back_populates="room", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<BookingRoom {self.room_name}>"


class BookingRoomExtension(BaseModel):
    """
    Booking room extension model.
    Stores additional room details like policies, facilities, etc.
    """

    __tablename__ = "booking_room_extensions"

    # Reference to room
    room_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("booking_rooms.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Room Description
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room description"
    )
    description_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Room description in Chinese"
    )

    # Policies
    cancellation_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cancellation policy"
    )
    cancellation_policy_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cancellation policy in Chinese"
    )
    prepayment_policy: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Prepayment policy"
    )
    prepayment_policy_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Prepayment policy in Chinese"
    )

    # Accessibility
    accessibility_features: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Accessibility features in JSON format"
    )

    # Additional Information
    additional_info: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional room information"
    )
    additional_info_cn: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional room information in Chinese"
    )

    # Important Notes
    important_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Important notes for this room"
    )

    # Relationships
    room: Mapped["BookingRoom"] = relationship("BookingRoom", back_populates="extension")

    def __repr__(self) -> str:
        return f"<BookingRoomExtension room_id={self.room_id}>"