"""
Translation API endpoint tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.translation import BatchTranslationResult, TranslationResult, TranslationSource


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = MagicMock()
    orchestrator.translate = AsyncMock(return_value=TranslationResult(
        original_text="豪华大床房",
        translated_text="Deluxe King Room",
        source_lang="zh",
        target_lang="en",
        source=TranslationSource.AI_ENHANCED,
        cached=False,
    ))
    orchestrator.batch_translate = AsyncMock(return_value=BatchTranslationResult(
        results=[
            TranslationResult(
                original_text="房间1",
                translated_text="Room 1",
                source_lang="zh",
                target_lang="en",
                source=TranslationSource.MACHINE,
                cached=False,
            ),
            TranslationResult(
                original_text="房间2",
                translated_text="Room 2",
                source_lang="zh",
                target_lang="en",
                source=TranslationSource.MACHINE,
                cached=False,
            ),
        ],
        total=2,
        cached_count=0,
        failed_count=0,
    ))
    orchestrator.health_check = AsyncMock(return_value={
        "orchestrator": "healthy",
        "tencent": "healthy",
        "ai": "configured",
        "cache": "healthy",
    })
    return orchestrator


class TestTranslationAPI:
    """Tests for Translation API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_translate_endpoint(self, client, mock_orchestrator):
        """Test single translation endpoint."""
        from app.api.v1.translation import get_translation_orchestrator

        app.dependency_overrides[get_translation_orchestrator] = lambda: mock_orchestrator
        try:
            response = client.post(
                "/api/v1/translation/translate",
                json={
                    "text": "豪华大床房",
                    "source_lang": "zh",
                    "target_lang": "en",
                    "use_cache": True,
                    "use_ai_enhance": True,
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["translated_text"] == "Deluxe King Room"
        assert data["data"]["source"] == "ai_enhanced"

    def test_translate_endpoint_validation_error(self, client):
        """Test translation endpoint with invalid input."""
        response = client.post(
            "/api/v1/translation/translate",
            json={
                "text": "",  # Empty text should fail validation
                "source_lang": "zh",
                "target_lang": "en",
            },
        )

        assert response.status_code == 422

    def test_translate_endpoint_text_too_long(self, client):
        """Test translation endpoint with text exceeding max length."""
        response = client.post(
            "/api/v1/translation/translate",
            json={
                "text": "x" * 5001,  # Exceeds max_length of 5000
                "source_lang": "zh",
                "target_lang": "en",
            },
        )

        assert response.status_code == 422

    def test_batch_translate_endpoint(self, client, mock_orchestrator):
        """Test batch translation endpoint."""
        from app.api.v1.translation import get_translation_orchestrator

        app.dependency_overrides[get_translation_orchestrator] = lambda: mock_orchestrator
        try:
            response = client.post(
                "/api/v1/translation/batch",
                json={
                    "texts": ["房间1", "房间2"],
                    "source_lang": "zh",
                    "target_lang": "en",
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 2
        assert len(data["data"]["results"]) == 2

    def test_batch_translate_too_many_texts(self, client):
        """Test batch translation with too many texts."""
        response = client.post(
            "/api/v1/translation/batch",
            json={
                "texts": ["text"] * 101,  # Exceeds max_length of 100
                "source_lang": "zh",
                "target_lang": "en",
            },
        )

        assert response.status_code == 422

    def test_health_check_endpoint(self, client, mock_orchestrator):
        """Test health check endpoint."""
        from app.api.v1.translation import get_translation_orchestrator

        app.dependency_overrides[get_translation_orchestrator] = lambda: mock_orchestrator
        try:
            response = client.get("/api/v1/translation/health")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["orchestrator"] == "healthy"

    def test_cache_stats_endpoint(self, client):
        """Test cache stats endpoint."""
        mock_stats = {"total_cached": 100, "ttl_seconds": 86400}

        with patch(
            "app.services.translation.get_cache_service"
        ) as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get_stats = AsyncMock(return_value=mock_stats)
            mock_get_cache.return_value = mock_cache

            response = client.get("/api/v1/translation/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_cached"] == 100

    def test_clear_cache_endpoint(self, client):
        """Test clear cache endpoint."""
        with patch(
            "app.services.translation.get_cache_service"
        ) as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.clear_all = AsyncMock(return_value=50)
            mock_get_cache.return_value = mock_cache

            response = client.delete("/api/v1/translation/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["deleted_count"] == 50


class TestTranslationAPIDocs:
    """Tests for API documentation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_openapi_schema_includes_translation(self, client):
        """Test that translation endpoints are in OpenAPI schema."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Check translation endpoints are documented
        paths = schema.get("paths", {})
        assert "/api/v1/translation/translate" in paths
        assert "/api/v1/translation/batch" in paths
        assert "/api/v1/translation/health" in paths
