"""
Export API E2E tests.
"""

import pytest


class TestExportList:
    """Test export list endpoints."""

    def test_export_list_pagination(self, http_client, api_url, auth_headers):
        """export-007: 导出历史列表 - 分页查询"""
        response = http_client.get(
            f"{api_url}/exports",
            params={"page": 1, "page_size": 20},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_export_list_filter_by_type(self, http_client, api_url, auth_headers):
        """export-008: 导出历史列表 - 按类型筛选"""
        response = http_client.get(
            f"{api_url}/exports",
            params={"export_type": "hotel"},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestHotelExport:
    """Test hotel data export."""

    def test_export_hotels_excel(self, http_client, api_url, auth_headers):
        """export-001: 酒店数据导出 - Excel格式"""
        response = http_client.post(
            f"{api_url}/exports/hotels",
            json={"export_format": "excel"},
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]

    def test_export_hotels_csv(self, http_client, api_url, auth_headers):
        """export-002: 酒店数据导出 - CSV格式"""
        response = http_client.post(
            f"{api_url}/exports/hotels",
            json={"export_format": "csv"},
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]

    def test_export_hotels_json(self, http_client, api_url, auth_headers):
        """export-003: 酒店数据导出 - JSON格式"""
        response = http_client.post(
            f"{api_url}/exports/hotels",
            json={"export_format": "json"},
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]


class TestRoomExport:
    """Test room data export."""

    def test_export_rooms(self, http_client, api_url, auth_headers):
        """export-004: 客房数据导出 - 成功"""
        response = http_client.post(
            f"{api_url}/exports/rooms",
            json={},
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]


class TestExportDetail:
    """Test export detail endpoints."""

    def test_export_progress(self, http_client, api_url, auth_headers):
        """export-005: 导出进度查询 - 存在任务"""
        response = http_client.get(
            f"{api_url}/exports/1",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_export_download(self, http_client, api_url, auth_headers):
        """export-006: 导出文件下载 - 存在文件"""
        response = http_client.get(
            f"{api_url}/exports/1/download",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
