"""
Tests for translation module.

Implements T035: Translation Module Unit Tests
"""

import json
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from app.schemas.translation import TranslationSource
from app.services.translation.ai_client import DeepSeekClient
from app.services.translation.cache_service import TranslationCacheService
from app.services.translation.orchestrator import TranslationOrchestrator
from app.services.translation.tencent_client import TencentTranslateClient


# ============================================================================
# Tencent Client Tests
# ============================================================================


class TestTencentTranslateClient:
    """Tests for TencentTranslateClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return TencentTranslateClient(
            secret_id="test_id",
            secret_key="test_key",
            region="ap-shanghai",
        )

    def test_normalize_language_code(self, client):
        """Test language code normalization."""
        assert client._normalize_language_code("zh") == "zh"
        assert client._normalize_language_code("ZH") == "zh"
        assert client._normalize_language_code("zh-cn") == "zh"
        assert client._normalize_language_code("en") == "en"
        assert client._normalize_language_code("ja") == "jp"
        assert client._normalize_language_code("unknown") == "unknown"

    def test_generate_signature(self, client):
        """Test signature generation."""
        payload = '{"test": "data"}'
        timestamp = 1700000000
        signature = client._generate_signature(payload, timestamp)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length
        assert isinstance(signature, str)

    def test_build_headers(self, client):
        """Test header building."""
        payload = '{"test": "data"}'
        headers = client._build_headers(payload)

        assert headers["Content-Type"] == "application/json"
        assert headers["Host"] == TencentTranslateClient.HOST
        assert headers["X-TC-Action"] == "TextTranslate"
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("TC3-HMAC-SHA256")

    def test_parse_response_success(self, client):
        """Test successful response parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Response": {
                "TargetText": "Deluxe King Room",
                "Source": "zh",
                "Target": "en",
                "RequestId": "test-request-id",
            }
        }

        result = client._parse_response(mock_response, "豪华大床房")

        assert result["translated_text"] == "Deluxe King Room"
        assert result["source"] == "zh"
        assert result["target"] == "en"
        assert result["request_id"] == "test-request-id"

    def test_parse_response_error(self, client):
        """Test error response parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "Response": {
                "Error": {
                    "Code": "InvalidParameter",
                    "Message": "Invalid parameter value",
                },
                "RequestId": "test-request-id",
            }
        }

        from app.middleware.exception import ExternalAPIError

        with pytest.raises(ExternalAPIError) as exc_info:
            client._parse_response(mock_response, "test")

        assert "Invalid parameter" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_translate_missing_credentials(self):
        """Test translation with missing credentials."""
        client = TencentTranslateClient(secret_id="", secret_key="")

        from app.middleware.exception import ExternalAPIError

        with pytest.raises(ExternalAPIError) as exc_info:
            await client.translate("test", "zh", "en")

        assert "credentials not configured" in str(exc_info.value)


# ============================================================================
# DeepSeek Client Tests
# ============================================================================


class TestDeepSeekClient:
    """Tests for DeepSeekClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return DeepSeekClient(
            api_key="test-api-key",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        )

    def test_build_translation_prompt(self, client):
        """Test prompt building."""
        prompt = client.build_translation_prompt(
            original_text="豪华大床房",
            machine_translation="Deluxe King Room",
            source_lang="zh",
            target_lang="en",
            context="hotel room type",
        )

        assert "豪华大床房" in prompt
        assert "Deluxe King Room" in prompt
        assert "zh" in prompt
        assert "en" in prompt
        assert "hotel room type" in prompt
        assert "JSON" in prompt

    def test_extract_json_from_markdown(self, client):
        """Test JSON extraction from markdown."""
        content = '''```json
{"enhanced_translation": "Grand Deluxe King Room", "changes": "Added 'Grand' for premium feel"}
```'''

        result = client._extract_json(content)
        assert result is not None

        parsed = json.loads(result)
        assert parsed["enhanced_translation"] == "Grand Deluxe King Room"

    def test_extract_json_raw(self, client):
        """Test JSON extraction from raw text."""
        content = 'Some text before {"enhanced_translation": "Test", "changes": "None"} some text after'

        result = client._extract_json(content)
        assert result is not None

        parsed = json.loads(result)
        assert parsed["enhanced_translation"] == "Test"

    def test_parse_enhancement_response_success(self, client):
        """Test successful enhancement response parsing."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"enhanced_translation": "Enhanced text", "changes": "Improved clarity"}'
                    }
                }
            ]
        }

        result = client._parse_enhancement_response(api_response, "fallback")

        assert result["enhanced_text"] == "Enhanced text"
        assert result["changes"] == "Improved clarity"
        assert result["raw_response"] == api_response

    def test_parse_enhancement_response_fallback(self, client):
        """Test enhancement response parsing with fallback."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": ""
                    }
                }
            ]
        }

        result = client._parse_enhancement_response(api_response, "fallback text")

        assert result["enhanced_text"] == "fallback text"
        assert "Empty" in result["changes"]

    def test_handle_api_response_error(self, client):
        """Test API error response handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key"
            }
        }

        from app.middleware.exception import ExternalAPIError

        with pytest.raises(ExternalAPIError) as exc_info:
            client._handle_api_response(mock_response)

        assert "Invalid API key" in str(exc_info.value)


# ============================================================================
# Cache Service Tests
# ============================================================================


class TestTranslationCacheService:
    """Tests for TranslationCacheService."""

    @pytest.fixture
    def cache_service(self):
        """Create a test cache service instance."""
        return TranslationCacheService(ttl=3600)

    def test_generate_cache_key(self, cache_service):
        """Test cache key generation."""
        key1 = cache_service._generate_cache_key(
            text="豪华大床房",
            source_lang="zh",
            target_lang="en",
            use_ai_enhance=True,
        )
        key2 = cache_service._generate_cache_key(
            text="豪华大床房",
            source_lang="zh",
            target_lang="en",
            use_ai_enhance=False,
        )
        key3 = cache_service._generate_cache_key(
            text="豪华大床房",
            source_lang="zh",
            target_lang="en",
            use_ai_enhance=True,
        )

        assert key1.startswith("translation:")
        assert key1 != key2  # Different enhancement flag should produce different key
        assert key1 == key3  # Same parameters should produce same key

    def test_serialize_cache_value(self, cache_service):
        """Test cache value serialization."""
        value = cache_service._serialize_cache_value(
            translated_text="Deluxe King Room",
            source=TranslationSource.AI_ENHANCED,
            original_text="豪华大床房",
            confidence=0.95,
            metadata={"model": "deepseek-chat"},
        )

        assert isinstance(value, str)
        parsed = json.loads(value)
        assert parsed["translated_text"] == "Deluxe King Room"
        assert parsed["source"] == "ai_enhanced"
        assert parsed["original_text"] == "豪华大床房"
        assert parsed["confidence"] == 0.95

    def test_deserialize_cache_value(self, cache_service):
        """Test cache value deserialization."""
        serialized = '{"translated_text": "Test", "source": "machine", "original_text": "测试"}'
        result = cache_service._deserialize_cache_value(serialized)

        assert result is not None
        assert result["translated_text"] == "Test"
        assert result["source"] == "machine"

    def test_deserialize_cache_value_invalid(self, cache_service):
        """Test deserialization with invalid JSON."""
        result = cache_service._deserialize_cache_value("invalid json")
        assert result is None


# ============================================================================
# Orchestrator Tests
# ============================================================================


class TestTranslationOrchestrator:
    """Tests for TranslationOrchestrator."""

    @pytest.fixture
    def mock_tencent_client(self):
        """Create mock Tencent client."""
        client = MagicMock(spec=TencentTranslateClient)
        client.secret_id = "test"
        client.secret_key = "test"
        client.translate = AsyncMock(return_value={
            "translated_text": "Deluxe King Room",
            "source": "zh",
            "target": "en",
            "request_id": "test-id",
        })
        client.batch_translate = AsyncMock(return_value=[
            {"translated_text": "Room 1", "source": "zh", "target": "en"},
            {"translated_text": "Room 2", "source": "zh", "target": "en"},
        ])
        return client

    @pytest.fixture
    def mock_ai_client(self):
        """Create mock AI client."""
        client = MagicMock(spec=DeepSeekClient)
        client.enhance_translation = AsyncMock(return_value={
            "enhanced_text": "Grand Deluxe King Room",
            "changes": "Enhanced for premium appeal",
        })
        return client

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service."""
        service = MagicMock(spec=TranslationCacheService)
        service.get = AsyncMock(return_value=None)
        service.set = AsyncMock(return_value=True)
        service.get_batch = AsyncMock(return_value={})
        service.set_batch = AsyncMock(return_value=2)
        return service

    @pytest.fixture
    def orchestrator(self, mock_tencent_client, mock_ai_client, mock_cache_service):
        """Create orchestrator with mocked dependencies."""
        return TranslationOrchestrator(
            tencent_client=mock_tencent_client,
            ai_client=mock_ai_client,
            cache_service=mock_cache_service,
        )

    @pytest.mark.asyncio
    async def test_translate_with_cache_hit(self, mock_cache_service):
        """Test translation with cache hit."""
        mock_cache_service.get = AsyncMock(return_value={
            "translated_text": "Cached Translation",
            "source": "ai_enhanced",
            "confidence": 0.9,
        })

        orchestrator = TranslationOrchestrator(
            tencent_client=MagicMock(),
            ai_client=MagicMock(),
            cache_service=mock_cache_service,
        )

        result = await orchestrator.translate(
            text="测试文本",
            source_lang="zh",
            target_lang="en",
            use_cache=True,
        )

        assert result.translated_text == "Cached Translation"
        assert result.source == TranslationSource.CACHE
        assert result.cached is True

    @pytest.mark.asyncio
    async def test_translate_without_cache(self, orchestrator):
        """Test translation without cache."""
        result = await orchestrator.translate(
            text="豪华大床房",
            source_lang="zh",
            target_lang="en",
            use_cache=True,
            use_ai_enhance=True,
        )

        assert result.translated_text == "Grand Deluxe King Room"
        assert result.source == TranslationSource.AI_ENHANCED
        assert result.cached is False

    @pytest.mark.asyncio
    async def test_translate_machine_only(self, mock_tencent_client, mock_cache_service):
        """Test translation without AI enhancement."""
        orchestrator = TranslationOrchestrator(
            tencent_client=mock_tencent_client,
            ai_client=MagicMock(),
            cache_service=mock_cache_service,
        )

        result = await orchestrator.translate(
            text="豪华大床房",
            source_lang="zh",
            target_lang="en",
            use_cache=True,
            use_ai_enhance=False,
        )

        assert result.translated_text == "Deluxe King Room"
        assert result.source == TranslationSource.MACHINE

    @pytest.mark.asyncio
    async def test_batch_translate(self, orchestrator):
        """Test batch translation."""
        result = await orchestrator.batch_translate(
            texts=["房间1", "房间2"],
            source_lang="zh",
            target_lang="en",
            use_cache=True,
        )

        assert result.total == 2
        assert len(result.results) == 2
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test health check."""
        # Add health check method to mock cache service
        orchestrator.cache_service.get_stats = AsyncMock(return_value={"total_cached": 10})

        status = await orchestrator.health_check()

        assert status["orchestrator"] == "healthy"
        assert "tencent" in status
        assert "ai" in status
        assert "cache" in status


# ============================================================================
# Integration Tests (require running services)
# ============================================================================


@pytest.mark.integration
class TestTranslationIntegration:
    """Integration tests for translation services."""

    @pytest.mark.asyncio
    async def test_full_translation_workflow(self):
        """
        Test full translation workflow with real services.

        This test requires:
        - Redis running
        - Tencent Cloud credentials configured
        - DeepSeek API key configured

        Run with: pytest -m integration
        """
        pytest.skip("Integration test - requires running services")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_translation_request():
    """Sample translation request data."""
    return {
        "text": "豪华海景套房",
        "source_lang": "zh",
        "target_lang": "en",
        "use_cache": True,
        "use_ai_enhance": True,
        "context": "hotel room type",
    }


@pytest.fixture
def sample_batch_request():
    """Sample batch translation request data."""
    return {
        "texts": ["标准间", "大床房", "套房", "海景房"],
        "source_lang": "zh",
        "target_lang": "en",
        "use_cache": True,
        "use_ai_enhance": True,
    }
