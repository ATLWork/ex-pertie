"""
Pytest configuration and fixtures for Ex-pertie Backend API E2E tests.
"""

import os
import time
from typing import Generator

import pytest
import requests


class TestConfig:
    """Test configuration."""

    BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_PREFIX: str = "/api/v1"

    TEST_USER: dict = {
        "username": "test_user",
        "password": "Test1234",
        "email": "test@example.com",
    }

    ADMIN_USER: dict = {
        "username": "admin",
        "password": "Admin1234",
        "email": "admin@example.com",
    }

    TEST_HOTEL: dict = {
        "name_cn": "测试酒店",
        "brand": "atour",
        "province": "上海市",
        "city": "上海市",
        "address_cn": "浦东新区世纪大道100号",
    }

    TEST_TRANSLATION: dict = {
        "text": "酒店提供免费WiFi和停车场",
        "source_lang": "zh-CN",
        "target_lang": "en-US",
    }

    @property
    def api_url(self) -> str:
        return f"{self.BASE_URL}{self.API_PREFIX}"


config = TestConfig()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return config.BASE_URL


@pytest.fixture(scope="session")
def api_url() -> str:
    return config.api_url


@pytest.fixture(scope="session")
def http_client() -> Generator[requests.Session, None, None]:
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    yield session
    session.close()


@pytest.fixture(scope="function")
def auth_headers(http_client: requests.Session, api_url: str) -> dict:
    login_data = {
        "username": config.TEST_USER["username"],
        "password": config.TEST_USER["password"],
    }

    response = http_client.post(f"{api_url}/auth/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}

    register_data = {
        "username": config.TEST_USER["username"],
        "password": config.TEST_USER["password"],
        "email": config.TEST_USER["email"],
    }
    http_client.post(f"{api_url}/auth/register", json=register_data)
    login_response = http_client.post(f"{api_url}/auth/login", json=login_data)

    if login_response.status_code == 200:
        data = login_response.json()
        token = data.get("data", {}).get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}

    pytest.fail("Failed to authenticate")


@pytest.fixture(scope="function")
def admin_auth_headers(http_client: requests.Session, api_url: str) -> dict:
    login_data = {
        "username": config.ADMIN_USER["username"],
        "password": config.ADMIN_USER["password"],
    }

    response = http_client.post(f"{api_url}/auth/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}

    register_data = {
        "username": config.ADMIN_USER["username"],
        "password": config.ADMIN_USER["password"],
        "email": config.ADMIN_USER["email"],
    }
    http_client.post(f"{api_url}/auth/register", json=register_data)
    login_response = http_client.post(f"{api_url}/auth/login", json=login_data)

    if login_response.status_code == 200:
        data = login_response.json()
        token = data.get("data", {}).get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}

    pytest.fail("Failed to authenticate as admin")


@pytest.fixture(scope="function")
def unique_username() -> str:
    return f"user_{int(time.time() * 1000)}"


@pytest.fixture(scope="function")
def unique_email() -> str:
    return f"user_{int(time.time() * 1000)}@example.com"


@pytest.fixture(scope="function")
def test_hotel_data() -> dict:
    return {
        "name_cn": f"测试酒店_{int(time.time() * 1000)}",
        "brand": "atour",
        "province": "上海市",
        "city": "上海市",
        "address_cn": "浦东新区世纪大道100号",
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "auth: authentication related tests")
    config.addinivalue_line("markers", "hotels: hotel management tests")
    config.addinivalue_line("markers", "imports: data import tests")
    config.addinivalue_line("markers", "exports: data export tests")
    config.addinivalue_line("markers", "translation: translation feature tests")
    config.addinivalue_line("markers", "users: user management tests")
    config.addinivalue_line("markers", "smoke: smoke tests")
    config.addinivalue_line("markers", "regression: regression tests")
