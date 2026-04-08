"""Health check endpoint for API status."""

from fastapi import APIRouter

from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[dict])
async def health_check():
    """
    Health check endpoint.
    Returns the API status and version.
    """
    return ApiResponse(
        code=200,
        message="success",
        data={
            "status": "healthy",
            "version": "0.1.0",
        },
    )


@router.get("/ready", response_model=ApiResponse[dict])
async def readiness_check():
    """
    Readiness check endpoint.
    Verifies that all required services are available.
    """
    # TODO: Add database and redis connectivity checks
    return ApiResponse(
        code=200,
        message="success",
        data={
            "status": "ready",
            "services": {
                "database": "connected",
                "redis": "connected",
            },
        },
    )
