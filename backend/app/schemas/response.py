"""
Unified API response schemas.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response format.
    All API responses should use this format.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "success",
                "data": {},
                "timestamp": 1712500000,
            }
        }
    )

    code: int = Field(..., description="Response code, 200 for success")
    message: str = Field(..., description="Response message")
    data: T = Field(..., description="Response data")
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Response timestamp",
    )


class PagedData(BaseModel, Generic[T]):
    """
    Paginated data structure.
    Used for list endpoints with pagination.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "list": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
            }
        }
    )

    list: List[T] = Field(..., description="Data list")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")


class PagedResponse(BaseModel, Generic[T]):
    """
    Paginated API response format.
    """

    code: int = Field(default=200, description="Response code")
    message: str = Field(default="success", description="Response message")
    data: PagedData[T] = Field(..., description="Paginated data")
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Response timestamp",
    )


class ErrorResponse(BaseModel):
    """
    Error response format.
    """

    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Error details"
    )
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Response timestamp",
    )


class ValidationErrorDetail(BaseModel):
    """Validation error detail for a single field."""

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(default=None, description="Invalid value")


class ValidationErrorResponse(BaseModel):
    """
    Validation error response with field details.
    """

    code: int = Field(default=422, description="Error code")
    message: str = Field(default="Validation Error", description="Error message")
    errors: List[ValidationErrorDetail] = Field(
        default_factory=list, description="Validation errors"
    )
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Response timestamp",
    )


def success_response(
    data: Any = None, message: str = "success", code: int = 200
) -> ApiResponse:
    """
    Create a success response.

    Args:
        data: Response data
        message: Success message
        code: Response code

    Returns:
        ApiResponse with success data
    """
    return ApiResponse(code=code, message=message, data=data)


def error_response(
    message: str, code: int = 400, details: Optional[dict] = None
) -> ErrorResponse:
    """
    Create an error response.

    Args:
        message: Error message
        code: Error code
        details: Additional error details

    Returns:
        ErrorResponse with error details
    """
    return ErrorResponse(code=code, message=message, details=details)


def paged_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "success",
) -> PagedResponse:
    """
    Create a paginated response.

    Args:
        items: List of items
        total: Total count
        page: Current page
        page_size: Items per page
        message: Success message

    Returns:
        PagedResponse with paginated data
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PagedResponse(
        code=200,
        message=message,
        data=PagedData(
            list=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )
