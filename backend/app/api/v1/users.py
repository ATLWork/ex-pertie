"""
User management API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_superuser, get_current_user
from app.middleware.exception import BadRequestError
from app.models.role import Role
from app.models.user import User, UserStatus
from app.schemas.auth import UserBriefResponse, UserResponse
from app.schemas.response import ApiResponse, PagedData, PagedResponse
from app.services.auth import RoleService, UserService

router = APIRouter()


@router.get("", response_model=PagedResponse[UserBriefResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users with pagination. Requires authentication.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by user status
    - **search**: Search by username or email
    """
    # Build query
    from sqlalchemy import func, or_, select

    query = select(User)

    if status:
        query = query.where(User.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[UserBriefResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user profile.
    """
    return ApiResponse(
        code=200,
        message="success",
        data=UserResponse.model_validate(current_user),
    )


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user by ID.
    """
    user = await UserService.get_user_by_id(db, user_id)
    return ApiResponse(
        code=200,
        message="success",
        data=UserResponse.model_validate(user),
    )


@router.post("/{user_id}/activate", response_model=ApiResponse[UserResponse])
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a user account. Requires superuser privileges.
    """
    user = await UserService.get_user_by_id(db, user_id)
    user = await UserService.activate_user(db, user)
    return ApiResponse(
        code=200,
        message="User activated successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/{user_id}/deactivate", response_model=ApiResponse[UserResponse])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user account. Requires superuser privileges.
    """
    user = await UserService.get_user_by_id(db, user_id)
    user = await UserService.deactivate_user(db, user)
    return ApiResponse(
        code=200,
        message="User deactivated successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/{user_id}/roles/{role_id}", response_model=ApiResponse[UserResponse])
async def assign_role(
    user_id: str,
    role_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a role to a user. Requires superuser privileges.
    """
    user = await UserService.get_user_by_id(db, user_id)
    role = await RoleService.get_role_by_id(db, role_id)
    await RoleService.assign_role_to_user(db, user, role)
    await db.refresh(user, ["roles"])
    return ApiResponse(
        code=200,
        message="Role assigned successfully",
        data=UserResponse.model_validate(user),
    )


@router.delete("/{user_id}/roles/{role_id}", response_model=ApiResponse[UserResponse])
async def remove_role(
    user_id: str,
    role_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a role from a user. Requires superuser privileges.
    """
    user = await UserService.get_user_by_id(db, user_id)
    role = await RoleService.get_role_by_id(db, role_id)
    await RoleService.remove_role_from_user(db, user, role)
    await db.refresh(user, ["roles"])
    return ApiResponse(
        code=200,
        message="Role removed successfully",
        data=UserResponse.model_validate(user),
    )
