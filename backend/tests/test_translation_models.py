"""
Tests for translation models and services.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.translation import (
    TranslationRule,
    TranslationReference,
    Glossary,
    TranslationHistory,
    RuleType,
    ReferenceSource,
    GlossaryCategory,
    TranslationType,
)
from app.services.translation_rule import translation_rule as rule_service
from app.services.translation_reference import translation_reference as reference_service
from app.services.glossary import glossary as glossary_service
from app.services.translation_history import translation_history as history_service


class TestTranslationRuleModel:
    """Tests for TranslationRule model."""

    @pytest.mark.asyncio
    async def test_create_translation_rule(self, db_session: AsyncSession):
        """Test creating a translation rule."""
        rule = TranslationRule(
            name="test_rule",
            source_lang="zh-CN",
            target_lang="en-US",
            field_name="hotel_name",
            rule_type=RuleType.AI,
            rule_value='{"temperature": 0.7}',
            is_active=True,
        )
        db_session.add(rule)
        await db_session.flush()
        await db_session.refresh(rule)

        assert rule.id is not None
        assert rule.name == "test_rule"
        assert rule.source_lang == "zh-CN"
        assert rule.target_lang == "en-US"
        assert rule.rule_type == RuleType.AI
        assert rule.is_active is True
        assert rule.created_at is not None
        assert rule.updated_at is not None

    @pytest.mark.asyncio
    async def test_translation_rule_service_create(self, db_session: AsyncSession):
        """Test creating rule via service."""
        rule = await rule_service.create(
            db_session,
            obj_in={
                "name": "service_rule",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "description",
                "rule_type": RuleType.DIRECT,
                "rule_value": '{"mapping": {}}',
                "is_active": True,
            },
        )

        assert rule.id is not None
        assert rule.name == "service_rule"

    @pytest.mark.asyncio
    async def test_get_active_rules(self, db_session: AsyncSession):
        """Test getting active rules."""
        # Create test rules
        await rule_service.create(
            db_session,
            obj_in={
                "name": "active_rule",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name",
                "rule_type": RuleType.AI,
                "rule_value": "{}",
                "is_active": True,
            },
        )
        await rule_service.create(
            db_session,
            obj_in={
                "name": "inactive_rule",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "field_name": "name",
                "rule_type": RuleType.AI,
                "rule_value": "{}",
                "is_active": False,
            },
        )

        active_rules = await rule_service.get_active_rules(
            db_session, source_lang="zh-CN", target_lang="en-US"
        )

        assert len(active_rules) == 1
        assert active_rules[0].name == "active_rule"


class TestTranslationReferenceModel:
    """Tests for TranslationReference model."""

    @pytest.mark.asyncio
    async def test_create_translation_reference(self, db_session: AsyncSession):
        """Test creating a translation reference."""
        ref = TranslationReference(
            source_text="酒店",
            translated_text="Hotel",
            source_lang="zh-CN",
            target_lang="en-US",
            context="Hotel name context",
            confidence=0.95,
            source=ReferenceSource.MANUAL,
        )
        db_session.add(ref)
        await db_session.flush()
        await db_session.refresh(ref)

        assert ref.id is not None
        assert ref.source_text == "酒店"
        assert ref.translated_text == "Hotel"
        assert ref.confidence == 0.95
        assert ref.source == ReferenceSource.MANUAL

    @pytest.mark.asyncio
    async def test_find_matching_reference(self, db_session: AsyncSession):
        """Test finding matching reference."""
        await reference_service.create(
            db_session,
            obj_in={
                "source_text": "豪华套房",
                "translated_text": "Deluxe Suite",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "confidence": 0.9,
                "source": ReferenceSource.MANUAL,
            },
        )

        match = await reference_service.find_match(
            db_session,
            source_text="豪华套房",
            source_lang="zh-CN",
            target_lang="en-US",
        )

        assert match is not None
        assert match.translated_text == "Deluxe Suite"

    @pytest.mark.asyncio
    async def test_find_similar_references(self, db_session: AsyncSession):
        """Test finding similar references."""
        await reference_service.create(
            db_session,
            obj_in={
                "source_text": "豪华大床房",
                "translated_text": "Deluxe King Room",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "confidence": 0.9,
                "source": ReferenceSource.MANUAL,
            },
        )
        await reference_service.create(
            db_session,
            obj_in={
                "source_text": "豪华双床房",
                "translated_text": "Deluxe Twin Room",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "confidence": 0.9,
                "source": ReferenceSource.MANUAL,
            },
        )

        similar = await reference_service.find_similar(
            db_session,
            source_text="豪华",
            source_lang="zh-CN",
            target_lang="en-US",
        )

        assert len(similar) == 2


class TestGlossaryModel:
    """Tests for Glossary model."""

    @pytest.mark.asyncio
    async def test_create_glossary(self, db_session: AsyncSession):
        """Test creating a glossary entry."""
        entry = Glossary(
            term="大堂",
            translation="Lobby",
            source_lang="zh-CN",
            target_lang="en-US",
            category=GlossaryCategory.HOTEL,
            notes="Common hotel area",
            is_active=True,
        )
        db_session.add(entry)
        await db_session.flush()
        await db_session.refresh(entry)

        assert entry.id is not None
        assert entry.term == "大堂"
        assert entry.translation == "Lobby"
        assert entry.category == GlossaryCategory.HOTEL

    @pytest.mark.asyncio
    async def test_lookup_term(self, db_session: AsyncSession):
        """Test looking up a term in glossary."""
        await glossary_service.create(
            db_session,
            obj_in={
                "term": "健身房",
                "translation": "Fitness Center",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": GlossaryCategory.AMENITY,
                "is_active": True,
            },
        )

        found = await glossary_service.lookup_term(
            db_session,
            text="健身房",
            source_lang="zh-CN",
            target_lang="en-US",
        )

        assert found is not None
        assert found.translation == "Fitness Center"

    @pytest.mark.asyncio
    async def test_get_active_terms_by_category(self, db_session: AsyncSession):
        """Test getting active terms filtered by category."""
        await glossary_service.create(
            db_session,
            obj_in={
                "term": "标准间",
                "translation": "Standard Room",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": GlossaryCategory.ROOM,
                "is_active": True,
            },
        )
        await glossary_service.create(
            db_session,
            obj_in={
                "term": "游泳池",
                "translation": "Swimming Pool",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "category": GlossaryCategory.AMENITY,
                "is_active": True,
            },
        )

        room_terms = await glossary_service.get_active_terms(
            db_session,
            source_lang="zh-CN",
            target_lang="en-US",
            category=GlossaryCategory.ROOM,
        )

        assert len(room_terms) == 1
        assert room_terms[0].term == "标准间"


class TestTranslationHistoryModel:
    """Tests for TranslationHistory model."""

    @pytest.mark.asyncio
    async def test_create_translation_history(self, db_session: AsyncSession):
        """Test creating a translation history entry."""
        history = TranslationHistory(
            source_text="欢迎入住",
            translated_text="Welcome to stay",
            source_lang="zh-CN",
            target_lang="en-US",
            translation_type=TranslationType.AI,
            reference_used=True,
            glossary_used=True,
            confidence_score=0.92,
        )
        db_session.add(history)
        await db_session.flush()
        await db_session.refresh(history)

        assert history.id is not None
        assert history.source_text == "欢迎入住"
        assert history.translation_type == TranslationType.AI
        assert history.reference_used is True
        assert history.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_get_recent_history(self, db_session: AsyncSession):
        """Test getting recent translation history."""
        await history_service.create(
            db_session,
            obj_in={
                "source_text": "测试文本1",
                "translated_text": "Test text 1",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "translation_type": TranslationType.MACHINE,
                "reference_used": False,
                "glossary_used": False,
            },
        )
        await history_service.create(
            db_session,
            obj_in={
                "source_text": "测试文本2",
                "translated_text": "Test text 2",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "translation_type": TranslationType.AI,
                "reference_used": True,
                "glossary_used": False,
            },
        )

        recent = await history_service.get_recent(db_session, limit=10)

        assert len(recent) == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session: AsyncSession):
        """Test getting translation statistics."""
        await history_service.create(
            db_session,
            obj_in={
                "source_text": "文本1",
                "translated_text": "Text 1",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "translation_type": TranslationType.AI,
                "reference_used": True,
                "glossary_used": True,
                "confidence_score": 0.9,
            },
        )
        await history_service.create(
            db_session,
            obj_in={
                "source_text": "文本2",
                "translated_text": "Text 2",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "translation_type": TranslationType.AI,
                "reference_used": False,
                "glossary_used": True,
                "confidence_score": 0.8,
            },
        )

        stats = await history_service.get_statistics(db_session)

        assert stats["total"] == 2
        assert stats["reference_usage"] == 1
        assert stats["glossary_usage"] == 2
        assert stats["average_confidence"] == 0.85
