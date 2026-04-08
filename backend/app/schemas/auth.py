"""
Authentication and user schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============== Token Schemas ==============
class Token(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type")


# ============== User Schemas ==============
class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


class UserCreate(UserBase):
    """User registration schema."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    """User password update schema."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class RoleResponse(BaseModel):
    """Role response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []


class UserResponse(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    status: str
    is_superuser: bool = False
    avatar_url: Optional[str] = None
    roles: List[RoleResponse] = []
    created_at: datetime
    updated_at: datetime


class UserBriefResponse(BaseModel):
    """User brief response schema (without roles)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    status: str
    is_superuser: bool = False
    avatar_url: Optional[str] = None


# ============== Login Schema ==============
class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== Role Schemas ==============
class RoleCreate(BaseModel):
    """Role creation schema."""

    name: str = Field(..., min_length=2, max_length=50, description="Role name")
    display_name: str = Field(..., max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[str] = Field(default_factory=list, description="Permissions")


class RoleUpdate(BaseModel):
    """Role update schema."""

    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
