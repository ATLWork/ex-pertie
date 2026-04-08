"""
Background task management utilities using ARQ.

This module provides a high-level interface for enqueueing background tasks
to the ARQ task queue.
"""

from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from arq import pool
from arq.connections import RedisSettings
from loguru import logger

from app.core.config import settings
from app.core.worker import get_redis_settings


class BackgroundTaskManager:
    """
    Manager for background tasks using ARQ.

    Provides methods to enqueue export tasks and manage task lifecycle.
    """

    _pool: Optional[pool.ArqPool] = None

    @classmethod
    async def get_pool(cls) -> pool.ArqPool:
        """
        Get or create the ARQ connection pool.

        Returns:
            ArqPool instance for enqueueing tasks
        """
        if cls._pool is None:
            redis_settings = get_redis_settings()
            cls._pool = await pool.ArqPool.from_url(
                redis_settings.url(),
                settings={"redis_settings": redis_settings},
            )
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close the ARQ connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def enqueue_export(
        cls,
        export_type: str,
        export_id: str,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Enqueue an export task.

        Args:
            export_type: Type of export ("hotel" or "room")
            export_id: Export history record ID
            job_id: Optional custom job ID for tracking
            **kwargs: Additional parameters to pass to the task
                - hotel_ids: List of hotel IDs to export
                - room_ids: List of room IDs to export
                - filter_criteria: JSON string of filter criteria
                - export_format: Export format (excel, csv, json, xml)
                - template_id: Template ID to use
                - operator_id: User ID who initiated the export

        Returns:
            Dict containing job information (job_id, enqueue_time, etc.)

        Raises:
            RuntimeError: If unable to enqueue the task
        """
        try:
            arq_pool = await cls.get_pool()

            # Select the appropriate task function
            if export_type == "hotel":
                task_function = "process_hotel_export"
            elif export_type == "room":
                task_function = "process_room_export"
            else:
                raise ValueError(f"Unknown export type: {export_type}")

            # Prepare job data
            job_data = {
                "export_id": export_id,
                **kwargs,
            }

            # Enqueue the job
            job = await arq_pool.enqueue_job(
                task_function,
                export_id=export_id,
                _job_id=job_id,
                **kwargs,
            )

            logger.info(
                f"Enqueued {export_type} export task: "
                f"export_id={export_id}, job_id={job.job_id}"
            )

            return {
                "job_id": job.job_id,
                "task": task_function,
                "export_id": export_id,
                "export_type": export_type,
                "status": "enqueued",
            }

        except Exception as e:
            logger.error(f"Failed to enqueue export task: export_id={export_id}, error={e}")
            raise RuntimeError(f"Failed to enqueue export task: {e}") from e

    @classmethod
    async def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background job.

        Args:
            job_id: The ARQ job ID

        Returns:
            Dict containing job status information, or None if not found
        """
        try:
            arq_pool = await cls.get_pool()
            job = await arq_pool.get_job_result(job_id)

            if job is None:
                return None

            # Parse result info
            result = {
                "job_id": job_id,
                "status": "unknown",
                "enqueue_time": job.enqueue_time.isoformat() if job.enqueue_time else None,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "finish_time": job.finish_time.isoformat() if job.finish_time else None,
                "result": job.result,
                "error": job.error,
                "function": job.function,
            }

            # Determine status based on job state
            if job.success is True:
                result["status"] = "completed"
            elif job.success is False:
                result["status"] = "failed"
            elif job.start_time is not None:
                result["status"] = "processing"
            elif job.enqueue_time is not None:
                result["status"] = "queued"

            return result

        except Exception as e:
            logger.error(f"Failed to get job status: job_id={job_id}, error={e}")
            return None

    @classmethod
    async def cancel_job(cls, job_id: str) -> bool:
        """
        Attempt to cancel a queued job.

        Note: This only works for jobs that haven't started yet.

        Args:
            job_id: The ARQ job ID

        Returns:
            True if cancelled, False if job not found or already running
        """
        try:
            arq_pool = await cls.get_pool()

            # Get current job info
            job = await arq_pool.get_job_info(job_id)

            if job is None:
                return False

            # Can only abort queued jobs
            if job.status == "queued":
                await arq_pool.abort_job(job_id)
                logger.info(f"Cancelled queued job: job_id={job_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to cancel job: job_id={job_id}, error={e}")
            return False

    @classmethod
    async def get_queue_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about the task queue.

        Returns:
            Dict containing queue statistics
        """
        try:
            arq_pool = await cls.get_pool()

            # Get queue info from Redis
            redis_client = arq_pool.redis

            # Count jobs by status
            queued_count = await redis_client.zcard("arq:queue")
            scheduled_count = await redis_client.zcard("arq:scheduled")
            working_count = await redis_client.scard("arq:working")
            failed_count = await redis_client.zcard("arq:failed")

            return {
                "queued": queued_count,
                "scheduled": scheduled_count,
                "working": working_count,
                "failed": failed_count,
            }

        except Exception as e:
            logger.error(f"Failed to get queue stats: error={e}")
            return {
                "queued": 0,
                "scheduled": 0,
                "working": 0,
                "failed": 0,
                "error": str(e),
            }


# Convenience functions

async def enqueue_hotel_export(
    export_id: str,
    hotel_ids: Optional[List[str]] = None,
    filter_criteria: Optional[Dict[str, Any]] = None,
    export_format: str = "excel",
    template_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enqueue a hotel export task.

    Args:
        export_id: Export history record ID
        hotel_ids: List of hotel IDs to export (optional)
        filter_criteria: Filter criteria dict (optional)
        export_format: Export format (excel, csv, json, xml)
        template_id: Template ID to use (optional)
        operator_id: User ID who initiated the export (optional)
        job_id: Optional custom job ID

    Returns:
        Dict containing job information
    """
    import json

    kwargs: Dict[str, Any] = {
        "export_format": export_format,
    }

    if hotel_ids:
        kwargs["hotel_ids"] = json.dumps(hotel_ids)
    if filter_criteria:
        kwargs["filter_criteria"] = json.dumps(filter_criteria)
    if template_id:
        kwargs["template_id"] = template_id
    if operator_id:
        kwargs["operator_id"] = operator_id

    return await BackgroundTaskManager.enqueue_export(
        export_type="hotel",
        export_id=export_id,
        job_id=job_id,
        **kwargs,
    )


async def enqueue_room_export(
    export_id: str,
    hotel_ids: Optional[List[str]] = None,
    room_ids: Optional[List[str]] = None,
    filter_criteria: Optional[Dict[str, Any]] = None,
    export_format: str = "excel",
    template_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enqueue a room export task.

    Args:
        export_id: Export history record ID
        hotel_ids: List of hotel IDs whose rooms to export (optional)
        room_ids: List of specific room IDs to export (optional)
        filter_criteria: Filter criteria dict (optional)
        export_format: Export format (excel, csv, json, xml)
        template_id: Template ID to use (optional)
        operator_id: User ID who initiated the export (optional)
        job_id: Optional custom job ID

    Returns:
        Dict containing job information
    """
    import json

    kwargs: Dict[str, Any] = {
        "export_format": export_format,
    }

    if hotel_ids:
        kwargs["hotel_ids"] = json.dumps(hotel_ids)
    if room_ids:
        kwargs["room_ids"] = json.dumps(room_ids)
    if filter_criteria:
        kwargs["filter_criteria"] = json.dumps(filter_criteria)
    if template_id:
        kwargs["template_id"] = template_id
    if operator_id:
        kwargs["operator_id"] = operator_id

    return await BackgroundTaskManager.enqueue_export(
        export_type="room",
        export_id=export_id,
        job_id=job_id,
        **kwargs,
    )
