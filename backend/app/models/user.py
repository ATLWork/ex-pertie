"""
User model for authentication and authorization.
"""

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import Role


class UserStatus(str, enum.Enum):
    """User status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class User(BaseModel):
    """
    User model for authentication.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        return any(role.has_permission(permission) for role in self.roles if role.is_active)

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        if self.is_superuser:
            return True
        return any(
            role.has_any_permission(permissions) for role in self.roles if role.is_active
        )

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
