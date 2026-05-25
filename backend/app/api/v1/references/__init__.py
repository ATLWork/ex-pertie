"""
Booking Reference API router.
"""

from fastapi import APIRouter

from app.api.v1.references.booking import router as booking_router

router = APIRouter()

router.include_router(booking_router, prefix="/booking", tags=["booking-references"])