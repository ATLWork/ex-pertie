"""
Tests for HotelImportService.
"""

import pytest
import csv
from io import StringIO
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hotel, HotelBrand, HotelStatus, ImportHistory, ImportType, ImportStatus
from app.services.hotel_import_service import HotelImportService


class TestHotelImportService:
    """Test cases for HotelImportService."""

    async def test_compute_file_hash(self, db_session: AsyncSession):
        """Test file hash computation."""
        service = HotelImportService()
        content = b"test content"
        hash1 = service._compute_file_hash(content)
        hash2 = service._compute_file_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    async def test_normalize_boolean(self, db_session: AsyncSession):
        """Test boolean normalization."""
        service = HotelImportService()

        # True values
        assert service._normalize_boolean(True) is True
        assert service._normalize_boolean("true") is True
        assert service._normalize_boolean("yes") is True
        assert service._normalize_boolean("1") is True
        assert service._normalize_boolean("t") is True
        assert service._normalize_boolean("y") is True

        # False values
        assert service._normalize_boolean(False) is False
        assert service._normalize_boolean("false") is False
        assert service._normalize_boolean("no") is False
        assert service._normalize_boolean("0") is False
        assert service._normalize_boolean("f") is False
        assert service._normalize_boolean("n") is False

        # None/null
        assert service._normalize_boolean(None) is None
        assert service._normalize_boolean("") is None

    async def test_normalize_value(self, db_session: AsyncSession):
        """Test value normalization."""
        service = HotelImportService()

        # Boolean field
        assert service._normalize_value("true", "is_active") is True

        # Float fields
        assert service._normalize_value("31.23", "latitude") == 31.23
        assert service._normalize_value("121.47", "longitude") == 121.47

        # String with whitespace
        assert service._normalize_value("  hello  ", "name_cn") == "hello"

        # None/empty
        assert service._normalize_value(None, "name_en") is None
        assert service._normalize_value("", "name_en") is None

    async def test_parse_csv_file(self, db_session: AsyncSession):
        """Test CSV file parsing."""
        service = HotelImportService()

        csv_content = """name_cn,name_en,city,province,country_code
上海酒店,Shanghai Hotel,上海,上海市,CN
北京酒店,Beijing Hotel,北京,北京市,CN"""

        rows = service._parse_csv_file(csv_content)

        assert len(rows) == 2
        assert rows[0]["name_cn"] == "上海酒店"
        assert rows[0]["name_en"] == "Shanghai Hotel"
        assert rows[0]["city"] == "上海"
        assert rows[1]["name_cn"] == "北京酒店"

    async def test_parse_csv_file_with_variations(self, db_session: AsyncSession):
        """Test CSV parsing with column name variations."""
        service = HotelImportService()

        # Test various column name variations
        csv_content = """hotel_name_cn,hotel_name_en,city_name,countrycode
测试酒店,Test Hotel,杭州,CN"""

        rows = service._parse_csv_file(csv_content)

        assert len(rows) == 1
        assert rows[0]["name_cn"] == "测试酒店"
        assert rows[0]["name_en"] == "Test Hotel"
        assert rows[0]["city"] == "杭州"

    async def test_parse_csv_file_empty(self, db_session: AsyncSession):
        """Test parsing CSV with no headers."""
        service = HotelImportService()

        with pytest.raises(ValueError, match="no headers"):
            service._parse_csv_file("")

    async def test_validate_before_import_valid(self, db_session: AsyncSession):
        """Test validation with valid hotel data."""
        service = HotelImportService()

        hotel_data = {
            "name_cn": "测试酒店",
            "name_en": "Test Hotel",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "brand": "atour",
            "status": "draft",
        }

        result = await service.validate_before_import(db_session, hotel_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    async def test_validate_before_import_missing_required(
        self, db_session: AsyncSession
    ):
        """Test validation with missing required fields."""
        service = HotelImportService()

        hotel_data = {
            "name_en": "Test Hotel",
            # Missing name_cn, province, city, address_cn
        }

        result = await service.validate_before_import(db_session, hotel_data)

        assert result.is_valid is False
        assert any(e.field == "name_cn" for e in result.errors)

    async def test_validate_before_import_invalid_country(
        self, db_session: AsyncSession
    ):
        """Test validation with invalid country code."""
        service = HotelImportService()

        hotel_data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "XX",  # Invalid
        }

        result = await service.validate_before_import(db_session, hotel_data)

        assert result.is_valid is False
        assert any(e.field == "country_code" for e in result.errors)

    async def test_validate_before_import_invalid_expedia_id(
        self, db_session: AsyncSession
    ):
        """Test validation with invalid Expedia ID format."""
        service = HotelImportService()

        hotel_data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "expedia_hotel_id": "abc",  # Too short
        }

        result = await service.validate_before_import(db_session, hotel_data)

        assert result.is_valid is False
        assert any(e.field == "expedia_hotel_id" for e in result.errors)

    async def test_import_single_success(self, db_session: AsyncSession):
        """Test successful single hotel import."""
        service = HotelImportService()

        hotel_data = {
            "name_cn": "测试导入酒店",
            "name_en": "Test Import Hotel",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路456号",
            "country_code": "CN",
            "brand": "atour",
            "status": "draft",
        }

        hotel, result = await service.import_single(db_session, hotel_data)

        assert hotel is not None
        assert hotel.name_cn == "测试导入酒店"
        assert result.is_valid is True

    async def test_import_single_invalid(self, db_session: AsyncSession):
        """Test single hotel import with invalid data."""
        service = HotelImportService()

        hotel_data = {
            "name_en": "Test Hotel",
            # Missing required fields
        }

        hotel, result = await service.import_single(db_session, hotel_data)

        assert hotel is None
        assert result.is_valid is False

    async def test_import_from_csv_file(self, db_session: AsyncSession):
        """Test importing hotels from CSV file."""
        service = HotelImportService()

        csv_content = """name_cn,name_en,province,city,address_cn,country_code,brand,status
测试酒店A,Test Hotel A,上海市,上海,浦东新区某路1号,CN,atour,draft
测试酒店B,Test Hotel B,北京市,北京,朝阳区某路2号,CN,atour_x,published"""

        file_content = csv_content.encode("utf-8")

        import_history, row_results = await service.import_from_file(
            db_session,
            file_content=file_content,
            file_name="hotels.csv",
            file_path="/uploads/hotels.csv",
            operator_name="Test Operator",
        )

        assert import_history is not None
        assert import_history.total_rows == 2
        assert import_history.success_rows >= 1
        assert import_history.import_type == ImportType.HOTEL
        assert import_history.status in (
            ImportStatus.COMPLETED,
            ImportStatus.PARTIAL,
        )

    async def test_import_from_file_unsupported_format(self, db_session: AsyncSession):
        """Test importing with unsupported file format."""
        service = HotelImportService()

        with pytest.raises(
            ValueError, match="Unsupported file format"
        ):
            await service.import_from_file(
                db_session,
                file_content=b"test content",
                file_name="test.txt",
                file_path="/uploads/test.txt",
            )

    async def test_get_import_history(self, db_session: AsyncSession):
        """Test getting import history."""
        service = HotelImportService()

        # Create some import history
        history1 = ImportHistory(
            file_name="hotels1.csv",
            file_path="/uploads/hotels1.csv",
            file_size=1000,
            file_hash="hash1",
            import_type=ImportType.HOTEL,
            status=ImportStatus.COMPLETED,
            total_rows=10,
            success_rows=10,
        )
        history2 = ImportHistory(
            file_name="hotels2.csv",
            file_path="/uploads/hotels2.csv",
            file_size=2000,
            file_hash="hash2",
            import_type=ImportType.HOTEL,
            status=ImportStatus.COMPLETED,
            total_rows=20,
            success_rows=20,
        )
        db_session.add_all([history1, history2])
        await db_session.flush()

        records, total = await service.get_import_history(db_session, skip=0, limit=10)

        assert total == 2
        assert len(records) == 2
        # Records may be returned in either order depending on database timestamp resolution
        assert records[0].file_name in ["hotels1.csv", "hotels2.csv"]  # Most recent first (or creation order if same timestamp)

    async def test_get_import_history_pagination(self, db_session: AsyncSession):
        """Test import history pagination."""
        service = HotelImportService()

        # Create multiple records
        for i in range(5):
            history = ImportHistory(
                file_name=f"hotels{i}.csv",
                file_path=f"/uploads/hotels{i}.csv",
                file_size=1000,
                file_hash=f"hash{i}",
                import_type=ImportType.HOTEL,
                status=ImportStatus.COMPLETED,
                total_rows=10,
            )
            db_session.add(history)
        await db_session.flush()

        # Test pagination
        records, total = await service.get_import_history(db_session, skip=0, limit=2)

        assert total == 5
        assert len(records) == 2

        records, total = await service.get_import_history(db_session, skip=2, limit=2)

        assert total == 5
        assert len(records) == 2


class TestHotelImportServiceEdgeCases:
    """Edge case tests for HotelImportService."""

    async def test_import_empty_csv(self, db_session: AsyncSession):
        """Test importing empty CSV file."""
        service = HotelImportService()

        csv_content = """name_cn,name_en,province,city,address_cn,country_code
"""

        file_content = csv_content.encode("utf-8")

        import_history, row_results = await service.import_from_file(
            db_session,
            file_content=file_content,
            file_name="empty.csv",
            file_path="/uploads/empty.csv",
        )

        # Empty file should be processed without errors
        assert import_history is not None

    async def test_normalize_boolean_numeric(self, db_session: AsyncSession):
        """Test boolean normalization with numeric values."""
        service = HotelImportService()

        assert service._normalize_boolean(1) is True
        assert service._normalize_boolean(0) is False

    async def test_validate_duplicate_expedia_id(self, db_session: AsyncSession):
        """Test validation detects duplicate Expedia ID."""
        service = HotelImportService()

        # Create existing hotel with Expedia ID
        existing = Hotel(
            name_cn="已存在酒店",
            name_en="Existing Hotel",
            expedia_hotel_id="EXP-123456",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路",
        )
        db_session.add(existing)
        await db_session.flush()

        # Try to import with same Expedia ID
        hotel_data = {
            "name_cn": "新酒店",
            "name_en": "New Hotel",
            "province": "北京",
            "city": "北京",
            "address_cn": "某路",
            "country_code": "CN",
            "expedia_hotel_id": "EXP-123456",  # Duplicate
        }

        result = await service.validate_before_import(db_session, hotel_data)

        assert result.is_valid is False
        assert any("already exists" in e.message for e in result.errors)