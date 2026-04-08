"""
Import history model for tracking data imports.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ImportType(str, enum.Enum):
    """Import type enum."""

    HOTEL = "hotel"  # Hotel data import
    ROOM = "room"  # Room data import
    MIXED = "mixed"  # Mixed import (hotel + room)


class ImportStatus(str, enum.Enum):
    """Import status enum."""

    PENDING = "pending"  # Pending
    PROCESSING = "processing"  # Processing
    COMPLETED = "completed"  # Completed
    FAILED = "failed"  # Failed
    PARTIAL = "partial"  # Partially succeeded


class ImportHistory(BaseModel):
    """
    Import history model.
    Records all data import operations for audit and tracking.
    """

    __tablename__ = "import_histories"

    # Import info
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Original file name"
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="File storage path"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="File size in bytes"
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="File MD5 hash for deduplication"
    )

    # Import type and status
    import_type: Mapped[ImportType] = mapped_column(
        Enum(ImportType), nullable=False, comment="Type of data being imported"
    )
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus), nullable=False, default=ImportStatus.PENDING, comment="Import status"
    )

    # Statistics
    total_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total rows in file"
    )
    success_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Successfully imported rows"
    )
    failed_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Failed rows"
    )
    skipped_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Skipped rows (duplicates)"
    )

    # Error tracking
    error_log: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error log in JSON format"
    )
    warning_log: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Warning log in JSON format"
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

    # Operator
    operator_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True, comment="User who initiated the import"
    )
    operator_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Operator name"
    )
    operator_ip: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Operator IP address"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Additional notes"
    )

    def __repr__(self) -> str:
        return f"<ImportHistory {self.file_name} ({self.status.value})>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_rows == 0:
            return 0.0
        return round(self.success_rows / self.total_rows * 100, 2)

    @property
    def is_completed(self) -> bool:
        """Check if import is completed (success or failure)."""
        return self.status in (ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.PARTIAL)
