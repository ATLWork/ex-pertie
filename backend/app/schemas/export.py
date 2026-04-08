"""
Export API schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Import enums from model to avoid duplication
from app.models.export_history import ExportFormat as ModelExportFormat
from app.models.export_history import ExportStatus as ModelExportStatus
from app.models.export_history import ExportType as ModelExportType


# Re-export for backwards compatibility
ExportFormat = ModelExportFormat
ExportStatus = ModelExportStatus
ExportType = ModelExportType


# ============== Request Schemas ==============


class HotelExportRequest(BaseModel):
    """Request schema for hotel data export."""

    export_format: ExportFormat = Field(
        default=ExportFormat.EXCEL, description="Export file format"
    )
    hotel_ids: Optional[List[str]] = Field(
        default=None, description="Specific hotel IDs to export (exports all if empty)"
    )
    use_template: bool = Field(
        default=False, description="Whether to use Expedia template format"
    )
    template_id: Optional[str] = Field(
        default=None, description="Template ID to use for export"
    )


class RoomExportRequest(BaseModel):
    """Request schema for room data export."""

    export_format: ExportFormat = Field(
        default=ExportFormat.EXCEL, description="Export file format"
    )
    hotel_ids: Optional[List[str]] = Field(
        default=None, description="Specific hotel IDs to filter rooms"
    )
    room_ids: Optional[List[str]] = Field(
        default=None, description="Specific room IDs to export"
    )
    use_template: bool = Field(
        default=False, description="Whether to use Expedia template format"
    )
    template_id: Optional[str] = Field(
        default=None, description="Template ID to use for export"
    )


# ============== Response Schemas ==============


class ExportHistoryResponse(BaseModel):
    """Export history record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Export record ID")
    file_name: str = Field(..., description="Generated file name")
    file_path: Optional[str] = Field(None, description="File storage path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL")
    export_type: ExportType = Field(..., description="Type of data exported")
    export_format: ExportFormat = Field(..., description="Export file format")
    status: ExportStatus = Field(..., description="Export status")
    filter_criteria: Optional[str] = Field(None, description="Filter criteria")
    hotel_ids: Optional[str] = Field(None, description="Selected hotel IDs")
    total_rows: int = Field(..., description="Total rows exported")
    total_hotels: int = Field(..., description="Total hotels exported")
    total_rooms: int = Field(..., description="Total rooms exported")
    template_id: Optional[str] = Field(None, description="Template ID used")
    template_name: Optional[str] = Field(None, description="Template name")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    download_count: int = Field(..., description="Download count")
    last_downloaded_at: Optional[datetime] = Field(None, description="Last download time")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    operator_id: Optional[str] = Field(None, description="Operator user ID")
    operator_name: Optional[str] = Field(None, description="Operator name")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Record update time")


class ExportInitiateResponse(BaseModel):
    """Response schema for export initiation."""

    export_id: str = Field(..., description="Export task ID")
    status: ExportStatus = Field(..., description="Initial status")
    message: str = Field(..., description="Status message")


class ExportDetailResponse(BaseModel):
    """Response schema for export detail."""

    export_id: str = Field(..., description="Export task ID")
    file_name: str = Field(..., description="File name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    status: ExportStatus = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL (if completed)")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    total_rows: int = Field(..., description="Total rows exported")
    total_hotels: int = Field(..., description="Total hotels exported")
    total_rooms: int = Field(..., description="Total rooms exported")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ExportListQuery(BaseModel):
    """Query parameters for export history list."""

    export_type: Optional[ExportType] = Field(None, description="Filter by export type")
    export_format: Optional[ExportFormat] = Field(None, description="Filter by format")
    status: Optional[ExportStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter start date")
    end_date: Optional[datetime] = Field(None, description="Filter end date")
