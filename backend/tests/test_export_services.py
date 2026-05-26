"""
Tests for export services.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_history import (
    ExportFormat,
    ExportHistory,
    ExportStatus,
    ExportType,
)
from app.services.export_service import ExportService
from app.services.room_export_service import RoomExportService


class TestExportService:
    """Tests for ExportService."""

    @pytest.fixture
    def service(self):
        """Create export service instance."""
        return ExportService()

    @pytest_asyncio.fixture
    async def export_record(self, db_session: AsyncSession) -> ExportHistory:
        """Create a test export record."""
        record = ExportHistory(
            file_name="test_export_20260101_120000",
            export_type=ExportType.HOTEL,
            export_format=ExportFormat.EXCEL,
            status=ExportStatus.PENDING,
            file_path="/exports/test_export_20260101_120000.xlsx",
        )
        db_session.add(record)
        await db_session.flush()
        await db_session.refresh(record)
        return record

    async def test_create_export_record(
        self, service: ExportService, db_session: AsyncSession
    ):
        """Test creating an export record."""
        record = await service.create_export_record(
            db_session,
            export_type=ExportType.HOTEL,
            export_format=ExportFormat.EXCEL,
            hotel_ids=["hotel-1", "hotel-2"],
            use_template=True,
            template_id="template-1",
            operator_id="user-1",
            operator_name="Test User",
            operator_ip="127.0.0.1",
        )

        assert record is not None
        assert record.export_type == ExportType.HOTEL
        assert record.export_format == ExportFormat.EXCEL
        assert record.status == ExportStatus.PENDING
        assert record.operator_id == "user-1"
        assert record.operator_name == "Test User"

    async def test_get_export_record(
        self, service: ExportService, db_session: AsyncSession, export_record: ExportHistory
    ):
        """Test getting an export record by ID."""
        found = await service.get_export_record(db_session, export_id=export_record.id)
        assert found is not None
        assert found.id == export_record.id
        assert found.file_name == export_record.file_name

    async def test_get_export_record_not_found(
        self, service: ExportService, db_session: AsyncSession
    ):
        """Test getting a non-existent export record."""
        found = await service.get_export_record(db_session, export_id="non-existent-id")
        assert found is None

    async def test_update_export_status(
        self, service: ExportService, db_session: AsyncSession, export_record: ExportHistory
    ):
        """Test updating export status."""
        updated = await service.update_export_status(
            db_session,
            export_id=export_record.id,
            status=ExportStatus.COMPLETED,
            file_path="/exports/updated_path.xlsx",
            file_size=1024,
        )
        assert updated.status == ExportStatus.COMPLETED
        assert updated.file_path == "/exports/updated_path.xlsx"
        assert updated.file_size == 1024


class TestRoomExportService:
    """Tests for RoomExportService."""

    @pytest.fixture
    def service(self):
        """Create room export service instance."""
        return RoomExportService()

    async def test_default_room_columns_defined(self, service: RoomExportService):
        """Test that default room columns are properly defined."""
        assert len(service.DEFAULT_ROOM_COLUMNS) > 0
        # Verify structure
        for col in service.DEFAULT_ROOM_COLUMNS:
            assert isinstance(col, tuple)
            assert len(col) == 2
            assert isinstance(col[0], str)
            assert isinstance(col[1], str)

    async def test_export_service_has_required_methods(self, service: RoomExportService):
        """Test that export service has the required methods."""
        # Check that methods exist
        assert hasattr(service, "export_to_excel")
        assert hasattr(service, "export_to_csv")
        assert hasattr(service, "_get_room_data_with_hotel")
        assert hasattr(service, "DEFAULT_ROOM_COLUMNS")
        assert hasattr(service, "export_using_template")
        assert hasattr(service, "get_export_history")

    def test_default_room_columns_has_expected_fields(self, service: RoomExportService):
        """Test that default room columns contains expected fields."""
        column_keys = [col[0] for col in service.DEFAULT_ROOM_COLUMNS]
        # Check for essential room fields
        essential_fields = ["room_type_code", "name_cn", "name_en", "bed_type", "max_occupancy"]
        for field in essential_fields:
            assert field in column_keys, f"Expected field {field} not found in DEFAULT_ROOM_COLUMNS"

    def test_export_history_model_has_required_fields(self):
        """Test that ExportHistory model has required fields for tracking exports."""
        record = ExportHistory(
            file_name="test_export",
            export_type=ExportType.HOTEL,
            export_format=ExportFormat.EXCEL,
            status=ExportStatus.PENDING,
        )
        assert record.file_name == "test_export"
        assert record.export_type == ExportType.HOTEL
        assert record.export_format == ExportFormat.EXCEL
        assert record.status == ExportStatus.PENDING