"""
Import history schemas for API request/response validation.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.import_history import ImportStatus, ImportType


class ImportHistoryBase(BaseModel):
    """Base import history schema."""

    file_name: str = Field(..., description="Original file name")
    import_type: ImportType = Field(..., description="Type of data being imported")
    status: ImportStatus = Field(..., description="Import status")


class ImportHistoryResponse(ImportHistoryBase):
    """Import history response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    file_size: int
    file_hash: Optional[str] = None
    total_rows: int
    success_rows: int
    failed_rows: int
    skipped_rows: int
    error_log: Optional[str] = None
    warning_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    operator_ip: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_rows == 0:
            return 0.0
        return round(self.success_rows / self.total_rows * 100, 2)

    @property
    def errors_list(self) -> List[Dict[str, Any]]:
        """Parse error log JSON to list."""
        if not self.error_log:
            return []
        try:
            return json.loads(self.error_log)
        except json.JSONDecodeError:
            return []

    @property
    def warnings_list(self) -> List[Dict[str, Any]]:
        """Parse warning log JSON to list."""
        if not self.warning_log:
            return []
        try:
            return json.loads(self.warning_log)
        except json.JSONDecodeError:
            return []


class ImportHistoryBriefResponse(BaseModel):
    """Brief import history response for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    import_type: ImportType
    status: ImportStatus
    total_rows: int
    success_rows: int
    failed_rows: int
    skipped_rows: int
    success_rate: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    operator_name: Optional[str] = None
    created_at: datetime


class ImportErrorDetail(BaseModel):
    """Single import error detail."""

    row: Any = Field(..., description="Row number or 'file' for file-level errors")
    data: Optional[Dict[str, Any]] = Field(None, description="Row data if available")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    message: Optional[str] = Field(None, description="Error message for file-level errors")


class ImportErrorsResponse(BaseModel):
    """Import errors response schema."""

    import_id: str
    file_name: str
    total_errors: int
    errors: List[ImportErrorDetail] = Field(default_factory=list)


class ImportResultRow(BaseModel):
    """Single row result in import response."""

    row: int = Field(..., description="Row number")
    success: bool = Field(..., description="Whether import succeeded")
    hotel_id: Optional[str] = Field(None, description="Created hotel ID if successful")
    room_id: Optional[str] = Field(None, description="Created room ID if successful")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Row errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Row warnings")


class ImportResultResponse(BaseModel):
    """Import result response schema."""

    import_id: str
    file_name: str
    status: ImportStatus
    total_rows: int
    success_rows: int
    failed_rows: int
    skipped_rows: int
    success_rate: float
    processing_time: float
    rows: List[ImportResultRow] = Field(default_factory=list)
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)


class ImportHistoryListResponse(BaseModel):
    """Import history list response schema."""

    imports: List[ImportHistoryBriefResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
