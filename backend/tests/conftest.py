"""
Pytest configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import create_application
from app.models.role import Permission, Role
from app.models.user import User, UserStatus
from app.services.auth import init_default_roles

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def app(db_session: AsyncSession) -> FastAPI:
    """Create a test application instance."""
    app = create_application()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture(scope="function")
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test123456"),
        full_name="Test User",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user, ["roles"])
    return user


@pytest_asyncio.fixture(scope="function")
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("Admin123456"),
        full_name="Admin User",
        status=UserStatus.ACTIVE,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user, ["roles"])
    return user


@pytest_asyncio.fixture(scope="function")
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    role = Role(
        name="test_role",
        display_name="Test Role",
        description="Role for testing",
        permissions=[Permission.HOTEL_READ.value, Permission.ROOM_READ.value],
    )
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture(scope="function")
async def default_roles(db_session: AsyncSession) -> list[Role]:
    """Initialize default roles."""
    await init_default_roles(db_session)
    from sqlalchemy import select

    result = await db_session.execute(select(Role))
    return list(result.scalars().all())


def get_auth_headers(user: User) -> dict[str, str]:
    """Get authorization headers for a user."""
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Get authorization headers for test user."""
    return get_auth_headers(test_user)


@pytest.fixture
def admin_auth_headers(test_superuser: User) -> dict[str, str]:
    """Get authorization headers for admin user."""
    return get_auth_headers(test_superuser)


# Translation test fixtures
@pytest.fixture
def mock_redis():
    """Create a mock Redis client for translation tests."""
    from unittest.mock import AsyncMock, MagicMock

    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.scan_iter = MagicMock(return_value=iter([]))
    return redis_mock


@pytest.fixture
def translation_settings():
    """Test settings for translation module."""
    from pydantic_settings import BaseSettings

    class TestSettings(BaseSettings):
        TENCENT_SECRET_ID: str = "test_secret_id"
        TENCENT_SECRET_KEY: str = "test_secret_key"
        TENCENT_REGION: str = "ap-shanghai"
        AI_API_KEY: str = "test_api_key"
        AI_API_BASE_URL: str = "https://api.deepseek.com/v1"
        AI_MODEL: str = "deepseek-chat"
        TRANSLATION_CACHE_TTL: int = 3600
        TRANSLATION_TIMEOUT: int = 30

    return TestSettings()
