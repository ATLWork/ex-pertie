"""
Room schemas for API request/response validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============== RoomExtension Schemas ==============
class RoomExtensionBase(BaseModel):
    """Base room extension schema."""

    amenities_cn: Optional[str] = Field(None, description="Room amenities in Chinese")
    amenities_en: Optional[str] = Field(None, description="Room amenities in English")
    amenity_details: Optional[str] = Field(None, description="Detailed amenities in JSON format")
    image_urls: Optional[str] = Field(None, description="Room image URLs in JSON format")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    view_type: Optional[str] = Field(None, description="View type (e.g., City, Sea, Garden)")
    balcony: Optional[bool] = Field(None, description="Has balcony")
    smoking_policy: Optional[str] = Field(None, description="Smoking policy")
    floor: Optional[str] = Field(None, description="Floor information")
    bathroom_type: Optional[str] = Field(None, description="Bathroom type")
    bathroom_amenities_cn: Optional[str] = Field(None, description="Bathroom amenities in Chinese")
    bathroom_amenities_en: Optional[str] = Field(None, description="Bathroom amenities in English")
    accessibility_features: Optional[str] = Field(None, description="Accessibility features in JSON format")


class RoomExtensionCreate(RoomExtensionBase):
    """Room extension creation schema."""

    room_id: str = Field(..., description="Room ID")


class RoomExtensionUpdate(BaseModel):
    """Room extension update schema."""

    amenities_cn: Optional[str] = None
    amenities_en: Optional[str] = None
    amenity_details: Optional[str] = None
    image_urls: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_type: Optional[str] = None
    balcony: Optional[bool] = None
    smoking_policy: Optional[str] = None
    floor: Optional[str] = None
    bathroom_type: Optional[str] = None
    bathroom_amenities_cn: Optional[str] = None
    bathroom_amenities_en: Optional[str] = None
    accessibility_features: Optional[str] = None


class RoomExtensionResponse(RoomExtensionBase):
    """Room extension response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: str
    created_at: datetime
    updated_at: datetime


# ============== Room Schemas ==============
class RoomBase(BaseModel):
    """Base room schema."""

    room_type_code: str = Field(..., max_length=100, description="Room type code (internal)")
    name_cn: str = Field(..., max_length=255, description="Room name in Chinese")
    name_en: Optional[str] = Field(None, max_length=255, description="Room name in English")
    description_cn: Optional[str] = Field(None, description="Room description in Chinese")
    description_en: Optional[str] = Field(None, description="Room description in English")
    bed_type: Optional[str] = Field(None, max_length=100, description="Bed type")
    max_occupancy: int = Field(default=2, ge=1, description="Maximum occupancy")
    standard_occupancy: int = Field(default=2, ge=1, description="Standard occupancy")
    room_size: Optional[float] = Field(None, description="Room size in square meters")
    floor_range: Optional[str] = Field(None, max_length=50, description="Floor range")
    total_rooms: int = Field(default=1, ge=1, description="Total number of rooms")
    expedia_room_id: Optional[str] = Field(None, max_length=100, description="Expedia Room ID")
    expedia_room_type_code: Optional[str] = Field(None, max_length=50, description="Expedia Room Type Code")
    is_active: bool = Field(default=True, description="Whether room type is active")


class RoomCreate(RoomBase):
    """Room creation schema."""

    hotel_id: str = Field(..., description="Hotel ID")


class RoomUpdate(BaseModel):
    """Room update schema."""

    room_type_code: Optional[str] = Field(None, max_length=100)
    name_cn: Optional[str] = Field(None, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    description_cn: Optional[str] = None
    description_en: Optional[str] = None
    bed_type: Optional[str] = Field(None, max_length=100)
    max_occupancy: Optional[int] = Field(None, ge=1)
    standard_occupancy: Optional[int] = Field(None, ge=1)
    room_size: Optional[float] = None
    floor_range: Optional[str] = Field(None, max_length=50)
    total_rooms: Optional[int] = Field(None, ge=1)
    expedia_room_id: Optional[str] = Field(None, max_length=100)
    expedia_room_type_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    """Room response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    hotel_id: str
    created_at: datetime
    updated_at: datetime


class RoomDetailResponse(RoomBase):
    """Room detail response with extension schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    hotel_id: str
    created_at: datetime
    updated_at: datetime
    extension: Optional[RoomExtensionResponse] = None


class RoomListResponse(BaseModel):
    """Room list response schema."""

    model_config = ConfigDict(from_attributes=True)

    rooms: List[RoomResponse]
    total: int
    page: int
    page_size: int
