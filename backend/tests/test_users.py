"""
Tests for user management endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User, UserStatus
from app.models.role import Role
from tests.conftest import get_auth_headers


class TestUserList:
    """Tests for user listing."""

    def test_list_users_success(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test listing users."""
        headers = get_auth_headers(test_user)
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]

    def test_list_users_pagination(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test user listing pagination."""
        headers = get_auth_headers(test_user)
        response = client.get(
            "/api/v1/users?page=1&page_size=10", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 10

    def test_list_users_search(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test user search."""
        headers = get_auth_headers(test_user)
        response = client.get(
            f"/api/v1/users?search={test_user.username}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 1

    def test_list_users_unauthorized(self, client: TestClient):
        """Test listing users without authentication."""
        response = client.get("/api/v1/users")
        assert response.status_code == 401


class TestUserGet:
    """Tests for getting user info."""

    def test_get_user_by_id(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test getting user by ID."""
        headers = get_auth_headers(test_user)
        response = client.get(f"/api/v1/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == test_user.id
        assert data["data"]["username"] == test_user.username

    def test_get_nonexistent_user(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test getting nonexistent user."""
        headers = get_auth_headers(test_user)
        response = client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert response.status_code == 404

    def test_get_my_profile(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test getting own profile."""
        headers = get_auth_headers(test_user)
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["username"] == test_user.username


class TestUserActivation:
    """Tests for user activation/deactivation."""

    def test_activate_user_as_admin(
        self, client: TestClient, test_superuser: User, test_user: User, db_session
    ):
        """Test activating user as admin."""
        # First deactivate
        test_user.status = UserStatus.INACTIVE
        db_session.add(test_user)
        db_session.flush()

        headers = get_auth_headers(test_superuser)
        response = client.post(
            f"/api/v1/users/{test_user.id}/activate", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "active"

    def test_deactivate_user_as_admin(
        self, client: TestClient, test_superuser: User, test_user: User, db_session
    ):
        """Test deactivating user as admin."""
        headers = get_auth_headers(test_superuser)
        response = client.post(
            f"/api/v1/users/{test_user.id}/deactivate", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "inactive"

    def test_activate_user_as_non_admin(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test activating user as non-admin (should fail)."""
        # Create another user to activate
        another_user = User(
            email="another@example.com",
            username="anotheruser",
            hashed_password="hashed",
            status=UserStatus.INACTIVE,
        )
        db_session.add(another_user)
        db_session.flush()

        headers = get_auth_headers(test_user)
        response = client.post(
            f"/api/v1/users/{another_user.id}/activate", headers=headers
        )
        assert response.status_code == 403


class TestUserRoleAssignment:
    """Tests for role assignment."""

    def test_assign_role_as_admin(
        self,
        client: TestClient,
        test_superuser: User,
        test_user: User,
        test_role: Role,
        db_session,
    ):
        """Test assigning role to user as admin."""
        headers = get_auth_headers(test_superuser)
        response = client.post(
            f"/api/v1/users/{test_user.id}/roles/{test_role.id}", headers=headers
        )
        assert response.status_code == 200
        roles = response.json()["data"]["roles"]
        assert any(r["id"] == test_role.id for r in roles)

    def test_remove_role_as_admin(
        self,
        client: TestClient,
        test_superuser: User,
        test_user: User,
        test_role: Role,
        db_session,
    ):
        """Test removing role from user as admin."""
        # First assign the role
        test_user.roles.append(test_role)
        db_session.flush()

        headers = get_auth_headers(test_superuser)
        response = client.delete(
            f"/api/v1/users/{test_user.id}/roles/{test_role.id}", headers=headers
        )
        assert response.status_code == 200
        roles = response.json()["data"]["roles"]
        assert not any(r["id"] == test_role.id for r in roles)

    def test_assign_role_as_non_admin(
        self,
        client: TestClient,
        test_user: User,
        test_role: Role,
        db_session,
    ):
        """Test assigning role as non-admin (should fail)."""
        headers = get_auth_headers(test_user)
        response = client.post(
            f"/api/v1/users/{test_user.id}/roles/{test_role.id}", headers=headers
        )
        assert response.status_code == 403
