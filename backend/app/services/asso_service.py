"""
ASSO SSO Service - Validates ASSO tokens and creates local users.
"""

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.middleware.exception import BadRequestError, UnauthorizedError
from app.models.role import Role
from app.models.user import User, UserStatus

# ASSO Gateway configuration
ASSO_GATEWAY_URL = "https://gateway.corp.yaduo.com"
ASSO_API_GET_USER = "/api/asso/asso/getUserByToken"


class AssoService:
    """Service for ASSO SSO integration."""

    @staticmethod
    async def validate_and_create_user(db: AsyncSession, asso_token: str) -> dict:
        """
        Validate ASSO token and create/get local user.

        Args:
            db: Database session
            asso_token: ASSO token from SSO login

        Returns:
            Dict with access_token, refresh_token, token_type, and user
        """
        # Get user info from ASSO Gateway
        user_info = await AssoService.get_user_info_from_asso(asso_token)

        if not user_info:
            raise UnauthorizedError(message="Invalid ASSO token")

        # Find or create local user
        user = await AssoService.get_or_create_user(db, user_info)

        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        logger.info(f"ASSO user logged in: {user.username}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    async def get_user_info_from_asso(asso_token: str) -> dict | None:
        """
        Call ASSO Gateway to get user info by token.

        Args:
            asso_token: ASSO token

        Returns:
            User info dict or None if validation fails
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{ASSO_GATEWAY_URL}{ASSO_API_GET_USER}",
                    json={"assoToken": asso_token, "source": "unknown"},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 200:
                        return data.get("data", {})
                    return None
                return None
        except Exception as e:
            logger.error(f"Failed to validate ASSO token: {e}")
            return None

    @staticmethod
    async def get_or_create_user(db: AsyncSession, user_info: dict) -> User:
        """
        Get existing user or create new one from ASSO user info.

        Args:
            db: Database session
            user_info: User info from ASSO

        Returns:
            User object
        """
        # Try to find user by ASSO user ID or email
        asso_user_id = user_info.get("userId")
        email = user_info.get("email")

        # Query user by asso_id or email
        query = select(User).options(selectinload(User.roles))

        if asso_user_id:
            query = query.where(User.asso_id == asso_user_id)
        elif email:
            query = query.where(User.email == email)
        else:
            raise BadRequestError(message="No userId or email from ASSO")

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Update user info from ASSO
            user.full_name = user_info.get("realName") or user.full_name
            user.email = email or user.email
            if not user.asso_id and asso_user_id:
                user.asso_id = asso_user_id
            await db.flush()
            await db.refresh(user, ["roles"])
            return user

        # Create new user
        username = user_info.get("userName") or user_info.get("realName") or email.split("@")[0] if email else "user"
        password = get_password_hash(f"asso_{asso_user_id}_{user_info.get('tenantId', 'default')}")

        user = User(
            email=email or f"{asso_user_id}@asso.local",
            username=username,
            hashed_password=password,
            full_name=user_info.get("realName"),
            status=UserStatus.ACTIVE,
            asso_id=asso_user_id,
        )

        # Assign default role (operator)
        roles_result = await db.execute(
            select(Role).where(Role.name == "operator")
        )
        operator_role = roles_result.scalar_one_or_none()
        if operator_role:
            user.roles.append(operator_role)

        db.add(user)
        await db.flush()
        await db.refresh(user, ["roles"])

        logger.info(f"Created new user from ASSO: {username}")

        return user