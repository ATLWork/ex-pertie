"""
Pydantic schemas for BookingReference API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BookingReferenceBase(BaseModel):
    """Base schema for booking reference."""

    source_text: str = Field(..., description="Original text in source language")
    ctrip_translation: Optional[str] = Field(None, description="Translation from Ctrip")
    booking_translation: Optional[str] = Field(None, description="Translation from Booking.com")
    source_lang: str = Field(..., max_length=10, description="Source language code")
    target_lang: str = Field(..., max_length=10, description="Target language code")
    hotel_name: Optional[str] = Field(None, max_length=255, description="Associated hotel name")
    hotel_address: Optional[str] = Field(None, description="Associated hotel address")
    is_active: bool = Field(default=True, description="Whether reference is active")


class BookingReferenceCreate(BookingReferenceBase):
    """Schema for creating booking reference."""

    pass


class BookingReferenceUpdate(BaseModel):
    """Schema for updating booking reference."""

    source_text: Optional[str] = Field(None, description="Original text in source language")
    ctrip_translation: Optional[str] = Field(None, description="Translation from Ctrip")
    booking_translation: Optional[str] = Field(None, description="Translation from Booking.com")
    source_lang: Optional[str] = Field(None, max_length=10, description="Source language code")
    target_lang: Optional[str] = Field(None, max_length=10, description="Target language code")
    hotel_name: Optional[str] = Field(None, max_length=255, description="Associated hotel name")
    hotel_address: Optional[str] = Field(None, description="Associated hotel address")
    is_active: Optional[bool] = Field(None, description="Whether reference is active")


class BookingReferenceResponse(BookingReferenceBase):
    """Schema for booking reference response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Reference ID")
    usage_count: int = Field(default=0, description="Number of times this reference was used")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class BookingReferenceQuery(BaseModel):
    """Query parameters for booking references."""

    source_lang: Optional[str] = Field(None, description="Filter by source language")
    target_lang: Optional[str] = Field(None, description="Filter by target language")
    hotel_name: Optional[str] = Field(None, description="Filter by hotel name (partial match)")
    hotel_address: Optional[str] = Field(None, description="Filter by hotel address (partial match)")
    source_text: Optional[str] = Field(None, description="Filter by source text (partial match)")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


class BookingReferenceBulkCreate(BaseModel):
    """Schema for bulk creating booking references."""

    items: List[BookingReferenceCreate] = Field(..., description="List of booking reference items to create")