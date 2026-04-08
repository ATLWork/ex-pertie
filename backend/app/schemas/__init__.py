"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    Token,
    TokenPayload,
    UserBriefResponse,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.response import (
    ApiResponse,
    ErrorResponse,
    PagedData,
    PagedResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
    error_response,
    paged_response,
    success_response,
)

__all__ = [
    # Response schemas
    "ApiResponse",
    "PagedData",
    "PagedResponse",
    "ErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "success_response",
    "error_response",
    "paged_response",
    # Auth schemas
    "Token",
    "TokenPayload",
    "LoginRequest",
    "LoginResponse",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserBriefResponse",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
]
