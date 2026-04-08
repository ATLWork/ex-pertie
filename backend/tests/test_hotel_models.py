"""
Tests for hotel and room models.
"""

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Hotel, HotelBrand, HotelStatus,
    Room, RoomExtension,
    ImportHistory, ImportType, ImportStatus,
    ExportHistory, ExportType, ExportFormat, ExportStatus,
    ExpediaTemplate, FieldMapping, TemplateType, TemplateStatus, FieldMappingType,
)


class TestHotelModel:
    """Test cases for Hotel model."""

    async def test_create_hotel(self, db_session: AsyncSession):
        """Test creating a hotel."""
        hotel = Hotel(
            name_cn="测试酒店",
            name_en="Test Hotel",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海市",
            city="上海",
            district="浦东新区",
            address_cn="浦东新区某路123号",
            address_en="123 Some Road, Pudong District",
            postal_code="200000",
            phone="+86-21-12345678",
            email="info@testhotel.com",
        )
        db_session.add(hotel)
        await db_session.flush()
        await db_session.refresh(hotel)

        assert hotel.id is not None
        assert hotel.name_cn == "测试酒店"
        assert hotel.name_en == "Test Hotel"
        assert hotel.brand == HotelBrand.ATour
        assert hotel.status == HotelStatus.DRAFT
        assert hotel.city == "上海"
        assert hotel.created_at is not None
        assert hotel.updated_at is not None

    async def test_hotel_display_name(self, db_session: AsyncSession):
        """Test hotel display_name property."""
        hotel_cn = Hotel(
            name_cn="中文名称",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="北京",
            city="北京",
            address_cn="某地址",
        )
        db_session.add(hotel_cn)
        await db_session.flush()

        assert hotel_cn.display_name == "中文名称"

        hotel_en = Hotel(
            name_cn="中文名",
            name_en="English Name",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="北京",
            city="北京",
            address_cn="某地址",
        )
        db_session.add(hotel_en)
        await db_session.flush()

        assert hotel_en.display_name == "English Name"

    async def test_hotel_with_expedia_id(self, db_session: AsyncSession):
        """Test hotel with Expedia ID."""
        hotel = Hotel(
            name_cn="Expedia酒店",
            brand=HotelBrand.ATour,
            status=HotelStatus.PUBLISHED,
            country_code="CN",
            province="广东",
            city="广州",
            address_cn="天河区某路",
            expedia_hotel_id="EXP-123456",
            expedia_chain_code="ATOUR",
            expedia_property_code="ATOUR-GZ-001",
        )
        db_session.add(hotel)
        await db_session.flush()
        await db_session.refresh(hotel)

        assert hotel.expedia_hotel_id == "EXP-123456"
        assert hotel.expedia_chain_code == "ATOUR"


class TestRoomModel:
    """Test cases for Room model."""

    async def test_create_room(self, db_session: AsyncSession):
        """Test creating a room."""
        hotel = Hotel(
            name_cn="测试酒店",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路123号",
        )
        db_session.add(hotel)
        await db_session.flush()

        room = Room(
            hotel_id=hotel.id,
            room_type_code="STD-KING",
            name_cn="标准大床房",
            name_en="Standard King Room",
            description_cn="温馨舒适的标准大床房",
            description_en="Cozy standard room with king bed",
            bed_type="King",
            max_occupancy=2,
            standard_occupancy=2,
            room_size=30.5,
            floor_range="5-10",
            total_rooms=20,
        )
        db_session.add(room)
        await db_session.flush()
        await db_session.refresh(room)

        assert room.id is not None
        assert room.hotel_id == hotel.id
        assert room.name_cn == "标准大床房"
        assert room.bed_type == "King"
        assert room.max_occupancy == 2

    async def test_room_display_name(self, db_session: AsyncSession):
        """Test room display_name property."""
        hotel = Hotel(
            name_cn="测试酒店",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路123号",
        )
        db_session.add(hotel)
        await db_session.flush()

        room_cn = Room(
            hotel_id=hotel.id,
            room_type_code="TEST",
            name_cn="中文房型",
        )
        db_session.add(room_cn)
        await db_session.flush()

        assert room_cn.display_name == "中文房型"

        room_en = Room(
            hotel_id=hotel.id,
            room_type_code="TEST2",
            name_cn="中文名",
            name_en="English Room",
        )
        db_session.add(room_en)
        await db_session.flush()

        assert room_en.display_name == "English Room"

    async def test_room_hotel_relationship(self, db_session: AsyncSession):
        """Test room-hotel relationship."""
        hotel = Hotel(
            name_cn="关系测试酒店",
            brand=HotelBrand.ATourX,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="浙江",
            city="杭州",
            address_cn="西湖区某路",
        )
        db_session.add(hotel)
        await db_session.flush()

        room1 = Room(
            hotel_id=hotel.id,
            room_type_code="DELUXE",
            name_cn="豪华房",
        )
        room2 = Room(
            hotel_id=hotel.id,
            room_type_code="SUITE",
            name_cn="套房",
        )
        db_session.add(room1)
        db_session.add(room2)
        await db_session.flush()

        # Refresh hotel to get rooms
        await db_session.refresh(hotel, ["rooms"])

        assert len(hotel.rooms) == 2
        room_names = [r.name_cn for r in hotel.rooms]
        assert "豪华房" in room_names
        assert "套房" in room_names


class TestRoomExtensionModel:
    """Test cases for RoomExtension model."""

    async def test_create_room_extension(self, db_session: AsyncSession):
        """Test creating room extension."""
        hotel = Hotel(
            name_cn="测试酒店",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路123号",
        )
        db_session.add(hotel)
        await db_session.flush()

        room = Room(
            hotel_id=hotel.id,
            room_type_code="STD",
            name_cn="标准间",
        )
        db_session.add(room)
        await db_session.flush()

        extension = RoomExtension(
            room_id=room.id,
            amenities_cn="免费WiFi,空调,电视",
            amenities_en="Free WiFi, Air conditioning, TV",
            view_type="城市景观",
            balcony=True,
            smoking_policy="无烟",
            bathroom_type="独立卫浴",
        )
        db_session.add(extension)
        await db_session.flush()
        await db_session.refresh(extension)

        assert extension.id is not None
        assert extension.room_id == room.id
        assert "免费WiFi" in extension.amenities_cn
        assert extension.balcony is True


class TestImportHistoryModel:
    """Test cases for ImportHistory model."""

    async def test_create_import_history(self, db_session: AsyncSession):
        """Test creating import history."""
        history = ImportHistory(
            file_name="hotels_20260409.xlsx",
            file_path="/uploads/hotels_20260409.xlsx",
            file_size=1024000,
            file_hash="abc123def456",
            import_type=ImportType.HOTEL,
            status=ImportStatus.PENDING,
            total_rows=100,
            operator_id="user-123",
            operator_name="Test User",
            operator_ip="192.168.1.1",
        )
        db_session.add(history)
        await db_session.flush()
        await db_session.refresh(history)

        assert history.id is not None
        assert history.file_name == "hotels_20260409.xlsx"
        assert history.import_type == ImportType.HOTEL
        assert history.success_rate == 0.0

    async def test_import_history_success_rate(self, db_session: AsyncSession):
        """Test import history success rate calculation."""
        history = ImportHistory(
            file_name="test.xlsx",
            file_path="/uploads/test.xlsx",
            file_size=1000,
            import_type=ImportType.ROOM,
            status=ImportStatus.COMPLETED,
            total_rows=100,
            success_rows=95,
            failed_rows=5,
        )
        db_session.add(history)
        await db_session.flush()

        assert history.success_rate == 95.0

    async def test_import_history_is_completed(self, db_session: AsyncSession):
        """Test is_completed property."""
        pending = ImportHistory(
            file_name="pending.xlsx",
            file_path="/uploads/pending.xlsx",
            file_size=1000,
            import_type=ImportType.MIXED,
            status=ImportStatus.PENDING,
        )
        completed = ImportHistory(
            file_name="completed.xlsx",
            file_path="/uploads/completed.xlsx",
            file_size=1000,
            import_type=ImportType.MIXED,
            status=ImportStatus.COMPLETED,
        )
        failed = ImportHistory(
            file_name="failed.xlsx",
            file_path="/uploads/failed.xlsx",
            file_size=1000,
            import_type=ImportType.MIXED,
            status=ImportStatus.FAILED,
        )
        db_session.add_all([pending, completed, failed])
        await db_session.flush()

        assert pending.is_completed is False
        assert completed.is_completed is True
        assert failed.is_completed is True


class TestExportHistoryModel:
    """Test cases for ExportHistory model."""

    async def test_create_export_history(self, db_session: AsyncSession):
        """Test creating export history."""
        history = ExportHistory(
            file_name="export_hotels_20260409.xlsx",
            export_type=ExportType.HOTEL,
            export_format=ExportFormat.EXCEL,
            status=ExportStatus.PENDING,
            total_rows=50,
            total_hotels=10,
            total_rooms=50,
            operator_id="user-456",
            operator_name="Export User",
        )
        db_session.add(history)
        await db_session.flush()
        await db_session.refresh(history)

        assert history.id is not None
        assert history.export_type == ExportType.HOTEL
        assert history.export_format == ExportFormat.EXCEL

    async def test_export_history_is_downloadable(self, db_session: AsyncSession):
        """Test is_downloadable property."""
        # Not completed - not downloadable
        not_completed = ExportHistory(
            file_name="pending.xlsx",
            export_type=ExportType.HOTEL,
            export_format=ExportFormat.EXCEL,
            status=ExportStatus.PROCESSING,
        )
        db_session.add(not_completed)
        await db_session.flush()

        assert not_completed.is_downloadable is False


class TestExpediaTemplateModel:
    """Test cases for ExpediaTemplate model."""

    async def test_create_expedia_template(self, db_session: AsyncSession):
        """Test creating Expedia template."""
        template = ExpediaTemplate(
            name="Expedia酒店模板",
            code="EXP-HOTEL-V1",
            description="Expedia酒店数据上传模板",
            template_type=TemplateType.HOTEL,
            status=TemplateStatus.DRAFT,
            version="1.0",
            expedia_template_name="Expedia Hotel Template",
            expedia_template_id="EXP-TPL-001",
            header_row=1,
            data_start_row=2,
            sheet_name="Hotels",
        )
        db_session.add(template)
        await db_session.flush()
        await db_session.refresh(template)

        assert template.id is not None
        assert template.code == "EXP-HOTEL-V1"
        assert template.template_type == TemplateType.HOTEL
        assert template.status == TemplateStatus.DRAFT


class TestFieldMappingModel:
    """Test cases for FieldMapping model."""

    async def test_create_field_mapping(self, db_session: AsyncSession):
        """Test creating field mapping."""
        template = ExpediaTemplate(
            name="测试模板",
            code="TEST-TPL",
            template_type=TemplateType.ROOM,
            status=TemplateStatus.ACTIVE,
        )
        db_session.add(template)
        await db_session.flush()

        mapping = FieldMapping(
            template_id=template.id,
            field_order=1,
            source_field="name_cn",
            source_field_cn="酒店名称",
            source_model="Hotel",
            target_field="HotelName",
            target_field_required=True,
            mapping_type=FieldMappingType.DIRECT,
            is_active=True,
            is_visible=True,
        )
        db_session.add(mapping)
        await db_session.flush()
        await db_session.refresh(mapping)

        assert mapping.id is not None
        assert mapping.source_field == "name_cn"
        assert mapping.target_field == "HotelName"
        assert mapping.mapping_type == FieldMappingType.DIRECT
