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


# ============================================================================
# Test Database Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def db_session_factory(test_engine):
    """Create a database session factory for tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return async_session_maker


@pytest_asyncio.fixture(scope="function")
async def db_session_with_transaction(db_session_factory):
    """Create a database session that rolls back after each test."""
    async with db_session_factory() as session:
        yield session
        await session.rollback()


# ============================================================================
# Hotel and Room Test Fixtures
# ============================================================================


@pytest.fixture
def hotel_factory():
    """
    Factory for creating test hotels.
    Uses factory_boy for flexible test data generation.
    """
    from tests.factories.hotel_factory import HotelFactory
    from app.models.hotel import HotelBrand, HotelStatus

    class HotelTestFactory:
        """Wrapper class for hotel factory with convenience methods."""

        def create(self, **kwargs):
            """Create a single hotel."""
            return HotelFactory(**kwargs)

        def create_batch(self, count: int, **kwargs):
            """Create multiple hotels."""
            return HotelFactory.create_batch(count, **kwargs)

        def create_with_expedia(self, **kwargs):
            """Create a hotel with Expedia IDs."""
            return HotelFactory.create_with_expedia(**kwargs)

        def create_published(self, **kwargs):
            """Create a published hotel."""
            return HotelFactory.create_published(**kwargs)

        def create_draft(self, **kwargs):
            """Create a draft hotel."""
            return HotelFactory.create_draft(**kwargs)

        def create_for_city(self, city: str, count: int = 1, **kwargs):
            """Create hotels in a specific city."""
            return HotelFactory.create_batch_for_city(city, count, **kwargs)

        # Allow direct access to enums
        @property
        def brands(self):
            return HotelBrand

        @property
        def statuses(self):
            return HotelStatus

    return HotelTestFactory()


@pytest.fixture
def room_factory():
    """
    Factory for creating test rooms.
    Uses factory_boy for flexible test data generation.
    """
    from tests.factories.room_factory import RoomFactory, RoomExtensionFactory

    class RoomTestFactory:
        """Wrapper class for room factory with convenience methods."""

        def create(self, **kwargs):
            """Create a single room."""
            return RoomFactory(**kwargs)

        def create_batch(self, count: int, **kwargs):
            """Create multiple rooms."""
            return RoomFactory.create_batch(count, **kwargs)

        def create_for_hotel(self, hotel, **kwargs):
            """Create a room for a specific hotel."""
            return RoomFactory.create_for_hotel(hotel, **kwargs)

        def create_batch_for_hotel(self, hotel, count: int, **kwargs):
            """Create multiple rooms for a specific hotel."""
            return RoomFactory.create_batch_for_hotel(hotel, count, **kwargs)

        def create_standard(self, **kwargs):
            """Create a standard configuration room."""
            return RoomFactory.create_standard_room(**kwargs)

        def create_suite(self, **kwargs):
            """Create a suite room type."""
            return RoomFactory.create_suite(**kwargs)

        def create_deluxe(self, **kwargs):
            """Create a deluxe room type."""
            return RoomFactory.create_deluxe(**kwargs)

    class RoomExtensionTestFactory:
        """Wrapper class for room extension factory with convenience methods."""

        def create(self, **kwargs):
            """Create a single room extension."""
            return RoomExtensionFactory(**kwargs)

        def create_for_room(self, room, **kwargs):
            """Create a room extension for a specific room."""
            return RoomExtensionFactory.create_for_room(room, **kwargs)

        def create_with_amenities(self, **kwargs):
            """Create a room extension with full amenities."""
            return RoomExtensionFactory.create_with_amenities(**kwargs)

    return RoomTestFactory()


@pytest.fixture
def room_extension_factory():
    """Factory for creating test room extensions."""
    from tests.factories.room_factory import RoomExtensionFactory

    class RoomExtensionTestFactory:
        """Wrapper class for room extension factory with convenience methods."""

        def create(self, **kwargs):
            """Create a single room extension."""
            return RoomExtensionFactory(**kwargs)

        def create_for_room(self, room, **kwargs):
            """Create a room extension for a specific room."""
            return RoomExtensionFactory.create_for_room(room, **kwargs)

        def create_with_amenities(self, **kwargs):
            """Create a room extension with full amenities."""
            return RoomExtensionFactory.create_with_amenities(**kwargs)

    return RoomExtensionTestFactory()


# ============================================================================
# Convenience Fixtures for Common Test Scenarios
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def sample_hotel(db_session):
    """Create a sample hotel for testing."""
    from app.models.hotel import Hotel, HotelBrand, HotelStatus

    hotel = Hotel(
        name_cn="测试酒店",
        name_en="Sample Hotel",
        brand=HotelBrand.ATour,
        status=HotelStatus.DRAFT,
        country_code="CN",
        province="上海市",
        city="上海",
        district="浦东新区",
        address_cn="浦东新区某路123号",
        address_en="123 Sample Road, Pudong District",
        postal_code="200000",
        phone="+86-21-12345678",
        email="info@samplehotel.com",
    )
    db_session.add(hotel)
    await db_session.flush()
    await db_session.refresh(hotel)
    return hotel


@pytest_asyncio.fixture(scope="function")
async def sample_room(db_session, sample_hotel):
    """Create a sample room for testing."""
    from app.models.hotel import Room

    room = Room(
        hotel_id=sample_hotel.id,
        room_type_code="STD-KING",
        name_cn="标准大床房",
        name_en="Standard King Room",
        description_cn="温馨舒适的标准大床房",
        description_en="Cozy standard room with king bed",
        bed_type="King",
        max_occupancy=2,
        standard_occupancy=2,
        room_size=30.5,
        floor_range="5-10",
        total_rooms=20,
    )
    db_session.add(room)
    await db_session.flush()
    await db_session.refresh(room)
    return room


@pytest_asyncio.fixture(scope="function")
async def published_hotel(db_session):
    """Create a published hotel for testing."""
    from app.models.hotel import Hotel, HotelBrand, HotelStatus

    hotel = Hotel(
        name_cn="已发布酒店",
        name_en="Published Hotel",
        brand=HotelBrand.ATourX,
        status=HotelStatus.PUBLISHED,
        country_code="CN",
        province="北京市",
        city="北京",
        address_cn="朝阳区某大街1号",
        address_en="1 Sample Street, Chaoyang District",
        postal_code="100000",
        expedia_hotel_id="EXP-PUB-001",
        expedia_chain_code="ATOUR",
        expedia_property_code="ATOUR-BJ-001",
    )
    db_session.add(hotel)
    await db_session.flush()
    await db_session.refresh(hotel)
    return hotel


@pytest_asyncio.fixture(scope="function")
async def hotel_with_rooms(db_session, room_factory):
    """Create a hotel with multiple rooms for testing."""
    from app.models.hotel import Hotel, HotelBrand, HotelStatus

    hotel = Hotel(
        name_cn="多房型酒店",
        name_en="Multi-Room Hotel",
        brand=HotelBrand.ATour,
        status=HotelStatus.DRAFT,
        country_code="CN",
        province="广东省",
        city="广州",
        address_cn="天河区某路100号",
    )
    db_session.add(hotel)
    await db_session.flush()

    # Create multiple room types
    rooms = [
        room_factory.create_for_hotel(hotel, room_type_code="STD", name_cn="标准间", total_rooms=30),
        room_factory.create_for_hotel(hotel, room_type_code="DLX", name_cn="豪华房", total_rooms=20),
        room_factory.create_for_hotel(hotel, room_type_code="STE", name_cn="套房", total_rooms=10),
    ]

    await db_session.flush()
    await db_session.refresh(hotel, ["rooms"])
    return hotel
