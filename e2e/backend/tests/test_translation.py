"""
Translation API E2E tests.
"""

import pytest


class TestTranslation:
    """Test basic translation endpoints."""

    def test_translate_single(self, http_client, api_url, auth_headers):
        """trans-001: 单条翻译 - 中译英"""
        response = http_client.post(
            f"{api_url}/translation/translate",
            json={
                "text": "酒店提供免费WiFi",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
            },
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_batch_translate(self, http_client, api_url, auth_headers):
        """trans-004: 批量翻译 - 空列表"""
        response = http_client.post(
            f"{api_url}/translation/batch",
            json={"texts": []},
            headers=auth_headers
        )

        assert response.status_code in [200, 400]


class TestGlossary:
    """Test glossary endpoints."""

    def test_glossary_list(self, http_client, api_url, auth_headers):
        """trans-005: 术语库列表查询 - 分页"""
        response = http_client.get(
            f"{api_url}/translation/glossary",
            params={"page": 1, "page_size": 20},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_glossary_create(self, http_client, api_url, auth_headers):
        """trans-006: 术语库创建 - 必填字段完整"""
        response = http_client.post(
            f"{api_url}/translation/glossary",
            json={
                "term": "测试术语",
                "translation": "Test Term",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": "general",
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_glossary_create_missing_fields(self, http_client, api_url, auth_headers):
        """trans-007: 术语库创建 - 缺少必填字段"""
        response = http_client.post(
            f"{api_url}/translation/glossary",
            json={"term": "测试"},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_glossary_update(self, http_client, api_url, auth_headers):
        """trans-008: 术语库更新 - 部分字段"""
        # Create first
        create_response = http_client.post(
            f"{api_url}/translation/glossary",
            json={
                "term": f"测试术语_{id}",
                "translation": "Test Term",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": "general",
            },
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            data = create_response.json()
            glossary_id = data.get("id")

            if glossary_id:
                update_response = http_client.put(
                    f"{api_url}/translation/glossary/{glossary_id}",
                    json={"translation": "Updated Term"},
                    headers=auth_headers
                )
                assert update_response.status_code == 200

    def test_glossary_delete(self, http_client, api_url, auth_headers):
        """trans-009: 术语库删除 - 存在术语"""
        # Create first
        create_response = http_client.post(
            f"{api_url}/translation/glossary",
            json={
                "term": f"删除测试术语_{id}",
                "translation": "Delete Test Term",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": "general",
            },
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            data = create_response.json()
            glossary_id = data.get("id")

            if glossary_id:
                delete_response = http_client.delete(
                    f"{api_url}/translation/glossary/{glossary_id}",
                    headers=auth_headers
                )
                assert delete_response.status_code == 200

    def test_glossary_bulk_create(self, http_client, api_url, auth_headers):
        """trans-010: 术语库批量导入 - 成功"""
        response = http_client.post(
            f"{api_url}/translation/glossary/bulk",
            json={
                "items": [
                    {
                        "term": "术语1",
                        "translation": "Term 1",
                        "source_lang": "zh-CN",
                        "target_lang": "en-US",
                    },
                    {
                        "term": "术语2",
                        "translation": "Term 2",
                        "source_lang": "zh-CN",
                        "target_lang": "en-US",
                    },
                ]
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_glossary_filter_by_category(self, http_client, api_url, auth_headers):
        """trans-011: 术语库查询 - 按分类筛选"""
        response = http_client.get(
            f"{api_url}/translation/glossary",
            params={"category": "hotel"},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_glossary_filter_by_lang(self, http_client, api_url, auth_headers):
        """trans-012: 术语库查询 - 按语言筛选"""
        response = http_client.get(
            f"{api_url}/translation/glossary",
            params={"source_lang": "zh-CN", "target_lang": "en-US"},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestRules:
    """Test translation rules endpoints."""

    def test_rules_list(self, http_client, api_url, auth_headers):
        """trans-013: 翻译规则列表查询"""
        response = http_client.get(
            f"{api_url}/translation/rules",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_rules_create(self, http_client, api_url, auth_headers):
        """trans-014: 翻译规则创建"""
        response = http_client.post(
            f"{api_url}/translation/rules",
            json={
                "name": f"test_rule_{id}",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name_cn",
                "rule_type": "direct",
                "rule_value": "{}",
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_rules_update(self, http_client, api_url, auth_headers):
        """trans-015: 翻译规则更新"""
        # Create first
        create_response = http_client.post(
            f"{api_url}/translation/rules",
            json={
                "name": f"update_rule_{id}",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name_cn",
                "rule_type": "direct",
                "rule_value": "{}",
            },
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            data = create_response.json()
            rule_id = data.get("id")

            if rule_id:
                update_response = http_client.put(
                    f"{api_url}/translation/rules/{rule_id}",
                    json={"rule_value": '{"new": "value"}'},
                    headers=auth_headers
                )
                assert update_response.status_code == 200

    def test_rules_delete(self, http_client, api_url, auth_headers):
        """trans-016: 翻译规则删除"""
        # Create first
        create_response = http_client.post(
            f"{api_url}/translation/rules",
            json={
                "name": f"delete_rule_{id}",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name_cn",
                "rule_type": "direct",
                "rule_value": "{}",
            },
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            data = create_response.json()
            rule_id = data.get("id")

            if rule_id:
                delete_response = http_client.delete(
                    f"{api_url}/translation/rules/{rule_id}",
                    headers=auth_headers
                )
                assert delete_response.status_code == 200

    def test_rules_activate_deactivate(self, http_client, api_url, auth_headers):
        """trans-017: 翻译规则激活/停用"""
        # Create first
        create_response = http_client.post(
            f"{api_url}/translation/rules",
            json={
                "name": f"activate_rule_{id}",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name_cn",
                "rule_type": "direct",
                "rule_value": "{}",
            },
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            data = create_response.json()
            rule_id = data.get("id")

            if rule_id:
                activate_response = http_client.post(
                    f"{api_url}/translation/rules/{rule_id}/activate",
                    headers=auth_headers
                )
                assert activate_response.status_code == 200


class TestReferences:
    """Test translation references endpoints."""

    def test_references_list(self, http_client, api_url, auth_headers):
        """trans-018: 翻译参考库列表查询"""
        response = http_client.get(
            f"{api_url}/translation/references",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_references_create(self, http_client, api_url, auth_headers):
        """trans-019: 翻译参考库创建"""
        response = http_client.post(
            f"{api_url}/translation/references",
            json={
                "source_text": "酒店",
                "translated_text": "Hotel",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "source": "manual",
            },
            headers=auth_headers
        )

        assert response.status_code in [200, 201]

    def test_references_match(self, http_client, api_url, auth_headers):
        """trans-020: 翻译参考库匹配查询"""
        response = http_client.get(
            f"{api_url}/translation/references/match",
            params={
                "source_text": "酒店",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
            },
            headers=auth_headers
        )

        assert response.status_code == 200
