"""
Tests for health check endpoints.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint returns healthy status."""
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/api/v1/health/ready")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["status"] == "ready"
    assert "services" in data["data"]


def test_api_docs_available_in_debug(client: TestClient):
    """Test API documentation is available in debug mode."""
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK


def test_openapi_json_available(client: TestClient):
    """Test OpenAPI JSON is available."""
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
