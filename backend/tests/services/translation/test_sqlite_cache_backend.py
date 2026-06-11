"""
Unit tests for SQLiteCacheBackend.
Tests all functionality of the SQLite-based translation cache backend.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.translation_cache import TranslationCache
from app.services.translation.sqlite_cache_backend import SQLiteCacheBackend

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine and create tables."""
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


@pytest_asyncio.fixture(scope="function")
def sqlite_backend() -> SQLiteCacheBackend:
    """Create SQLiteCacheBackend instance."""
    return SQLiteCacheBackend()


@pytest.mark.asyncio
async def test_set_then_get_roundtrip(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test basic set and get roundtrip functionality."""
    cache_key = "translation:zh:en:mt:1234567890abcdef"
    
    set_success = await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="你好世界",
        source_lang="zh",
        target_lang="en",
        translated_text="Hello World",
        source="MACHINE",
        confidence=0.95,
        metadata={"model": "test-model"}
    )
    
    assert set_success is True
    
    cached_value = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    
    assert cached_value is not None
    data = json.loads(cached_value)
    assert data["translated_text"] == "Hello World"
    assert data["original_text"] == "你好世界"
    assert data["source"] == "MACHINE"
    assert data["confidence"] == 0.95
    assert data["metadata"]["model"] == "test-model"


@pytest.mark.asyncio
async def test_get_missing_key_returns_none(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that getting a non-existent key returns None."""
    result = await sqlite_backend.get(db=db_session, cache_key="nonexistent:key")
    assert result is None


@pytest.mark.asyncio
async def test_expired_entry_not_returned(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that expired entries are not returned."""
    cache_key = "translation:zh:en:mt:expired01"
    
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=0,  # Expires immediately
        text="过期文本",
        source_lang="zh",
        target_lang="en",
        translated_text="Expired Text",
        source="MACHINE"
    )
    
    # Wait a tiny bit to ensure expiration
    await asyncio.sleep(0.01)
    
    result = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    assert result is None


@pytest.mark.asyncio
async def test_ttl_boundary(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test TTL boundary conditions - one expired, one active."""
    # Create two entries with different TTLs
    key1 = "translation:zh:en:mt:active01"
    key2 = "translation:zh:en:mt:expired02"
    
    await sqlite_backend.set(db=db_session, cache_key=key1, ttl=3600, text="active", 
                            source_lang="zh", target_lang="en", translated_text="Active", source="MACHINE")
    await sqlite_backend.set(db=db_session, cache_key=key2, ttl=-1, text="expired", 
                            source_lang="zh", target_lang="en", translated_text="Expired", source="MACHINE")
    
    # Manually set ttl_expires_at to past for key2 to ensure it's expired
    from sqlalchemy import select
    stmt = select(TranslationCache).where(TranslationCache.cache_key == key2)
    result = await db_session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.ttl_expires_at = datetime.now() - timedelta(hours=1)
        await db_session.commit()
    
    # Check results
    active_result = await sqlite_backend.get(db=db_session, cache_key=key1)
    expired_result = await sqlite_backend.get(db=db_session, cache_key=key2)
    
    assert active_result is not None
    assert expired_result is None


@pytest.mark.asyncio
async def test_upsert_existing_key(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that setting an existing key updates it (upsert)."""
    cache_key = "translation:zh:en:mt:upsert01"
    
    # First set
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="原始文本",
        source_lang="zh",
        target_lang="en",
        translated_text="Original Text",
        source="MACHINE",
        confidence=0.8
    )
    
    # Verify first value
    first_value = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    first_data = json.loads(first_value)
    assert first_data["translated_text"] == "Original Text"
    assert first_data["confidence"] == 0.8
    
    # Update with new value
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="原始文本",
        source_lang="zh",
        target_lang="en",
        translated_text="Updated Text",
        source="AI_ENHANCED",
        confidence=0.99,
        metadata={"updated": True}
    )
    
    # Verify updated value
    second_value = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    second_data = json.loads(second_value)
    assert second_data["translated_text"] == "Updated Text"
    assert second_data["source"] == "AI_ENHANCED"
    assert second_data["confidence"] == 0.99
    assert second_data["metadata"]["updated"] is True


@pytest.mark.asyncio
async def test_delete_existing_key(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test deleting an existing key."""
    cache_key = "translation:zh:en:mt:delete01"
    
    # First set
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="删除我",
        source_lang="zh",
        target_lang="en",
        translated_text="Delete Me",
        source="MACHINE"
    )
    
    # Verify it exists
    before_delete = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    assert before_delete is not None
    
    # Delete it
    delete_success = await sqlite_backend.delete(db=db_session, cache_key=cache_key)
    assert delete_success is True
    
    # Verify it's gone
    after_delete = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    assert after_delete is None


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_true(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that deleting a non-existent key returns True (success)."""
    result = await sqlite_backend.delete(db=db_session, cache_key="nonexistent:key")
    assert result is True


@pytest.mark.asyncio
async def test_stats_counts_valid_entries(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that stats correctly counts active and expired entries."""
    # Add some entries
    keys = [
        ("key1", 3600, "active1"),
        ("key2", 3600, "active2"), 
        ("key3", -3600, "expired1"),  # Will be expired immediately
    ]
    
    for key, ttl, text in keys:
        await sqlite_backend.set(
            db=db_session,
            cache_key=f"translation:zh:en:mt:{key}",
            ttl=ttl,
            text=text,
            source_lang="zh",
            target_lang="en",
            translated_text=text,
            source="MACHINE"
        )
    
    # Manually update the expired one to ensure ttl_expires_at is past
    from sqlalchemy import select
    stmt = select(TranslationCache).where(TranslationCache.cache_key == "translation:zh:en:mt:key3")
    result = await db_session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.ttl_expires_at = datetime.now() - timedelta(hours=1)
        await db_session.commit()
    
    stats = await sqlite_backend.stats(db=db_session)
    
    assert stats["total_cached"] == 2  # only non-expired
    assert stats["backend"] == "sqlite"
    assert stats["oldest_entry"] is not None


@pytest.mark.asyncio
async def test_clear_all_returns_true(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that clear_all removes all entries."""
    # Add multiple entries
    for i in range(5):
        await sqlite_backend.set(
            db=db_session,
            cache_key=f"translation:zh:en:mt:key{i}",
            ttl=3600,
            text=f"Text {i}",
            source_lang="zh",
            target_lang="en",
            translated_text=f"Translated {i}",
            source="MACHINE"
        )
    
    # Verify they exist by checking stats
    before_stats = await sqlite_backend.stats(db=db_session)
    assert before_stats["total_cached"] == 5
    
    # Clear all
    clear_success = await sqlite_backend.clear_all(db=db_session)
    assert clear_success is True
    
    # Verify all are gone
    after_stats = await sqlite_backend.stats(db=db_session)
    assert after_stats["total_cached"] == 0


@pytest.mark.asyncio
async def test_is_available_returns_true(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that is_available correctly reports database availability."""
    result = await sqlite_backend.is_available(db=db_session)
    assert result is True


@pytest.mark.asyncio
async def test_metadata_none_handled(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that None metadata is handled correctly."""
    cache_key = "translation:zh:en:mt:metanone"
    
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="测试元数据",
        source_lang="zh",
        target_lang="en",
        translated_text="Test Metadata None",
        source="MACHINE",
        metadata=None
    )
    
    result = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    data = json.loads(result)
    assert data["metadata"] == {}


@pytest.mark.asyncio
async def test_confidence_none_handled(sqlite_backend: SQLiteCacheBackend, db_session: AsyncSession):
    """Test that None confidence is handled correctly."""
    cache_key = "translation:zh:en:mt:confnone"
    
    await sqlite_backend.set(
        db=db_session,
        cache_key=cache_key,
        ttl=3600,
        text="测试置信度",
        source_lang="zh",
        target_lang="en",
        translated_text="Test Confidence None",
        source="MACHINE",
        confidence=None
    )
    
    result = await sqlite_backend.get(db=db_session, cache_key=cache_key)
    data = json.loads(result)
    assert data["confidence"] is None
