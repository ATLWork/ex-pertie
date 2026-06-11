"""
Initialization helpers for CLI tools.

Provides graceful degradation for Redis - CLI tools can work without cache.
"""

from typing import AsyncGenerator

import typer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.core.redis import RedisService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields a database session for CLI tools.

    Wraps get_db_context() to provide a simple async iteration interface.
    Handles commit/rollback automatically.

    Usage:
        async for session in get_db_session():
            result = await session.execute(query)

    Yields:
        AsyncSession: Database session for executing queries.
    """
    async with get_db_context() as session:
        yield session


async def init_redis_with_fallback() -> bool:
    """
    Initialize Redis connection with graceful degradation.

    Attempts to connect to Redis. If connection fails, logs a warning
    and returns False so CLI tools can skip cache operations.

    Returns:
        bool: True if Redis connected successfully, False otherwise.
    """
    try:
        # RedisService.init() must be called before get_client()
        await RedisService.init()
        # Verify connection by getting client
        RedisService.get_client()
        return True
    except Exception as e:
        typer.echo(
            f"[WARNING] Redis connection failed: {e}",
            err=True,
        )
        typer.echo(
            "[WARNING] Continuing without Redis cache - some features may be slower",
            err=True,
        )
        return False
