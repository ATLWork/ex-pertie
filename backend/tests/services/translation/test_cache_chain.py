"""
Unit tests for TranslationCacheService chain-of-responsibility behavior.
Tests the Redis → SQLite fallback chain with mocked backends.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest import MonkeyPatch

from app.schemas.translation import TranslationSource
from app.services.translation.cache_service import (
    TranslationCacheService,
    _RedisBackend,
    _SqliteBackend,
)


@pytest.fixture
def service() -> TranslationCacheService:
    """Create a TranslationCacheService with mocked backends."""
    svc = TranslationCacheService(ttl=3600)
    # Replace real backends with mocks
    svc._redis = MagicMock(spec=_RedisBackend)
    svc._redis.get = AsyncMock()
    svc._redis.set = AsyncMock(return_value=True)
    svc._redis.delete = AsyncMock(return_value=True)
    svc._redis.clear_all = AsyncMock(return_value=True)
    svc._redis.get_stats = AsyncMock(return_value={"total_cached": 5, "backend": "redis"})

    svc._sqlite = MagicMock(spec=_SqliteBackend)
    svc._sqlite.get = AsyncMock()
    svc._sqlite.set = AsyncMock(return_value=True)
    svc._sqlite.delete = AsyncMock(return_value=True)
    svc._sqlite.clear_all = AsyncMock(return_value=True)
    svc._sqlite.get_stats = AsyncMock(return_value={"total_cached": 3, "backend": "sqlite"})
    return svc


class TestGetChain:
    """Tests for the get() chain-of-responsibility."""

    @pytest.mark.asyncio
    async def test_redis_available_uses_redis(self, service: TranslationCacheService):
        """When redis returns a value, sqlite should NOT be called."""
        service._redis.get = AsyncMock(return_value='{"translated_text":"Hello","source":"machine","original_text":"你好","confidence":0.9}')

        result = await service.get(text="你好", source_lang="zh", target_lang="en")

        assert result is not None
        assert result["translated_text"] == "Hello"
        assert result["cached"] is True
        service._redis.get.assert_awaited_once()
        service._sqlite.get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_redis_unavailable_falls_to_sqlite(self, service: TranslationCacheService):
        """When redis returns None, it should fall back to sqlite."""
        service._redis.get = AsyncMock(return_value=None)
        service._sqlite.get = AsyncMock(return_value='{"translated_text":"Bonjour","source":"cache","original_text":"你好","confidence":0.85}')

        result = await service.get(text="你好", source_lang="zh", target_lang="fr")

        assert result is not None
        assert result["translated_text"] == "Bonjour"
        assert result["cached"] is True
        service._redis.get.assert_awaited_once()
        service._sqlite.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_both_unavailable_returns_none(self, service: TranslationCacheService):
        """When both backends return None, get() should return None."""
        service._redis.get = AsyncMock(return_value=None)
        service._sqlite.get = AsyncMock(return_value=None)

        result = await service.get(text="你好", source_lang="zh", target_lang="de")

        assert result is None
        service._redis.get.assert_awaited_once()
        service._sqlite.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_redis_exception_falls_to_sqlite(self, service: TranslationCacheService):
        """When redis raises an exception, it should fall back to sqlite."""
        service._redis.get = AsyncMock(side_effect=Exception("Redis connection lost"))
        service._sqlite.get = AsyncMock(return_value='{"translated_text":"Ciao","source":"cache","original_text":"你好","confidence":0.9}')

        result = await service.get(text="你好", source_lang="zh", target_lang="it")

        assert result is not None
        assert result["translated_text"] == "Ciao"
        service._redis.get.assert_awaited_once()
        service._sqlite.get.assert_awaited_once()


class TestSetChain:
    """Tests for the set() chain-of-responsibility."""

    @pytest.mark.asyncio
    async def test_set_only_writes_first_available(self, service: TranslationCacheService):
        """When redis succeeds, sqlite should NOT be called."""
        service._redis.set = AsyncMock(return_value=True)

        success = await service.set(
            text="你好",
            translated_text="Hello",
            source_lang="zh",
            target_lang="en",
            source=TranslationSource.MACHINE,
        )

        assert success is True
        service._redis.set.assert_awaited_once()
        service._sqlite.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_redis_fails_writes_sqlite(self, service: TranslationCacheService):
        """When redis fails, it should fall back to sqlite."""
        service._redis.set = AsyncMock(side_effect=Exception("Redis write failed"))
        service._sqlite.set = AsyncMock(return_value=True)

        success = await service.set(
            text="你好",
            translated_text="Hello",
            source_lang="zh",
            target_lang="en",
            source=TranslationSource.AI_ENHANCED,
        )

        assert success is True
        service._redis.set.assert_awaited_once()
        service._sqlite.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_both_fail_returns_false(self, service: TranslationCacheService):
        """When both backends fail, set() should return False."""
        service._redis.set = AsyncMock(side_effect=Exception("Redis write failed"))
        service._sqlite.set = AsyncMock(side_effect=Exception("SQLite write failed"))

        success = await service.set(
            text="你好",
            translated_text="Hello",
            source_lang="zh",
            target_lang="en",
            source=TranslationSource.MACHINE,
        )

        assert success is False
        service._redis.set.assert_awaited_once()
        service._sqlite.set.assert_awaited_once()


class TestDeleteChain:
    """Tests for the delete() chain-of-responsibility."""

    @pytest.mark.asyncio
    async def test_delete_falls_through(self, service: TranslationCacheService):
        """Delete should try redis first, then sqlite, and return True if either succeeds."""
        service._redis.delete = AsyncMock(return_value=True)

        success = await service.delete(text="你好", source_lang="zh", target_lang="en")

        assert success is True
        service._redis.delete.assert_awaited_once()
        service._sqlite.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_redis_fails_falls_to_sqlite(self, service: TranslationCacheService):
        """When redis delete fails, it should fall back to sqlite."""
        service._redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        service._sqlite.delete = AsyncMock(return_value=True)

        success = await service.delete(text="你好", source_lang="zh", target_lang="en")

        assert success is True
        service._redis.delete.assert_awaited_once()
        service._sqlite.delete.assert_awaited_once()


class TestActiveBackend:
    """Tests for the active_backend() method."""

    @pytest.mark.asyncio
    async def test_active_backend_returns_redis(self, service: TranslationCacheService):
        """When Redis is available, active_backend should return 'redis'."""
        with patch("app.services.translation.cache_service.RedisService.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_get_client.return_value = mock_client

            result = await service.active_backend()

            assert result == "redis"

    @pytest.mark.asyncio
    async def test_active_backend_returns_sqlite_when_redis_unavailable(
        self, service: TranslationCacheService
    ):
        """When Redis is unavailable but SQLite is available, return 'sqlite'."""
        # Mock redis to fail
        with patch("app.services.translation.cache_service.RedisService.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=Exception("Redis not available"))
            mock_get_client.return_value = mock_client

            # Mock sqlite to be available
            service._sqlite._backend = AsyncMock()
            service._sqlite._backend.is_available = AsyncMock(return_value=True)

            result = await service.active_backend()

            assert result == "sqlite"

    @pytest.mark.asyncio
    async def test_active_backend_returns_none(self, service: TranslationCacheService):
        """When both backends are unavailable, return 'none'."""
        with patch("app.services.translation.cache_service.RedisService.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=Exception("Redis not available"))
            mock_get_client.return_value = mock_client

            # Mock sqlite to also fail
            service._sqlite._backend = AsyncMock()
            service._sqlite._backend.is_available = AsyncMock(side_effect=Exception("DB not available"))

            result = await service.active_backend()

            assert result == "none"


class TestBatchOperations:
    """Tests for batch operations (get_batch, set_batch)."""

    @pytest.mark.asyncio
    async def test_get_batch_returns_correct_count(self, service: TranslationCacheService):
        """get_batch should return results for each text."""
        service._redis.get = AsyncMock(return_value='{"translated_text":"Hello","source":"machine","original_text":"你好","confidence":0.9}')

        texts = ["你好", "世界", "测试"]
        results = await service.get_batch(texts, source_lang="zh", target_lang="en")

        assert len(results) == 3
        assert all(v is not None for v in results.values())

    @pytest.mark.asyncio
    async def test_set_batch_counts_successes(self, service: TranslationCacheService):
        """set_batch should count the number of successful writes."""
        service._redis.set = AsyncMock(return_value=True)

        items = [
            {"text": "你好", "translated_text": "Hello", "source": TranslationSource.MACHINE},
            {"text": "世界", "translated_text": "World", "source": TranslationSource.MACHINE},
        ]
        count = await service.set_batch(items, source_lang="zh", target_lang="en")

        assert count == 2
        assert service._redis.set.await_count == 2