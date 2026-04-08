"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, health, translation, users

from app.api.v1.hotels import router as hotels_router
from app.api.v1.imports import router as imports_router
from app.api.v1.exports import router as exports_router

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(hotels_router, prefix="/hotels", tags=["hotels"])
api_router.include_router(imports_router, prefix="/imports", tags=["imports"])
api_router.include_router(exports_router, prefix="/exports", tags=["exports"])
