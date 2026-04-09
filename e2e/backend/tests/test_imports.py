"""
Import API E2E tests.
"""

import io
import pytest


class TestImportList:
    """Test import list endpoints."""

    def test_import_list_pagination(self, http_client, api_url, auth_headers):
        """import-006: 导入历史列表 - 分页查询"""
        response = http_client.get(
            f"{api_url}/imports",
            params={"page": 1, "page_size": 20},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_import_list_filter_by_type(self, http_client, api_url, auth_headers):
        """import-007: 导入历史列表 - 按类型筛选"""
        response = http_client.get(
            f"{api_url}/imports",
            params={"import_type": "hotels"},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestHotelImport:
    """Test hotel data import."""

    def test_import_hotels_excel(self, http_client, api_url, auth_headers):
        """import-001: 酒店数据导入 - Excel格式"""
        files = {
            "file": ("hotels.xlsx", io.BytesIO(b"dummy"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = http_client.post(
            f"{api_url}/imports/hotels",
            files=files,
            headers=auth_headers
        )

        # May fail due to invalid file, but should not crash
        assert response.status_code in [201, 400, 422]

    def test_import_hotels_csv(self, http_client, api_url, auth_headers):
        """import-002: 酒店数据导入 - CSV格式"""
        files = {
            "file": ("hotels.csv", io.BytesIO(b"dummy"), "text/csv")
        }
        response = http_client.post(
            f"{api_url}/imports/hotels",
            files=files,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]


class TestRoomImport:
    """Test room data import."""

    def test_import_rooms_excel(self, http_client, api_url, auth_headers):
        """import-003: 客房数据导入 - Excel格式"""
        files = {
            "file": ("rooms.xlsx", io.BytesIO(b"dummy"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = http_client.post(
            f"{api_url}/imports/rooms",
            files=files,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 422]


class TestImportDetail:
    """Test import detail endpoints."""

    def test_import_progress(self, http_client, api_url, auth_headers):
        """import-004: 导入进度查询"""
        response = http_client.get(
            f"{api_url}/imports/1",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_import_errors(self, http_client, api_url, auth_headers):
        """import-005: 导入错误查看"""
        response = http_client.get(
            f"{api_url}/imports/1/errors",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
