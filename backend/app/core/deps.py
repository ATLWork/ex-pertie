"""
Authentication dependencies for FastAPI.
"""

from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.middleware.exception import ForbiddenError, UnauthorizedError
from app.models.user import User, UserStatus

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        UnauthorizedError: If token is invalid or user not found
    """
    if credentials is None:
        raise UnauthorizedError(message="Not authenticated", details={"reason": "no_token"})

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if user_id is None:
        raise UnauthorizedError(message="Invalid token", details={"reason": "invalid_token"})

    # Query user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError(message="User not found", details={"reason": "user_not_found"})

    if not user.is_active:
        raise UnauthorizedError(message="User is inactive", details={"reason": "user_inactive"})

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current user from JWT token

    Returns:
        User object if active

    Raises:
        UnauthorizedError: If user is not active
    """
    if not current_user.is_active:
        raise UnauthorizedError(message="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current superuser.

    Args:
        current_user: Current user from JWT token

    Returns:
        User object if superuser

    Raises:
        ForbiddenError: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise ForbiddenError(message="Not enough permissions")
    return current_user


def require_permissions(permissions: List[str]):
    """
    Dependency factory to check if user has required permissions.

    Args:
        permissions: List of required permissions (user needs at least one)

    Returns:
        Dependency function
    """

    async def check_permissions(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        if not current_user.has_any_permission(permissions):
            raise ForbiddenError(
                message="Not enough permissions",
                details={"required": permissions},
            )
        return current_user

    return check_permissions


def require_permission(permission: str):
    """
    Dependency factory to check if user has a specific permission.

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """

    async def check_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        if not current_user.has_permission(permission):
            raise ForbiddenError(
                message="Not enough permissions",
                details={"required": permission},
            )
        return current_user

    return check_permission


def require_roles(role_names: List[str]):
    """
    Dependency factory to check if user has required roles.

    Args:
        role_names: List of required role names (user needs at least one)

    Returns:
        Dependency function
    """

    async def check_roles(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        if not any(current_user.has_role(role_name) for role_name in role_names):
            raise ForbiddenError(
                message="Not enough permissions",
                details={"required_roles": role_names},
            )
        return current_user

    return check_roles


# Optional user dependency - returns None if not authenticated
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object or None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if user_id is None:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        return user

    return None
