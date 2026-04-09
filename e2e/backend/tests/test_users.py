"""
User Management API E2E tests.
"""

import pytest


class TestUserList:
    """Test user list endpoints."""

    def test_user_list_default_pagination(self, http_client, api_url, admin_auth_headers):
        """user-001: 用户列表查询 - 默认分页"""
        response = http_client.get(
            f"{api_url}/users",
            headers=admin_auth_headers
        )

        assert response.status_code == 200

    def test_user_list_search(self, http_client, api_url, admin_auth_headers):
        """user-002: 用户列表查询 - 搜索用户"""
        response = http_client.get(
            f"{api_url}/users",
            params={"search": "admin"},
            headers=admin_auth_headers
        )

        assert response.status_code == 200


class TestUserDetail:
    """Test user detail endpoints."""

    def test_get_user_detail(self, http_client, api_url, admin_auth_headers):
        """user-003: 获取用户详情 - 存在用户"""
        response = http_client.get(
            f"{api_url}/users/me",
            headers=admin_auth_headers
        )

        assert response.status_code == 200


class TestUserStatus:
    """Test user status management."""

    def test_user_activate(self, http_client, api_url, admin_auth_headers, unique_username, unique_email):
        """user-004: 用户激活"""
        # Create user first
        register_data = {
            "username": unique_username,
            "password": "Test1234",
            "email": unique_email,
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        # Get user list to find user_id
        list_response = http_client.get(
            f"{api_url}/users",
            params={"search": unique_username},
            headers=admin_auth_headers
        )

        if list_response.status_code == 200:
            data = list_response.json()
            users = data.get("data", {}).get("list", []) or data.get("list", [])
            if users:
                user_id = users[0].get("id")
                if user_id:
                    activate_response = http_client.post(
                        f"{api_url}/users/{user_id}/activate",
                        headers=admin_auth_headers
                    )
                    assert activate_response.status_code == 200

    def test_user_deactivate(self, http_client, api_url, admin_auth_headers, unique_username, unique_email):
        """user-005: 用户停用"""
        # Create user first
        register_data = {
            "username": unique_username,
            "password": "Test1234",
            "email": unique_email,
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        # Get user list to find user_id
        list_response = http_client.get(
            f"{api_url}/users",
            params={"search": unique_username},
            headers=admin_auth_headers
        )

        if list_response.status_code == 200:
            data = list_response.json()
            users = data.get("data", {}).get("list", []) or data.get("list", [])
            if users:
                user_id = users[0].get("id")
                if user_id:
                    deactivate_response = http_client.post(
                        f"{api_url}/users/{user_id}/deactivate",
                        headers=admin_auth_headers
                    )
                    assert deactivate_response.status_code == 200


class TestUserRoles:
    """Test user role management."""

    def test_assign_role(self, http_client, api_url, admin_auth_headers, unique_username, unique_email):
        """user-006: 角色分配"""
        # Create user first
        register_data = {
            "username": unique_username,
            "password": "Test1234",
            "email": unique_email,
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        # Get user list to find user_id
        list_response = http_client.get(
            f"{api_url}/users",
            params={"search": unique_username},
            headers=admin_auth_headers
        )

        # Get roles to find role_id
        roles_response = http_client.get(
            f"{api_url}/auth/roles",
            headers=admin_auth_headers
        )

        if list_response.status_code == 200 and roles_response.status_code == 200:
            users = list_response.json().get("data", {}).get("list", []) or []
            roles = roles_response.json().get("data", {}).get("list", []) or []

            if users and roles:
                user_id = users[0].get("id")
                role_id = roles[0].get("id")

                if user_id and role_id:
                    assign_response = http_client.post(
                        f"{api_url}/users/{user_id}/roles/{role_id}",
                        headers=admin_auth_headers
                    )
                    assert assign_response.status_code == 200

    def test_remove_role(self, http_client, api_url, admin_auth_headers, unique_username, unique_email):
        """user-007: 角色移除"""
        # Create user first
        register_data = {
            "username": unique_username,
            "password": "Test1234",
            "email": unique_email,
        }
        http_client.post(f"{api_url}/auth/register", json=register_data)

        # Get user list and roles
        list_response = http_client.get(
            f"{api_url}/users",
            params={"search": unique_username},
            headers=admin_auth_headers
        )
        roles_response = http_client.get(
            f"{api_url}/auth/roles",
            headers=admin_auth_headers
        )

        if list_response.status_code == 200 and roles_response.status_code == 200:
            users = list_response.json().get("data", {}).get("list", []) or []
            roles = roles_response.json().get("data", {}).get("list", []) or []

            if users and roles:
                user_id = users[0].get("id")
                role_id = roles[0].get("id")

                if user_id and role_id:
                    remove_response = http_client.delete(
                        f"{api_url}/users/{user_id}/roles/{role_id}",
                        headers=admin_auth_headers
                    )
                    assert remove_response.status_code == 200
