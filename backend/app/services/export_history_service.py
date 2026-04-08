"""
Export history CRUD service.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_history import (
    ExportFormat,
    ExportHistory,
    ExportStatus,
    ExportType,
)
from app.services.base import CRUDBase


class ExportHistoryService(CRUDBase[ExportHistory, Any, Any]):
    """
    CRUD service for ExportHistory model.
    """

    async def get_by_status(
        self,
        db: AsyncSession,
        status: ExportStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ExportHistory]:
        """
        Get export histories by status.

        Args:
            db: Database session
            status: Export status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ExportHistory records
        """
        query = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_operator(
        self,
        db: AsyncSession,
        operator_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ExportHistory]:
        """
        Get export histories by operator.

        Args:
            db: Database session
            operator_id: Operator user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ExportHistory records
        """
        query = (
            select(self.model)
            .where(self.model.operator_id == operator_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        id: str,
        status: ExportStatus,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        total_rows: Optional[int] = None,
        total_hotels: Optional[int] = None,
        total_rooms: Optional[int] = None,
        processing_time: Optional[float] = None,
        download_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ExportHistory]:
        """
        Update export status and related fields.

        Args:
            db: Database session
            id: Export history ID
            status: New status
            file_path: Path to generated file
            file_size: Size of generated file in bytes
            total_rows: Total rows exported
            total_hotels: Total hotels exported
            total_rooms: Total rooms exported
            processing_time: Time taken for processing in seconds
            download_url: URL to download the file
            error_message: Error message if failed

        Returns:
            Updated ExportHistory or None
        """
        from datetime import datetime

        export = await self.get(db, id)
        if not export:
            return None

        export.status = status

        if status == ExportStatus.PROCESSING:
            export.started_at = datetime.utcnow()
        elif status == ExportStatus.COMPLETED:
            export.completed_at = datetime.utcnow()
        elif status == ExportStatus.FAILED:
            export.completed_at = datetime.utcnow()

        if file_path is not None:
            export.file_path = file_path
        if file_size is not None:
            export.file_size = file_size
        if total_rows is not None:
            export.total_rows = total_rows
        if total_hotels is not None:
            export.total_hotels = total_hotels
        if total_rooms is not None:
            export.total_rooms = total_rooms
        if processing_time is not None:
            export.processing_time = processing_time
        if download_url is not None:
            export.download_url = download_url
        if error_message is not None:
            export.error_message = error_message

        db.add(export)
        await db.flush()
        await db.refresh(export)
        return export

    async def increment_download(
        self,
        db: AsyncSession,
        id: str,
    ) -> Optional[ExportHistory]:
        """
        Increment download count and update last download time.

        Args:
            db: Database session
            id: Export history ID

        Returns:
            Updated ExportHistory or None
        """
        from datetime import datetime

        export = await self.get(db, id)
        if not export:
            return None

        export.download_count += 1
        export.last_downloaded_at = datetime.utcnow()

        db.add(export)
        await db.flush()
        await db.refresh(export)
        return export

    async def get_statistics(
        self,
        db: AsyncSession,
        operator_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get export statistics.

        Args:
            db: Database session
            operator_id: Optional operator ID to filter by

        Returns:
            Dict containing statistics
        """
        query = select(func.count()).select_from(self.model)

        if operator_id:
            query = query.where(self.model.operator_id == operator_id)

        # Total count
        total_result = await db.execute(query)
        total = total_result.scalar_one()

        # Count by status
        status_counts = {}
        for status in ExportStatus:
            status_query = (
                select(func.count())
                .select_from(self.model)
                .where(self.model.status == status)
            )
            if operator_id:
                status_query = status_query.where(self.model.operator_id == operator_id)
            result = await db.execute(status_query)
            status_counts[status.value] = result.scalar_one()

        # Count by format
        format_counts = {}
        for fmt in ExportFormat:
            fmt_query = (
                select(func.count())
                .select_from(self.model)
                .where(self.model.export_format == fmt)
            )
            if operator_id:
                fmt_query = fmt_query.where(self.model.operator_id == operator_id)
            result = await db.execute(fmt_query)
            format_counts[fmt.value] = result.scalar_one()

        return {
            "total": total,
            "by_status": status_counts,
            "by_format": format_counts,
        }


# Singleton instance
export_history_service = ExportHistoryService(ExportHistory)
