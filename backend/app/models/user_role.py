"""
User-Role association table for many-to-many relationship.
"""

from sqlalchemy import Column, ForeignKey, String, Table

from app.core.database import Base

# User-Role association table (many-to-many)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
