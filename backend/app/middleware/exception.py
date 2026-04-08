"""
Global exception handling middleware and custom exceptions.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError


class AppException(Exception):
    """
    Base application exception.
    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        code: int,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict] = None):
        super().__init__(
            code=404,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class BadRequestError(AppException):
    """Bad request exception."""

    def __init__(self, message: str = "Bad request", details: Optional[Dict] = None):
        super().__init__(
            code=400,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UnauthorizedError(AppException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict] = None):
        super().__init__(
            code=401,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppException):
    """Forbidden exception."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict] = None):
        super().__init__(
            code=403,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(AppException):
    """Conflict exception."""

    def __init__(self, message: str = "Conflict", details: Optional[Dict] = None):
        super().__init__(
            code=409,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


# Business Exceptions (1000+)
class ImportError(AppException):
    """Data import exception."""

    def __init__(self, message: str = "Import failed", details: Optional[Dict] = None):
        super().__init__(
            code=1001,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ValidationError(AppException):
    """Data validation exception."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            code=1002,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class TranslationError(AppException):
    """Translation service exception."""

    def __init__(self, message: str = "Translation failed", details: Optional[Dict] = None):
        super().__init__(
            code=1003,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExportError(AppException):
    """Data export exception."""

    def __init__(self, message: str = "Export failed", details: Optional[Dict] = None):
        super().__init__(
            code=1004,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalAPIError(AppException):
    """External API exception."""

    def __init__(self, message: str = "External API error", details: Optional[Dict] = None):
        super().__init__(
            code=1005,
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


def create_error_response(
    code: int, message: str, details: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "code": code,
        "message": message,
        "details": details or {},
        "timestamp": int(datetime.now().timestamp()),
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handler for custom application exceptions."""
    logger.error(
        f"Application error: {exc.code} - {exc.message}",
        extra={"details": exc.details, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.code, exc.message, exc.details),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler for Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"errors": errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            code=422, message="Validation Error", details={"errors": errors}
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions."""
    logger.exception(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            code=500,
            message="Internal Server Error",
            details={"error": str(exc)} if logger.level("DEBUG") >= 20 else None,
        ),
    )


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add exception handlers to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # Uncomment in production to catch all unhandled exceptions
    # app.add_exception_handler(Exception, generic_exception_handler)
