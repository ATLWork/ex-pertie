"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.user import User, UserStatus
from app.models.role import Role, Permission
from tests.conftest import get_auth_headers


class TestAuthRegister:
    """Tests for user registration."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "NewUser123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["username"] == "newuser"
        assert "hashed_password" not in data["data"]

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "AnotherUser123",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["message"]

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with duplicate username."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "another@example.com",
                "username": test_user.username,
                "password": "AnotherUser123",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["message"]

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        # Password without uppercase
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "weakpassword1",
            },
        )
        assert response.status_code == 422

        # Password without digit
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "WeakPassword",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "TestUser123",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "Test123456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["username"] == test_user.username

    def test_login_with_email(self, client: TestClient, test_user: User):
        """Test login with email instead of username."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.email,
                "password": "Test123456",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123",
            },
        )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for current user endpoints."""

    def test_get_current_user_success(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test getting current user info."""
        headers = get_auth_headers(test_user)
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["username"] == test_user.username
        assert data["data"]["email"] == test_user.email

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_update_current_user(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test updating current user info."""
        headers = get_auth_headers(test_user)
        response = client.put(
            "/api/v1/auth/me",
            headers=headers,
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["full_name"] == "Updated Name"


class TestAuthRoles:
    """Tests for role management."""

    def test_create_role_as_admin(
        self, client: TestClient, test_superuser: User, db_session
    ):
        """Test creating role as admin."""
        headers = get_auth_headers(test_superuser)
        response = client.post(
            "/api/v1/auth/roles",
            headers=headers,
            json={
                "name": "new_role",
                "display_name": "New Role",
                "description": "A new role",
                "permissions": ["hotel:read"],
            },
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "new_role"

    def test_create_role_as_non_admin(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test creating role as non-admin (should fail)."""
        headers = get_auth_headers(test_user)
        response = client.post(
            "/api/v1/auth/roles",
            headers=headers,
            json={
                "name": "another_role",
                "display_name": "Another Role",
                "permissions": ["hotel:read"],
            },
        )
        assert response.status_code == 403

    def test_list_roles(self, client: TestClient, test_user: User, default_roles):
        """Test listing roles."""
        headers = get_auth_headers(test_user)
        response = client.get("/api/v1/auth/roles", headers=headers)
        assert response.status_code == 200
        roles = response.json()["data"]
        assert len(roles) >= 3  # admin, operator, viewer


class TestPasswordChange:
    """Tests for password change."""

    def test_change_password_success(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test successful password change."""
        headers = get_auth_headers(test_user)
        response = client.put(
            "/api/v1/auth/me/password",
            headers=headers,
            json={
                "current_password": "Test123456",
                "new_password": "NewTest123456",
            },
        )
        assert response.status_code == 200

        # Verify can login with new password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "NewTest123456",
            },
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test password change with wrong current password."""
        headers = get_auth_headers(test_user)
        response = client.put(
            "/api/v1/auth/me/password",
            headers=headers,
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewTest123456",
            },
        )
        assert response.status_code == 400
