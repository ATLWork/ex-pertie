"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_superuser
from app.middleware.exception import BadRequestError
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    Token,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.response import ApiResponse
from app.services.auth import (
    AuthService,
    RoleService,
    UserService,
    init_default_roles,
)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    - **email**: User email address
    - **username**: Unique username
    - **password**: Password (min 8 chars, must include uppercase, lowercase, and digit)
    - **full_name**: Optional full name
    """
    user = await UserService.create_user(db, user_data)
    return ApiResponse(
        code=200,
        message="User registered successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with username/email and password.

    Returns access token and refresh token.
    """
    result = await AuthService.login(db, login_data)
    return ApiResponse(
        code=200,
        message="Login successful",
        data=LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            user=UserResponse.model_validate(result["user"]),
        ),
    )


@router.post("/refresh", response_model=ApiResponse[Token])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.

    Send the refresh token in Authorization header as Bearer token.
    """
    refresh_token = credentials.credentials
    result = await AuthService.refresh_tokens(db, refresh_token)
    return ApiResponse(
        code=200,
        message="Token refreshed successfully",
        data=Token(**result),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user information.
    """
    return ApiResponse(
        code=200,
        message="success",
        data=UserResponse.model_validate(current_user),
    )


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user information.
    """
    user = await UserService.update_user(db, current_user, user_data)
    return ApiResponse(
        code=200,
        message="User updated successfully",
        data=UserResponse.model_validate(user),
    )


@router.put("/me/password", response_model=ApiResponse[dict])
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user password.
    """
    await UserService.change_password(
        db,
        current_user,
        password_data.current_password,
        password_data.new_password,
    )
    return ApiResponse(
        code=200,
        message="Password changed successfully",
        data={},
    )


# ============== Role Management Endpoints ==============

@router.post("/roles", response_model=ApiResponse[RoleResponse])
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new role. Requires superuser privileges.
    """
    role = await RoleService.create_role(db, role_data)
    return ApiResponse(
        code=200,
        message="Role created successfully",
        data=RoleResponse.model_validate(role),
    )


@router.get("/roles", response_model=ApiResponse[list[RoleResponse]])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all roles.
    """
    roles = await RoleService.get_all_roles(db, active_only=False)
    return ApiResponse(
        code=200,
        message="success",
        data=[RoleResponse.model_validate(r) for r in roles],
    )


@router.get("/roles/{role_id}", response_model=ApiResponse[RoleResponse])
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get role by ID.
    """
    role = await RoleService.get_role_by_id(db, role_id)
    return ApiResponse(
        code=200,
        message="success",
        data=RoleResponse.model_validate(role),
    )


@router.put("/roles/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Update role. Requires superuser privileges.
    """
    role = await RoleService.get_role_by_id(db, role_id)
    role = await RoleService.update_role(db, role, role_data)
    return ApiResponse(
        code=200,
        message="Role updated successfully",
        data=RoleResponse.model_validate(role),
    )
