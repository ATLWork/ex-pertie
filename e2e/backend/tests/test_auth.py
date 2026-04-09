"""
Authentication API E2E tests.
"""

import pytest


class TestAuthLogin:
    """Test auth login endpoints."""

    def test_login_success(self, http_client, api_url):
        """auth-001: 登录成功 - 正确用户名密码"""
        # First register
        register_data = {
            "username": "test_user_login",
            "password": "Test1234",
            "email": "test_login@example.com",
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        # Then login
        login_data = {
            "username": "test_user_login",
            "password": "Test1234",
        }
        response = http_client.post(f"{api_url}/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0 or data.get("access_token") is not None

    def test_login_fail_wrong_password(self, http_client, api_url):
        """auth-002: 登录失败 - 错误密码"""
        register_data = {
            "username": "test_user_wrong",
            "password": "Test1234",
            "email": "test_wrong@example.com",
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        login_data = {
            "username": "test_user_wrong",
            "password": "WrongPassword",
        }
        response = http_client.post(f"{api_url}/auth/login", json=login_data)

        assert response.status_code in [401, 422]

    def test_login_fail_nonexistent_user(self, http_client, api_url):
        """auth-003: 登录失败 - 不存在用户"""
        login_data = {
            "username": "nonexistent_user_xyz",
            "password": "Test1234",
        }
        response = http_client.post(f"{api_url}/auth/login", json=login_data)

        assert response.status_code in [401, 404, 422]


class TestAuthRegister:
    """Test auth register endpoints."""

    def test_register_success(self, http_client, api_url, unique_username, unique_email):
        """auth-004: 注册成功 - 符合密码规范"""
        register_data = {
            "username": unique_username,
            "password": "Test1234",
            "email": unique_email,
        }
        response = http_client.post(f"{api_url}/auth/register", json=register_data)

        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0 or data.get("message") == "success"

    def test_register_fail_no_uppercase(self, http_client, api_url, unique_username, unique_email):
        """auth-005: 注册失败 - 密码不含大写"""
        register_data = {
            "username": unique_username,
            "password": "test1234",
            "email": unique_email,
        }
        response = http_client.post(f"{api_url}/auth/register", json=register_data)

        assert response.status_code == 422

    def test_register_fail_no_digit(self, http_client, api_url, unique_username, unique_email):
        """auth-006: 注册失败 - 密码不含数字"""
        register_data = {
            "username": unique_username,
            "password": "TestPassword",
            "email": unique_email,
        }
        response = http_client.post(f"{api_url}/auth/register", json=register_data)

        assert response.status_code == 422

    def test_register_fail_short_password(self, http_client, api_url, unique_username, unique_email):
        """auth-007: 注册失败 - 密码少于8位"""
        register_data = {
            "username": unique_username,
            "password": "Test1",
            "email": unique_email,
        }
        response = http_client.post(f"{api_url}/auth/register", json=register_data)

        assert response.status_code == 422


class TestAuthToken:
    """Test token refresh and user info."""

    def test_token_refresh(self, http_client, api_url, auth_headers):
        """auth-008: Token刷新成功"""
        response = http_client.post(
            f"{api_url}/auth/refresh",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_get_current_user(self, http_client, api_url, auth_headers):
        """auth-009: 获取当前用户信息"""
        response = http_client.get(
            f"{api_url}/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "user" in data


class TestAuthRoles:
    """Test role management endpoints."""

    def test_list_roles(self, http_client, api_url, admin_auth_headers):
        """List roles - requires admin"""
        response = http_client.get(
            f"{api_url}/auth/roles",
            headers=admin_auth_headers
        )

        assert response.status_code == 200
