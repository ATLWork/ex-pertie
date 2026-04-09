"""
Hotel Management API E2E tests.
"""

import pytest


class TestHotelList:
    """Test hotel list endpoints."""

    def test_hotel_list_default_pagination(self, http_client, api_url, auth_headers):
        """hotel-001: 酒店列表查询 - 默认分页"""
        response = http_client.get(
            f"{api_url}/hotels",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "list" in data

    def test_hotel_list_custom_pagination(self, http_client, api_url, auth_headers):
        """hotel-002: 酒店列表查询 - 自定义分页"""
        response = http_client.get(
            f"{api_url}/hotels",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_hotel_list_filter_by_city(self, http_client, api_url, auth_headers):
        """hotel-003: 酒店列表查询 - 按城市筛选"""
        response = http_client.get(
            f"{api_url}/hotels",
            params={"city": "上海市"},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_hotel_list_filter_by_brand(self, http_client, api_url, auth_headers):
        """hotel-004: 酒店列表查询 - 按品牌筛选"""
        response = http_client.get(
            f"{api_url}/hotels",
            params={"brand": "atour"},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_hotel_list_filter_by_status(self, http_client, api_url, auth_headers):
        """hotel-005: 酒店列表查询 - 按状态筛选"""
        response = http_client.get(
            f"{api_url}/hotels",
            params={"status": "active"},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestHotelSearch:
    """Test hotel search endpoints."""

    def test_hotel_search_by_name(self, http_client, api_url, auth_headers):
        """hotel-006: 酒店搜索 - 按名称模糊搜索"""
        response = http_client.get(
            f"{api_url}/hotels/search",
            params={"keyword": "酒店"},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestHotelCRUD:
    """Test hotel CRUD operations."""

    def test_create_hotel_success(self, http_client, api_url, auth_headers, test_hotel_data):
        """hotel-007: 创建酒店 - 必填字段完整"""
        response = http_client.post(
            f"{api_url}/hotels",
            json=test_hotel_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data.get("id") is not None or data.get("data", {}).get("id") is not None

    def test_create_hotel_missing_fields(self, http_client, api_url, auth_headers):
        """hotel-008: 创建酒店 - 缺少必填字段"""
        response = http_client.post(
            f"{api_url}/hotels",
            json={"name_cn": "测试"},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_update_hotel(self, http_client, api_url, auth_headers, test_hotel_data):
        """hotel-009: 更新酒店 - 部分字段更新"""
        # Create hotel first
        create_response = http_client.post(
            f"{api_url}/hotels",
            json=test_hotel_data,
            headers=auth_headers
        )

        if create_response.status_code == 201:
            data = create_response.json()
            hotel_id = data.get("id") or data.get("data", {}).get("id")

            if hotel_id:
                update_data = {"name_cn": "更新后的酒店名称"}
                update_response = http_client.put(
                    f"{api_url}/hotels/{hotel_id}",
                    json=update_data,
                    headers=auth_headers
                )
                assert update_response.status_code == 200

    def test_delete_hotel(self, http_client, api_url, auth_headers, test_hotel_data):
        """hotel-010: 删除酒店 - 存在酒店删除"""
        # Create hotel first
        create_response = http_client.post(
            f"{api_url}/hotels",
            json=test_hotel_data,
            headers=auth_headers
        )

        if create_response.status_code == 201:
            data = create_response.json()
            hotel_id = data.get("id") or data.get("data", {}).get("id")

            if hotel_id:
                delete_response = http_client.delete(
                    f"{api_url}/hotels/{hotel_id}",
                    headers=auth_headers
                )
                assert delete_response.status_code == 200

    def test_get_hotel_detail(self, http_client, api_url, auth_headers, test_hotel_data):
        """hotel-011: 获取酒店详情 - 存在ID"""
        # Create hotel first
        create_response = http_client.post(
            f"{api_url}/hotels",
            json=test_hotel_data,
            headers=auth_headers
        )

        if create_response.status_code == 201:
            data = create_response.json()
            hotel_id = data.get("id") or data.get("data", {}).get("id")

            if hotel_id:
                get_response = http_client.get(
                    f"{api_url}/hotels/{hotel_id}",
                    headers=auth_headers
                )
                assert get_response.status_code == 200

    def test_get_hotel_detail_not_found(self, http_client, api_url, auth_headers):
        """hotel-012: 获取酒店详情 - 不存在ID"""
        response = http_client.get(
            f"{api_url}/hotels/nonexistent_id_xyz",
            headers=auth_headers
        )

        assert response.status_code in [404, 422]
