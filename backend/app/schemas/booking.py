"""
Pydantic schemas for Booking.com hotel and room related APIs.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingSource


class BookingHotelBase(BaseModel):
    """Base schema for BookingHotel."""

    # Basic Info
    source: BookingSource = Field(default=BookingSource.BOOKING_COM, description="Data source")
    source_hotel_id: Optional[str] = Field(None, description="Hotel ID in source system")
    name_cn: Optional[str] = Field(None, description="Hotel name in Chinese")
    name_en: str = Field(..., description="Hotel name in English")
    display_name: Optional[str] = Field(None, description="Display name")

    # Brand and Chain
    brand: Optional[str] = Field(None, description="Hotel brand")
    chain_name: Optional[str] = Field(None, description="Hotel chain name")

    # Star Rating
    star_rating: Optional[float] = Field(None, description="Star rating")

    # Location Info
    country_code: str = Field(default="CN", description="Country code")
    country_name: Optional[str] = Field(None, description="Country name")
    province: Optional[str] = Field(None, description="Province/State")
    city: str = Field(..., description="City")
    city_id: Optional[str] = Field(None, description="City ID in source system")
    district: Optional[str] = Field(None, description="District/County")
    address: str = Field(..., description="Street address")
    postal_code: Optional[str] = Field(None, description="Postal code")

    # Geolocation
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")

    # Contact Info
    phone: Optional[str] = Field(None, description="Phone number")
    fax: Optional[str] = Field(None, description="Fax number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")

    # Hotel Features
    check_in_time: Optional[str] = Field(None, description="Check-in time")
    check_out_time: Optional[str] = Field(None, description="Check-out time")
    built_year: Optional[int] = Field(None, description="Year hotel was built")
    renovated_year: Optional[int] = Field(None, description="Last renovation year")
    floor_count: Optional[int] = Field(None, description="Number of floors")
    room_count: Optional[int] = Field(None, description="Total number of rooms")

    # URL
    booking_url: Optional[str] = Field(None, description="URL on Booking.com")

    # Status
    is_active: bool = Field(default=True, description="Whether hotel is active")


class BookingHotelCreate(BookingHotelBase):
    """Schema for creating a booking hotel."""
    pass


class BookingHotelUpdate(BaseModel):
    """Schema for updating a booking hotel."""

    # Basic Info
    source: Optional[BookingSource] = Field(None, description="Data source")
    source_hotel_id: Optional[str] = Field(None, description="Hotel ID in source system")
    name_cn: Optional[str] = Field(None, description="Hotel name in Chinese")
    name_en: Optional[str] = Field(None, description="Hotel name in English")
    display_name: Optional[str] = Field(None, description="Display name")

    # Brand and Chain
    brand: Optional[str] = Field(None, description="Hotel brand")
    chain_name: Optional[str] = Field(None, description="Hotel chain name")

    # Star Rating
    star_rating: Optional[float] = Field(None, description="Star rating")

    # Location Info
    country_code: Optional[str] = Field(None, description="Country code")
    country_name: Optional[str] = Field(None, description="Country name")
    province: Optional[str] = Field(None, description="Province/State")
    city: Optional[str] = Field(None, description="City")
    city_id: Optional[str] = Field(None, description="City ID in source system")
    district: Optional[str] = Field(None, description="District/County")
    address: Optional[str] = Field(None, description="Street address")
    postal_code: Optional[str] = Field(None, description="Postal code")

    # Geolocation
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")

    # Contact Info
    phone: Optional[str] = Field(None, description="Phone number")
    fax: Optional[str] = Field(None, description="Fax number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")

    # Hotel Features
    check_in_time: Optional[str] = Field(None, description="Check-in time")
    check_out_time: Optional[str] = Field(None, description="Check-out time")
    built_year: Optional[int] = Field(None, description="Year hotel was built")
    renovated_year: Optional[int] = Field(None, description="Last renovation year")
    floor_count: Optional[int] = Field(None, description="Number of floors")
    room_count: Optional[int] = Field(None, description="Total number of rooms")

    # URL
    booking_url: Optional[str] = Field(None, description="URL on Booking.com")

    # Status
    is_active: Optional[bool] = Field(None, description="Whether hotel is active")


class BookingHotelExtensionBase(BaseModel):
    """Base schema for BookingHotelExtension."""

    # Hotel Description
    description: Optional[str] = Field(None, description="Hotel description")
    description_cn: Optional[str] = Field(None, description="Hotel description in Chinese")

    # Policies
    cancellation_policy: Optional[str] = Field(None, description="Cancellation policy")
    cancellation_policy_cn: Optional[str] = Field(None, description="Cancellation policy in Chinese")
    prepayment_policy: Optional[str] = Field(None, description="Prepayment policy")
    prepayment_policy_cn: Optional[str] = Field(None, description="Prepayment policy in Chinese")
    kid_policy: Optional[str] = Field(None, description="Child policy")
    pet_policy: Optional[str] = Field(None, description="Pet policy")

    # Services
    services: Optional[str] = Field(None, description="Hotel services")
    services_cn: Optional[str] = Field(None, description="Hotel services in Chinese")
    service_details: Optional[str] = Field(None, description="Service details in JSON format")

    # Facilities
    facilities: Optional[str] = Field(None, description="Hotel facilities")
    facilities_cn: Optional[str] = Field(None, description="Hotel facilities in Chinese")
    facility_details: Optional[str] = Field(None, description="Facility details in JSON format")

    # Room Facilities
    room_facilities: Optional[str] = Field(None, description="Room facilities")
    room_facilities_cn: Optional[str] = Field(None, description="Room facilities in Chinese")

    # Photos
    photo_urls: Optional[str] = Field(None, description="Hotel photo URLs in JSON format")
    cover_photo_url: Optional[str] = Field(None, description="Cover photo URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail photo URL")

    # Reviews Summary
    review_score: Optional[float] = Field(None, description="Review score")
    review_count: Optional[int] = Field(None, description="Total review count")
    review_score_breakdown: Optional[str] = Field(None, description="Review score breakdown in JSON")

    # Awards/Certifications
    awards: Optional[str] = Field(None, description="Awards and certifications")

    # Nearby Attractions
    nearby_attractions: Optional[str] = Field(None, description="Nearby attractions in JSON format")

    # Important Notes
    important_notes: Optional[str] = Field(None, description="Important notes for guests")


class BookingHotelExtensionCreate(BookingHotelExtensionBase):
    """Schema for creating booking hotel extension."""
    pass


class BookingHotelExtensionUpdate(BaseModel):
    """Schema for updating booking hotel extension."""

    # Hotel Description
    description: Optional[str] = Field(None, description="Hotel description")
    description_cn: Optional[str] = Field(None, description="Hotel description in Chinese")

    # Policies
    cancellation_policy: Optional[str] = Field(None, description="Cancellation policy")
    cancellation_policy_cn: Optional[str] = Field(None, description="Cancellation policy in Chinese")
    prepayment_policy: Optional[str] = Field(None, description="Prepayment policy")
    prepayment_policy_cn: Optional[str] = Field(None, description="Prepayment policy in Chinese")
    kid_policy: Optional[str] = Field(None, description="Child policy")
    pet_policy: Optional[str] = Field(None, description="Pet policy")

    # Services
    services: Optional[str] = Field(None, description="Hotel services")
    services_cn: Optional[str] = Field(None, description="Hotel services in Chinese")
    service_details: Optional[str] = Field(None, description="Service details in JSON format")

    # Facilities
    facilities: Optional[str] = Field(None, description="Hotel facilities")
    facilities_cn: Optional[str] = Field(None, description="Hotel facilities in Chinese")
    facility_details: Optional[str] = Field(None, description="Facility details in JSON format")

    # Room Facilities
    room_facilities: Optional[str] = Field(None, description="Room facilities")
    room_facilities_cn: Optional[str] = Field(None, description="Room facilities in Chinese")

    # Photos
    photo_urls: Optional[str] = Field(None, description="Hotel photo URLs in JSON format")
    cover_photo_url: Optional[str] = Field(None, description="Cover photo URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail photo URL")

    # Reviews Summary
    review_score: Optional[float] = Field(None, description="Review score")
    review_count: Optional[int] = Field(None, description="Total review count")
    review_score_breakdown: Optional[str] = Field(None, description="Review score breakdown in JSON")

    # Awards/Certifications
    awards: Optional[str] = Field(None, description="Awards and certifications")

    # Nearby Attractions
    nearby_attractions: Optional[str] = Field(None, description="Nearby attractions in JSON format")

    # Important Notes
    important_notes: Optional[str] = Field(None, description="Important notes for guests")


class BookingHotelResponse(BookingHotelBase):
    """Schema for booking hotel response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Hotel ID")
    internal_hotel_id: Optional[str] = Field(None, description="Mapped internal hotel ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class BookingHotelWithExtension(BookingHotelResponse):
    """Schema for booking hotel with extension data."""

    extension: Optional[BookingHotelExtensionBase] = Field(None, description="Hotel extension")


class BookingHotelQuery(BaseModel):
    """Query parameters for booking hotels."""

    source: Optional[BookingSource] = Field(None, description="Filter by source")
    source_hotel_id: Optional[str] = Field(None, description="Filter by source hotel ID")
    name: Optional[str] = Field(None, description="Search by hotel name")
    city: Optional[str] = Field(None, description="Filter by city")
    province: Optional[str] = Field(None, description="Filter by province")
    country_code: Optional[str] = Field(None, description="Filter by country code")
    brand: Optional[str] = Field(None, description="Filter by brand")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    internal_hotel_id: Optional[str] = Field(None, description="Filter by internal hotel ID")


class BookingHotelListResponse(BaseModel):
    """Schema for booking hotel list response."""

    items: List[BookingHotelResponse] = Field(..., description="Hotel list")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")


# ============ Room Schemas ============


class BookingRoomBase(BaseModel):
    """Base schema for BookingRoom."""

    # Basic Info
    source: BookingSource = Field(default=BookingSource.BOOKING_COM, description="Data source")
    source_room_id: Optional[str] = Field(None, description="Room ID in source system")
    room_name: str = Field(..., description="Room name on Booking.com")
    room_name_cn: Optional[str] = Field(None, description="Room name in Chinese")
    room_type_code: Optional[str] = Field(None, description="Room type code")

    # Room Configuration
    room_type: Optional[str] = Field(None, description="Room type category")
    bed_type: Optional[str] = Field(None, description="Bed type")
    bed_configuration: Optional[str] = Field(None, description="Bed configuration details")
    max_occupancy: int = Field(default=2, description="Maximum occupancy")
    standard_occupancy: int = Field(default=2, description="Standard occupancy")
    extra_bed_count: Optional[int] = Field(None, description="Extra bed count available")
    room_size: Optional[float] = Field(None, description="Room size in square meters")
    floor: Optional[str] = Field(None, description="Floor information")

    # Room View
    view_type: Optional[str] = Field(None, description="View type")
    window_type: Optional[str] = Field(None, description="Window type")

    # Amenities
    amenities: Optional[str] = Field(None, description="Room amenities")
    amenities_cn: Optional[str] = Field(None, description="Room amenities in Chinese")
    amenity_details: Optional[str] = Field(None, description="Amenity details in JSON format")

    # Bathroom
    bathroom_type: Optional[str] = Field(None, description="Bathroom type")
    bathroom_amenities: Optional[str] = Field(None, description="Bathroom amenities")
    bathroom_amenities_cn: Optional[str] = Field(None, description="Bathroom amenities in Chinese")

    # Media
    photo_urls: Optional[str] = Field(None, description="Room photo URLs in JSON format")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail photo URL")

    # Smoking Policy
    smoking_policy: Optional[str] = Field(None, description="Smoking policy")

    # Booking URL
    booking_url: Optional[str] = Field(None, description="URL on Booking.com")

    # Status
    is_active: bool = Field(default=True, description="Whether room is active")


class BookingRoomCreate(BookingRoomBase):
    """Schema for creating a booking room."""

    hotel_id: str = Field(..., description="Booking hotel ID")


class BookingRoomUpdate(BaseModel):
    """Schema for updating a booking room."""

    # Basic Info
    source: Optional[BookingSource] = Field(None, description="Data source")
    source_room_id: Optional[str] = Field(None, description="Room ID in source system")
    room_name: Optional[str] = Field(None, description="Room name on Booking.com")
    room_name_cn: Optional[str] = Field(None, description="Room name in Chinese")
    room_type_code: Optional[str] = Field(None, description="Room type code")

    # Room Configuration
    room_type: Optional[str] = Field(None, description="Room type category")
    bed_type: Optional[str] = Field(None, description="Bed type")
    bed_configuration: Optional[str] = Field(None, description="Bed configuration details")
    max_occupancy: Optional[int] = Field(None, description="Maximum occupancy")
    standard_occupancy: Optional[int] = Field(None, description="Standard occupancy")
    extra_bed_count: Optional[int] = Field(None, description="Extra bed count available")
    room_size: Optional[float] = Field(None, description="Room size in square meters")
    floor: Optional[str] = Field(None, description="Floor information")

    # Room View
    view_type: Optional[str] = Field(None, description="View type")
    window_type: Optional[str] = Field(None, description="Window type")

    # Amenities
    amenities: Optional[str] = Field(None, description="Room amenities")
    amenities_cn: Optional[str] = Field(None, description="Room amenities in Chinese")
    amenity_details: Optional[str] = Field(None, description="Amenity details in JSON format")

    # Bathroom
    bathroom_type: Optional[str] = Field(None, description="Bathroom type")
    bathroom_amenities: Optional[str] = Field(None, description="Bathroom amenities")
    bathroom_amenities_cn: Optional[str] = Field(None, description="Bathroom amenities in Chinese")

    # Media
    photo_urls: Optional[str] = Field(None, description="Room photo URLs in JSON format")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail photo URL")

    # Smoking Policy
    smoking_policy: Optional[str] = Field(None, description="Smoking policy")

    # Booking URL
    booking_url: Optional[str] = Field(None, description="URL on Booking.com")

    # Status
    is_active: Optional[bool] = Field(None, description="Whether room is active")


class BookingRoomExtensionBase(BaseModel):
    """Base schema for BookingRoomExtension."""

    # Room Description
    description: Optional[str] = Field(None, description="Room description")
    description_cn: Optional[str] = Field(None, description="Room description in Chinese")

    # Policies
    cancellation_policy: Optional[str] = Field(None, description="Cancellation policy")
    cancellation_policy_cn: Optional[str] = Field(None, description="Cancellation policy in Chinese")
    prepayment_policy: Optional[str] = Field(None, description="Prepayment policy")
    prepayment_policy_cn: Optional[str] = Field(None, description="Prepayment policy in Chinese")

    # Accessibility
    accessibility_features: Optional[str] = Field(None, description="Accessibility features in JSON")

    # Additional Information
    additional_info: Optional[str] = Field(None, description="Additional room information")
    additional_info_cn: Optional[str] = Field(None, description="Additional room information in Chinese")

    # Important Notes
    important_notes: Optional[str] = Field(None, description="Important notes for this room")


class BookingRoomExtensionCreate(BookingRoomExtensionBase):
    """Schema for creating booking room extension."""
    pass


class BookingRoomExtensionUpdate(BaseModel):
    """Schema for updating booking room extension."""

    # Room Description
    description: Optional[str] = Field(None, description="Room description")
    description_cn: Optional[str] = Field(None, description="Room description in Chinese")

    # Policies
    cancellation_policy: Optional[str] = Field(None, description="Cancellation policy")
    cancellation_policy_cn: Optional[str] = Field(None, description="Cancellation policy in Chinese")
    prepayment_policy: Optional[str] = Field(None, description="Prepayment policy")
    prepayment_policy_cn: Optional[str] = Field(None, description="Prepayment policy in Chinese")

    # Accessibility
    accessibility_features: Optional[str] = Field(None, description="Accessibility features in JSON")

    # Additional Information
    additional_info: Optional[str] = Field(None, description="Additional room information")
    additional_info_cn: Optional[str] = Field(None, description="Additional room information in Chinese")

    # Important Notes
    important_notes: Optional[str] = Field(None, description="Important notes for this room")


class BookingRoomResponse(BookingRoomBase):
    """Schema for booking room response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Room ID")
    hotel_id: str = Field(..., description="Booking hotel ID")
    internal_room_id: Optional[str] = Field(None, description="Mapped internal room ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class BookingRoomWithExtension(BookingRoomResponse):
    """Schema for booking room with extension data."""

    extension: Optional[BookingRoomExtensionBase] = Field(None, description="Room extension")


class BookingRoomQuery(BaseModel):
    """Query parameters for booking rooms."""

    source: Optional[BookingSource] = Field(None, description="Filter by source")
    source_room_id: Optional[str] = Field(None, description="Filter by source room ID")
    hotel_id: Optional[str] = Field(None, description="Filter by hotel ID")
    room_name: Optional[str] = Field(None, description="Search by room name")
    room_type: Optional[str] = Field(None, description="Filter by room type")
    bed_type: Optional[str] = Field(None, description="Filter by bed type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    internal_room_id: Optional[str] = Field(None, description="Filter by internal room ID")


class BookingRoomListResponse(BaseModel):
    """Schema for booking room list response."""

    items: List[BookingRoomResponse] = Field(..., description="Room list")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total pages")
