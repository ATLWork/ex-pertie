"""
Role model for RBAC.
"""

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Permission(str, enum.Enum):
    """Permission enum for role-based access control."""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Role management
    ROLE_READ = "role:read"
    ROLE_WRITE = "role:write"
    ROLE_DELETE = "role:delete"

    # Hotel data management
    HOTEL_READ = "hotel:read"
    HOTEL_WRITE = "hotel:write"
    HOTEL_DELETE = "hotel:delete"

    # Room data management
    ROOM_READ = "room:read"
    ROOM_WRITE = "room:write"
    ROOM_DELETE = "room:delete"

    # Translation
    TRANSLATION_READ = "translation:read"
    TRANSLATION_WRITE = "translation:write"

    # Export
    EXPORT_READ = "export:read"
    EXPORT_WRITE = "export:write"

    # Admin
    ADMIN_ALL = "admin:all"


class Role(BaseModel):
    """
    Role model for role-based access control.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    permissions: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions or Permission.ADMIN_ALL in self.permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if role has any of the specified permissions."""
        if Permission.ADMIN_ALL in self.permissions:
            return True
        return any(p in self.permissions for p in permissions)
