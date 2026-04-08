"""
Pydantic schemas for Hotel and Room related APIs.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.hotel import HotelBrand, HotelStatus


class HotelBase(BaseModel):
    """Base schema for Hotel."""

    # Basic Info
    name_cn: str = Field(..., max_length=255, description="Hotel name in Chinese")
    name_en: Optional[str] = Field(None, max_length=255, description="Hotel name in English")
    brand: HotelBrand = Field(default=HotelBrand.ATour, description="Hotel brand")
    status: HotelStatus = Field(default=HotelStatus.DRAFT, description="Hotel status")

    # Location Info
    country_code: str = Field(default="CN", max_length=10, description="Country code (ISO 3166-1)")
    province: str = Field(..., max_length=100, description="Province/State")
    city: str = Field(..., max_length=100, description="City")
    district: Optional[str] = Field(None, max_length=100, description="District/County")
    address_cn: str = Field(..., max_length=500, description="Address in Chinese")
    address_en: Optional[str] = Field(None, max_length=500, description="Address in English")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")

    # Contact Info
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=500, description="Website URL")

    # Geolocation
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")

    # Expedia specific
    expedia_hotel_id: Optional[str] = Field(None, max_length=100, description="Expedia Hotel ID")
    expedia_chain_code: Optional[str] = Field(None, max_length=50, description="Expedia Chain Code")
    expedia_property_code: Optional[str] = Field(None, max_length=50, description="Expedia Property Code")

    # Timestamps
    opened_at: Optional[datetime] = Field(None, description="Hotel opening date")
    renovated_at: Optional[datetime] = Field(None, description="Last renovation date")


class HotelCreate(HotelBase):
    """Schema for creating a hotel."""

    pass


class HotelUpdate(BaseModel):
    """Schema for updating a hotel."""

    # Basic Info
    name_cn: Optional[str] = Field(None, max_length=255, description="Hotel name in Chinese")
    name_en: Optional[str] = Field(None, max_length=255, description="Hotel name in English")
    brand: Optional[HotelBrand] = Field(None, description="Hotel brand")
    status: Optional[HotelStatus] = Field(None, description="Hotel status")

    # Location Info
    country_code: Optional[str] = Field(None, max_length=10, description="Country code (ISO 3166-1)")
    province: Optional[str] = Field(None, max_length=100, description="Province/State")
    city: Optional[str] = Field(None, max_length=100, description="City")
    district: Optional[str] = Field(None, max_length=100, description="District/County")
    address_cn: Optional[str] = Field(None, max_length=500, description="Address in Chinese")
    address_en: Optional[str] = Field(None, max_length=500, description="Address in English")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")

    # Contact Info
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=500, description="Website URL")

    # Geolocation
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")

    # Expedia specific
    expedia_hotel_id: Optional[str] = Field(None, max_length=100, description="Expedia Hotel ID")
    expedia_chain_code: Optional[str] = Field(None, max_length=50, description="Expedia Chain Code")
    expedia_property_code: Optional[str] = Field(None, max_length=50, description="Expedia Property Code")

    # Timestamps
    opened_at: Optional[datetime] = Field(None, description="Hotel opening date")
    renovated_at: Optional[datetime] = Field(None, description="Last renovation date")


class HotelResponse(HotelBase):
    """Schema for hotel response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Hotel ID")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class HotelListResponse(BaseModel):
    """Schema for hotel list response."""

    items: List[HotelResponse] = Field(..., description="Hotel list")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class HotelQuery(BaseModel):
    """Query parameters for hotels."""

    name: Optional[str] = Field(None, description="Search by hotel name")
    brand: Optional[HotelBrand] = Field(None, description="Filter by brand")
    status: Optional[HotelStatus] = Field(None, description="Filter by status")
    city: Optional[str] = Field(None, description="Filter by city")
    province: Optional[str] = Field(None, description="Filter by province")
    expedia_hotel_id: Optional[str] = Field(None, description="Filter by Expedia Hotel ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
