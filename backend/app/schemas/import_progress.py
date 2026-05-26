"""
Import progress schemas for API request/response validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportProgressResponse(BaseModel):
    """Import progress response schema."""

    model_config = ConfigDict(from_attributes=True)

    import_id: str = Field(..., description="Import ID")
    total_rows: int = Field(..., description="Total number of rows")
    processed_rows: int = Field(..., description="Number of processed rows")
    success_rows: int = Field(..., description="Number of successful rows")
    failed_rows: int = Field(..., description="Number of failed rows")
    skipped_rows: int = Field(..., description="Number of skipped rows")
    current_row: Optional[int] = Field(None, description="Current row being processed")
    status: str = Field(..., description="Import status")
    progress_percentage: float = Field(..., description="Progress percentage")
    success_rate: float = Field(..., description="Success rate percentage")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Warnings")
    started_at: Optional[str] = Field(None, description="Start time in ISO format")
    updated_at: Optional[str] = Field(None, description="Last update time in ISO format")
    completed_at: Optional[str] = Field(None, description="Completion time in ISO format")
    operator_id: Optional[str] = Field(None, description="Operator ID")
    operator_name: Optional[str] = Field(None, description="Operator name")