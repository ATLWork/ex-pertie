"""
Tests for RoomImportService.
"""

import pytest
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hotel, HotelBrand, HotelStatus, Room, ImportHistory, ImportType, ImportStatus
from app.services.room_import_service import RoomImportService


class TestRoomImportService:
    """Test cases for RoomImportService."""

    async def test_compute_file_hash(self, db_session: AsyncSession):
        """Test file hash computation."""
        service = RoomImportService()
        content = b"test content"
        hash1 = service._compute_file_hash(content)
        hash2 = service._compute_file_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    async def test_normalize_boolean(self, db_session: AsyncSession):
        """Test boolean normalization."""
        service = RoomImportService()

        # True values
        assert service._normalize_boolean(True) is True
        assert service._normalize_boolean("true") is True
        assert service._normalize_boolean("yes") is True
        assert service._normalize_boolean("1") is True

        # False values
        assert service._normalize_boolean(False) is False
        assert service._normalize_boolean("false") is False
        assert service._normalize_boolean("no") is False
        assert service._normalize_boolean("0") is False

        # None
        assert service._normalize_boolean(None) is None

    async def test_normalize_value(self, db_session: AsyncSession):
        """Test value normalization."""
        service = RoomImportService()

        # Boolean field
        assert service._normalize_value("true", "is_active") is True
        assert service._normalize_value("true", "balcony") is True

        # Integer fields
        assert service._normalize_value("2", "max_occupancy") == 2
        assert service._normalize_value("3.0", "standard_occupancy") == 3

        # Float fields
        assert service._normalize_value("30.5", "room_size") == 30.5

        # String with whitespace
        assert service._normalize_value("  hello  ", "name_cn") == "hello"

        # None/empty
        assert service._normalize_value(None, "name_en") is None
        assert service._normalize_value("", "name_en") is None

    async def test_find_column(self, db_session: AsyncSession):
        """Test finding column by name."""
        service = RoomImportService()

        headers = ["hotel_id", "name_cn", "name_en", "max_occupancy"]

        assert service._find_column(headers, "hotel_id") == 0
        assert service._find_column(headers, "name_cn") == 1
        assert service._find_column(headers, "Name_CN") == 1  # Case insensitive
        assert service._find_column(headers, "max_occupancy") == 3
        assert service._find_column(headers, "nonexistent") is None

    async def test_parse_headers(self, db_session: AsyncSession):
        """Test header parsing."""
        service = RoomImportService()

        headers = ["hotel_id", "room_name_cn", "room_name_en", "max_occupancy"]
        field_map = service._parse_headers(headers)

        assert "hotel_id" in field_map
        assert "name_cn" in field_map
        assert "name_en" in field_map
        assert "max_occupancy" in field_map

    async def test_row_to_dict(self, db_session: AsyncSession):
        """Test converting row to dictionary."""
        service = RoomImportService()

        field_map = {
            "hotel_id": 0,
            "name_cn": 1,
            "name_en": 2,
            "max_occupancy": 3,
        }
        row = ["hotel-123", "标准大床房", "Standard King Room", "2"]

        result = service._row_to_dict(row, field_map)

        assert result["hotel_id"] == "hotel-123"
        assert result["name_cn"] == "标准大床房"
        assert result["name_en"] == "Standard King Room"
        assert result["max_occupancy"] == 2

    async def test_parse_csv_file(self, db_session: AsyncSession):
        """Test CSV file parsing."""
        service = RoomImportService()

        csv_content = """hotel_id,name_cn,name_en,max_occupancy,bed_type
hotel-123,标准大床房,Standard King Room,2,King
hotel-123,标准双床房,Standard Twin Room,2,Twin"""

        rows = service._parse_csv_file(csv_content)

        assert len(rows) == 2
        assert rows[0]["name_cn"] == "标准大床房"
        assert rows[0]["max_occupancy"] == 2
        assert rows[1]["name_en"] == "Standard Twin Room"

    async def test_parse_csv_file_with_variations(self, db_session: AsyncSession):
        """Test CSV parsing with column name variations."""
        service = RoomImportService()

        csv_content = """hotel,room_name_cn,maxoccupancy
hotel-123,豪华套房,3"""

        rows = service._parse_csv_file(csv_content)

        assert len(rows) == 1
        assert rows[0]["name_cn"] == "豪华套房"
        assert rows[0]["max_occupancy"] == 3

    async def test_validate_before_import_valid(self, db_session: AsyncSession):
        """Test validation with valid room data."""
        service = RoomImportService()

        # Create hotel first
        hotel = Hotel(
            name_cn="测试酒店",
            name_en="Test Hotel",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路",
        )
        db_session.add(hotel)
        await db_session.flush()

        room_data = {
            "hotel_id": hotel.id,
            "name_cn": "标准大床房",
            "name_en": "Standard King Room",
            "room_type_code": "STD-KING-001",
            "standard_occupancy": 2,
            "total_rooms": 10,
            "max_occupancy": 2,
            "bed_type": "King",
        }

        result = await service.validate_before_import(db_session, room_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    async def test_validate_before_import_missing_hotel(
        self, db_session: AsyncSession
    ):
        """Test validation with non-existent hotel."""
        service = RoomImportService()

        room_data = {
            "hotel_id": "nonexistent-hotel-id",
            "name_cn": "标准大床房",
            "name_en": "Standard King Room",
            "max_occupancy": 2,
        }

        result = await service.validate_before_import(db_session, room_data)

        assert result.is_valid is False
        assert any(e.field == "hotel_id" for e in result.errors)

    async def test_validate_before_import_invalid_occupancy(
        self, db_session: AsyncSession
    ):
        """Test validation with invalid occupancy."""
        service = RoomImportService()

        # Create hotel first
        hotel = Hotel(
            name_cn="测试酒店",
            name_en="Test Hotel",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路",
        )
        db_session.add(hotel)
        await db_session.flush()

        room_data = {
            "hotel_id": hotel.id,
            "name_cn": "标准大床房",
            "name_en": "Standard King Room",
            "max_occupancy": 100,  # Too high
            "bed_type": "King",
        }

        result = await service.validate_before_import(db_session, room_data)

        assert result.is_valid is False


class TestRoomImportServiceIntegration:
    """Integration tests for RoomImportService."""

    async def test_import_single_room_success(self, db_session: AsyncSession):
        """Test successful single room import."""
        service = RoomImportService()

        # Create hotel first
        hotel = Hotel(
            name_cn="导入测试酒店",
            name_en="Import Test Hotel",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路",
        )
        db_session.add(hotel)
        await db_session.flush()

        room_data = {
            "hotel_id": hotel.id,
            "name_cn": "标准大床房",
            "name_en": "Standard King Room",
            "room_type_code": "STD-KING-001",
            "standard_occupancy": 2,
            "total_rooms": 10,
            "max_occupancy": 2,
            "bed_type": "King",
            "room_size": 30.0,
        }

        room, result = await service.import_single(db_session, room_data)

        assert room is not None
        assert room.name_cn == "标准大床房"
        assert result.is_valid is True

    async def test_import_from_csv(self, db_session: AsyncSession):
        """Test importing rooms from CSV file."""
        service = RoomImportService()

        # Create hotel first
        hotel = Hotel(
            name_cn="CSV导入测试酒店",
            name_en="CSV Import Test Hotel",
            brand=HotelBrand.ATour,
            status=HotelStatus.DRAFT,
            country_code="CN",
            province="上海",
            city="上海",
            address_cn="某路",
        )
        db_session.add(hotel)
        await db_session.flush()

        csv_content = f"""hotel_id,name_cn,name_en,max_occupancy,bed_type
{hotel.id},标准大床房,Standard King Room,2,King
{hotel.id},豪华套房,Deluxe Suite,3,King"""

        file_content = csv_content.encode("utf-8")

        import_history, row_results = await service.import_from_file(
            db_session,
            file_content=file_content,
            file_name="rooms.csv",
            file_path="/uploads/rooms.csv",
            operator_name="Test Operator",
        )

        assert import_history is not None
        assert import_history.total_rows == 2
        assert import_history.import_type == ImportType.ROOM

    async def test_get_import_history(self, db_session: AsyncSession):
        """Test getting import history."""
        service = RoomImportService()

        # Create some import history
        history1 = ImportHistory(
            file_name="rooms1.csv",
            file_path="/uploads/rooms1.csv",
            file_size=1000,
            file_hash="hash1",
            import_type=ImportType.ROOM,
            status=ImportStatus.COMPLETED,
            total_rows=10,
            success_rows=10,
        )
        db_session.add(history1)
        await db_session.flush()

        records, total = await service.get_import_history(db_session, skip=0, limit=10)

        assert total >= 1
        assert len(records) >= 1


class TestRoomImportServiceEdgeCases:
    """Edge case tests for RoomImportService."""

    async def test_normalize_integer_conversion(self, db_session: AsyncSession):
        """Test integer normalization handles float-like strings."""
        service = RoomImportService()

        assert service._normalize_value("3.0", "max_occupancy") == 3
        assert service._normalize_value("5.7", "total_rooms") == 5

    async def test_empty_csv_headers(self, db_session: AsyncSession):
        """Test parsing CSV with empty headers."""
        service = RoomImportService()

        with pytest.raises(ValueError, match="no headers"):
            service._parse_csv_file("")

    async def test_parse_csv_no_matching_fields(self, db_session: AsyncSession):
        """Test parsing CSV with no recognized fields."""
        service = RoomImportService()

        csv_content = """col1,col2,col3
val1,val2,val3"""

        with pytest.raises(ValueError, match="No recognized room fields"):
            service._parse_csv_file(csv_content)