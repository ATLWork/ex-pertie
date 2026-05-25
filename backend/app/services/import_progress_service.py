"""
Import progress tracking service.

Provides real-time progress tracking for import operations using Redis.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.redis import RedisService

logger = logging.getLogger(__name__)


@dataclass
class ImportProgress:
    """Represents import progress for a specific import operation."""

    import_id: str
    total_rows: int = 0
    processed_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    skipped_rows: int = 0
    current_row: Optional[int] = None
    status: str = "pending"  # pending, processing, completed, failed
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_rows == 0:
            return 0.0
        return round(self.processed_rows / self.total_rows * 100, 2)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_rows == 0:
            return 0.0
        return round(self.success_rows / self.processed_rows * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "import_id": self.import_id,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "skipped_rows": self.skipped_rows,
            "current_row": self.current_row,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "success_rate": self.success_rate,
            "errors": self.errors,
            "warnings": self.warnings,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }


class ImportProgressService:
    """
    Service for tracking import progress using Redis.

    Provides real-time progress tracking for hotel and room import operations.
    Progress is stored in Redis hashes with automatic expiration.
    """

    # Redis key prefixes
    PROGRESS_KEY_PREFIX = "import:progress:"
    PROGRESS_TTL = 86400 * 7  # 7 days expiration

    def __init__(self) -> None:
        """Initialize the import progress service."""
        pass

    def _get_progress_key(self, import_id: str) -> str:
        """
        Get Redis key for import progress.

        Args:
            import_id: Import ID

        Returns:
            Redis key string
        """
        return f"{self.PROGRESS_KEY_PREFIX}{import_id}"

    async def create_progress(
        self,
        import_id: str,
        total_rows: int,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> ImportProgress:
        """
        Create a new progress tracking entry.

        Args:
            import_id: Unique import ID
            total_rows: Total number of rows to process
            operator_id: Optional operator ID
            operator_name: Optional operator name

        Returns:
            ImportProgress instance
        """
        progress = ImportProgress(
            import_id=import_id,
            total_rows=total_rows,
            status="pending",
            started_at=datetime.utcnow().isoformat(),
        )

        if operator_id:
            progress.__dict__["operator_id"] = operator_id
        if operator_name:
            progress.__dict__["operator_name"] = operator_name

        await self._save_progress(progress)
        return progress

    async def update_progress(
        self,
        import_id: str,
        processed_rows: Optional[int] = None,
        success_rows: Optional[int] = None,
        failed_rows: Optional[int] = None,
        skipped_rows: Optional[int] = None,
        current_row: Optional[int] = None,
        status: Optional[str] = None,
        error: Optional[Dict[str, Any]] = None,
        warning: Optional[Dict[str, Any]] = None,
    ) -> Optional[ImportProgress]:
        """
        Update progress for an import operation.

        Args:
            import_id: Import ID
            processed_rows: Number of processed rows
            success_rows: Number of successful rows
            failed_rows: Number of failed rows
            skipped_rows: Number of skipped rows
            current_row: Current row being processed
            status: Import status
            error: Error information
            warning: Warning information

        Returns:
            Updated ImportProgress or None if not found
        """
        progress = await self.get_progress(import_id)
        if progress is None:
            logger.warning(f"Progress not found for import_id: {import_id}")
            return None

        # Update fields
        if processed_rows is not None:
            progress.processed_rows = processed_rows
        if success_rows is not None:
            progress.success_rows = success_rows
        if failed_rows is not None:
            progress.failed_rows = failed_rows
        if skipped_rows is not None:
            progress.skipped_rows = skipped_rows
        if current_row is not None:
            progress.current_row = current_row
        if status is not None:
            progress.status = status

        if error:
            progress.errors.append(error)
        if warning:
            progress.warnings.append(warning)

        progress.updated_at = datetime.utcnow().isoformat()

        await self._save_progress(progress)
        return progress

    async def mark_completed(
        self,
        import_id: str,
        status: str = "completed",
    ) -> Optional[ImportProgress]:
        """
        Mark an import as completed.

        Args:
            import_id: Import ID
            status: Final status (completed, failed, partial)

        Returns:
            Updated ImportProgress or None if not found
        """
        progress = await self.get_progress(import_id)
        if progress is None:
            return None

        progress.status = status
        progress.completed_at = datetime.utcnow().isoformat()
        progress.updated_at = datetime.utcnow().isoformat()

        await self._save_progress(progress)
        return progress

    async def add_error(
        self,
        import_id: str,
        error: Dict[str, Any],
    ) -> Optional[ImportProgress]:
        """
        Add an error to the progress.

        Args:
            import_id: Import ID
            error: Error information

        Returns:
            Updated ImportProgress or None if not found
        """
        return await self.update_progress(import_id, error=error)

    async def add_warning(
        self,
        import_id: str,
        warning: Dict[str, Any],
    ) -> Optional[ImportProgress]:
        """
        Add a warning to the progress.

        Args:
            import_id: Import ID
            warning: Warning information

        Returns:
            Updated ImportProgress or None if not found
        """
        return await self.update_progress(import_id, warning=warning)

    async def get_progress(self, import_id: str) -> Optional[ImportProgress]:
        """
        Get progress for an import operation.

        Args:
            import_id: Import ID

        Returns:
            ImportProgress or None if not found
        """
        try:
            data = await RedisService.hgetall(self._get_progress_key(import_id))
            if not data:
                return None

            progress = ImportProgress(
                import_id=import_id,
                total_rows=int(data.get("total_rows", 0)),
                processed_rows=int(data.get("processed_rows", 0)),
                success_rows=int(data.get("success_rows", 0)),
                failed_rows=int(data.get("failed_rows", 0)),
                skipped_rows=int(data.get("skipped_rows", 0)),
                current_row=int(data["current_row"]) if data.get("current_row") else None,
                status=data.get("status", "pending"),
                errors=json.loads(data["errors"]) if data.get("errors") else [],
                warnings=json.loads(data["warnings"]) if data.get("warnings") else [],
                started_at=data.get("started_at"),
                updated_at=data.get("updated_at"),
                completed_at=data.get("completed_at"),
            )

            # Optional fields
            if data.get("operator_id"):
                progress.__dict__["operator_id"] = data["operator_id"]
            if data.get("operator_name"):
                progress.__dict__["operator_name"] = data["operator_name"]

            return progress
        except Exception as e:
            logger.error(f"Failed to get progress for {import_id}: {e}")
            return None

    async def _save_progress(self, progress: ImportProgress) -> None:
        """
        Save progress to Redis.

        Args:
            progress: ImportProgress instance
        """
        try:
            data: Dict[str, Any] = {
                "total_rows": str(progress.total_rows),
                "processed_rows": str(progress.processed_rows),
                "success_rows": str(progress.success_rows),
                "failed_rows": str(progress.failed_rows),
                "skipped_rows": str(progress.skipped_rows),
                "current_row": str(progress.current_row) if progress.current_row else "",
                "status": progress.status,
                "errors": json.dumps(progress.errors, ensure_ascii=False),
                "warnings": json.dumps(progress.warnings, ensure_ascii=False),
                "started_at": progress.started_at or "",
                "updated_at": progress.updated_at or "",
                "completed_at": progress.completed_at or "",
            }

            if hasattr(progress, "operator_id") and progress.operator_id:
                data["operator_id"] = progress.operator_id
            if hasattr(progress, "operator_name") and progress.operator_name:
                data["operator_name"] = progress.operator_name

            key = self._get_progress_key(progress.import_id)
            await RedisService.hset(key, "total_rows", data["total_rows"])
            await RedisService.hset(key, "processed_rows", data["processed_rows"])
            await RedisService.hset(key, "success_rows", data["success_rows"])
            await RedisService.hset(key, "failed_rows", data["failed_rows"])
            await RedisService.hset(key, "skipped_rows", data["skipped_rows"])
            await RedisService.hset(key, "current_row", data["current_row"])
            await RedisService.hset(key, "status", data["status"])
            await RedisService.hset(key, "errors", data["errors"])
            await RedisService.hset(key, "warnings", data["warnings"])
            await RedisService.hset(key, "started_at", data["started_at"])
            await RedisService.hset(key, "updated_at", data["updated_at"])
            await RedisService.hset(key, "completed_at", data["completed_at"])

            if "operator_id" in data:
                await RedisService.hset(key, "operator_id", data["operator_id"])
            if "operator_name" in data:
                await RedisService.hset(key, "operator_name", data["operator_name"])

            # Set expiration
            await RedisService.expire(key, self.PROGRESS_TTL)

        except Exception as e:
            logger.error(f"Failed to save progress for {progress.import_id}: {e}")

    async def delete_progress(self, import_id: str) -> bool:
        """
        Delete progress tracking for an import operation.

        Args:
            import_id: Import ID

        Returns:
            True if deleted successfully
        """
        try:
            await RedisService.delete(self._get_progress_key(import_id))
            return True
        except Exception as e:
            logger.error(f"Failed to delete progress for {import_id}: {e}")
            return False

    async def list_progress(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ImportProgress]:
        """
        List all progress entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of ImportProgress instances
        """
        # This requires Redis SCAN which is not directly available
        # For now, return empty list - can be enhanced with proper SCAN implementation
        logger.warning("list_progress not fully implemented - requires Redis SCAN")
        return []


# Singleton instance
_import_progress_service: Optional[ImportProgressService] = None


def get_import_progress_service() -> ImportProgressService:
    """Get import progress service singleton."""
    global _import_progress_service
    if _import_progress_service is None:
        _import_progress_service = ImportProgressService()
    return _import_progress_service