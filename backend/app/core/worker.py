"""
ARQ worker configuration for background task processing.

ARQ is an async task queue library that uses Redis as the message broker.
"""

from typing import Any, Dict, Optional

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings


def get_redis_settings() -> RedisSettings:
    """
    Get ARQ Redis connection settings.

    Returns:
        RedisSettings for ARQ worker
    """
    # Parse Redis URL to extract components
    redis_url = settings.REDIS_URL
    # Default values
    host = "localhost"
    port = 6379
    database = 0
    password: Optional[str] = None

    # Parse URL if present
    if redis_url.startswith("redis://"):
        import urllib.parse

        parsed = urllib.parse.urlparse(redis_url)
        if parsed.hostname:
            host = parsed.hostname
        if parsed.port:
            port = parsed.port
        if parsed.path and len(parsed.path) > 1:
            try:
                database = int(parsed.path[1:])
            except ValueError:
                pass
        if parsed.password:
            password = parsed.password

    return RedisSettings(
        host=host,
        port=port,
        database=database,
        password=password,
    )


# ARQ Worker settings
WORKER_SETTINGS = {
    "redis_settings": get_redis_settings(),
    "job_timeout": 300,  # 5 minutes max per job
    "keep_result": 3600,  # Keep results for 1 hour
    "keep_result_days": 7,  # Keep results in Redis for 7 days
    "max_tries": 3,  # Retry failed jobs up to 3 times
    "retry_delay": 60,  # Wait 60 seconds before retry
    "max_concurrent_tasks": 5,  # Max 5 concurrent tasks
    "burst_mode": False,  # Don't exit when queue is empty in web services
}


async def startup(ctx: Dict[str, Any]) -> None:
    """
    ARQ worker startup function.
    Called when the worker starts.

    Args:
        ctx: ARQ context dictionary
    """
    from app.core.database import engine
    from app.core.redis import RedisService

    # Initialize database connection
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    # Initialize Redis
    await RedisService.init()

    print("ARQ Worker started")


async def shutdown(ctx: Dict[str, Any]) -> None:
    """
    ARQ worker shutdown function.
    Called when the worker stops.

    Args:
        ctx: ARQ context dictionary
    """
    from app.core.redis import RedisService

    await RedisService.close()
    print("ARQ Worker stopped")


# Cron jobs configuration (optional)
def get_cron_jobs() -> list:
    """
    Get list of cron jobs for scheduled tasks.

    Returns:
        List of cron job configurations
    """
    return [
        # Example: Run cleanup every day at 3 AM
        # cron(coro=cleanup_old_exports, hour=3, minute=0),
    ]
