"""
User authentication and management services.
"""

from typing import Optional

from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.middleware.exception import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.models.role import Permission, Role
from app.models.user import User, UserStatus
from app.schemas.auth import (
    LoginRequest,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)


class AuthService:
    """Authentication service for user login and token management."""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User:
        """
        Authenticate a user by username/email and password.

        Args:
            db: Database session
            username: Username or email
            password: Plain text password

        Returns:
            User object if authentication successful

        Raises:
            UnauthorizedError: If credentials are invalid
        """
        # Query user by username or email with roles
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(
                or_(
                    User.username == username,
                    User.email == username,
                )
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise UnauthorizedError(
                message="Invalid credentials",
                details={"field": "username"},
            )

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError(
                message="Invalid credentials",
                details={"field": "password"},
            )

        if not user.is_active:
            raise UnauthorizedError(
                message="User account is inactive",
                details={"status": user.status.value},
            )

        return user

    @staticmethod
    async def login(db: AsyncSession, login_data: LoginRequest) -> dict:
        """
        Login user and return tokens.

        Args:
            db: Database session
            login_data: Login request data

        Returns:
            Dict with tokens and user info
        """
        user = await AuthService.authenticate_user(
            db,
            login_data.username,
            login_data.password,
        )

        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        logger.info(f"User logged in: {user.username}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            db: Database session
            refresh_token: Valid refresh token

        Returns:
            Dict with new tokens
        """
        from app.core.security import verify_token

        user_id = verify_token(refresh_token, token_type="refresh")
        if user_id is None:
            raise UnauthorizedError(message="Invalid refresh token")

        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise UnauthorizedError(message="User not found or inactive")

        new_access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }


class UserService:
    """User management service."""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
        role_names: Optional[list[str]] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User creation data
            role_names: Optional list of role names to assign

        Returns:
            Created User object

        Raises:
            ConflictError: If username or email already exists
        """
        # Check if username or email already exists
        result = await db.execute(
            select(User).where(
                or_(
                    User.username == user_data.username,
                    User.email == user_data.email,
                )
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == user_data.username:
                raise ConflictError(
                    message="Username already registered",
                    details={"field": "username"},
                )
            else:
                raise ConflictError(
                    message="Email already registered",
                    details={"field": "email"},
                )

        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            status=UserStatus.ACTIVE,
        )

        # Assign roles if provided
        if role_names:
            roles_result = await db.execute(
                select(Role).where(Role.name.in_(role_names))
            )
            roles = roles_result.scalars().all()
            user.roles = list(roles)

        db.add(user)
        await db.flush()
        await db.refresh(user, ["roles"])

        logger.info(f"User created: {user.username}")

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object

        Raises:
            NotFoundError: If user not found
        """
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise NotFoundError(message="User not found")

        return user

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User object or None
        """
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: Email address

        Returns:
            User object or None
        """
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user: User,
        user_data: UserUpdate,
    ) -> User:
        """
        Update user information.

        Args:
            db: Database session
            user: User object to update
            user_data: Update data

        Returns:
            Updated User object
        """
        update_data = user_data.model_dump(exclude_unset=True)

        # Check email uniqueness if changing email
        if "email" in update_data and update_data["email"] != user.email:
            existing = await UserService.get_user_by_email(db, update_data["email"])
            if existing:
                raise ConflictError(
                    message="Email already registered",
                    details={"field": "email"},
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.flush()
        await db.refresh(user, ["roles"])

        logger.info(f"User updated: {user.username}")

        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change user password.

        Args:
            db: Database session
            user: User object
            current_password: Current password
            new_password: New password

        Raises:
            BadRequestError: If current password is incorrect
        """
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestError(message="Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        await db.flush()

        logger.info(f"Password changed for user: {user.username}")

    @staticmethod
    async def deactivate_user(db: AsyncSession, user: User) -> User:
        """
        Deactivate a user account.

        Args:
            db: Database session
            user: User object

        Returns:
            Updated User object
        """
        user.status = UserStatus.INACTIVE
        await db.flush()
        await db.refresh(user)

        logger.info(f"User deactivated: {user.username}")

        return user

    @staticmethod
    async def activate_user(db: AsyncSession, user: User) -> User:
        """
        Activate a user account.

        Args:
            db: Database session
            user: User object

        Returns:
            Updated User object
        """
        user.status = UserStatus.ACTIVE
        await db.flush()
        await db.refresh(user)

        logger.info(f"User activated: {user.username}")

        return user


class RoleService:
    """Role management service."""

    @staticmethod
    async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
        """
        Create a new role.

        Args:
            db: Database session
            role_data: Role creation data

        Returns:
            Created Role object

        Raises:
            ConflictError: If role name already exists
        """
        result = await db.execute(select(Role).where(Role.name == role_data.name))
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictError(
                message="Role name already exists",
                details={"field": "name"},
            )

        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            permissions=role_data.permissions,
        )

        db.add(role)
        await db.flush()
        await db.refresh(role)

        logger.info(f"Role created: {role.name}")

        return role

    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: str) -> Role:
        """
        Get role by ID.

        Args:
            db: Database session
            role_id: Role ID

        Returns:
            Role object

        Raises:
            NotFoundError: If role not found
        """
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()

        if role is None:
            raise NotFoundError(message="Role not found")

        return role

    @staticmethod
    async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        """
        Get role by name.

        Args:
            db: Database session
            name: Role name

        Returns:
            Role object or None
        """
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_roles(db: AsyncSession, active_only: bool = True) -> list[Role]:
        """
        Get all roles.

        Args:
            db: Database session
            active_only: Whether to return only active roles

        Returns:
            List of Role objects
        """
        query = select(Role)
        if active_only:
            query = query.where(Role.is_active == True)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_role(
        db: AsyncSession,
        role: Role,
        role_data: RoleUpdate,
    ) -> Role:
        """
        Update role information.

        Args:
            db: Database session
            role: Role object to update
            role_data: Update data

        Returns:
            Updated Role object
        """
        update_data = role_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(role, field, value)

        await db.flush()
        await db.refresh(role)

        logger.info(f"Role updated: {role.name}")

        return role

    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession,
        user: User,
        role: Role,
    ) -> None:
        """
        Assign a role to a user.

        Args:
            db: Database session
            user: User object
            role: Role object
        """
        if role not in user.roles:
            user.roles.append(role)
            await db.flush()
            logger.info(f"Role '{role.name}' assigned to user '{user.username}'")

    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user: User,
        role: Role,
    ) -> None:
        """
        Remove a role from a user.

        Args:
            db: Database session
            user: User object
            role: Role object
        """
        if role in user.roles:
            user.roles.remove(role)
            await db.flush()
            logger.info(f"Role '{role.name}' removed from user '{user.username}'")


async def init_default_roles(db: AsyncSession) -> None:
    """
    Initialize default roles if they don't exist.
    """
    default_roles = [
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system administrator",
            "permissions": [Permission.ADMIN_ALL.value],
        },
        {
            "name": "operator",
            "display_name": "Operator",
            "description": "Channel operator with data management permissions",
            "permissions": [
                Permission.HOTEL_READ.value,
                Permission.HOTEL_WRITE.value,
                Permission.ROOM_READ.value,
                Permission.ROOM_WRITE.value,
                Permission.TRANSLATION_READ.value,
                Permission.TRANSLATION_WRITE.value,
                Permission.EXPORT_READ.value,
                Permission.EXPORT_WRITE.value,
            ],
        },
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Read-only access",
            "permissions": [
                Permission.HOTEL_READ.value,
                Permission.ROOM_READ.value,
                Permission.TRANSLATION_READ.value,
                Permission.EXPORT_READ.value,
            ],
        },
    ]

    for role_data in default_roles:
        existing = await RoleService.get_role_by_name(db, role_data["name"])
        if not existing:
            await RoleService.create_role(
                db,
                RoleCreate(**role_data),
            )

    logger.info("Default roles initialized")
