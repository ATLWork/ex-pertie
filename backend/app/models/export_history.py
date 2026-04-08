"""
Export history model for tracking data exports.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ExportType(str, enum.Enum):
    """Export type enum."""

    HOTEL = "hotel"  # Hotel data export
    ROOM = "room"  # Room data export
    MIXED = "mixed"  # Mixed export (hotel + room)
    EXPEDIA_TEMPLATE = "expedia_template"  # Expedia template export


class ExportFormat(str, enum.Enum):
    """Export format enum."""

    EXCEL = "excel"  # Excel format
    CSV = "csv"  # CSV format
    JSON = "json"  # JSON format
    XML = "xml"  # XML format


class ExportStatus(str, enum.Enum):
    """Export status enum."""

    PENDING = "pending"  # Pending
    PROCESSING = "processing"  # Processing
    COMPLETED = "completed"  # Completed
    FAILED = "failed"  # Failed


class ExportHistory(BaseModel):
    """
    Export history model.
    Records all data export operations for audit and tracking.
    """

    __tablename__ = "export_histories"

    # Export info
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Generated file name"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="File storage path"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="File size in bytes"
    )
    download_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Download URL"
    )

    # Export type and format
    export_type: Mapped[ExportType] = mapped_column(
        Enum(ExportType), nullable=False, comment="Type of data being exported"
    )
    export_format: Mapped[ExportFormat] = mapped_column(
        Enum(ExportFormat), nullable=False, comment="Export file format"
    )
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus), nullable=False, default=ExportStatus.PENDING, comment="Export status"
    )

    # Filter criteria
    filter_criteria: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Filter criteria in JSON format"
    )
    hotel_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Selected hotel IDs in JSON format"
    )

    # Statistics
    total_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total rows exported"
    )
    total_hotels: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total hotels exported"
    )
    total_rooms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total rooms exported"
    )

    # Template info
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="Template ID used for export"
    )
    template_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Template name"
    )
    template_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Template version"
    )

    # Processing info
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Processing start time"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Processing completion time"
    )
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Processing time in seconds"
    )

    # Download tracking
    download_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Download count"
    )
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last download time"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Download link expiration time"
    )

    # Operator
    operator_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True, comment="User who initiated the export"
    )
    operator_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Operator name"
    )
    operator_ip: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Operator IP address"
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if failed"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional notes"
    )

    def __repr__(self) -> str:
        return f"<ExportHistory {self.file_name} ({self.status.value})>"

    @property
    def is_downloadable(self) -> bool:
        """Check if export is available for download."""
        if self.status != ExportStatus.COMPLETED:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
