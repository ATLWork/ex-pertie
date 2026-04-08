"""
Redis connection and cache service.
"""

from typing import Any, Optional

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisService:
    """Redis service for caching and session management."""

    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    @classmethod
    async def init(cls):
        """Initialize Redis connection pool."""
        if cls._pool is not None:
            return

        cls._pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD or None,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True,
        )
        cls._client = Redis(connection_pool=cls._pool)

    @classmethod
    async def close(cls):
        """Close Redis connection pool."""
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None

    @classmethod
    def get_client(cls) -> Redis:
        """Get Redis client instance."""
        if cls._client is None:
            raise RuntimeError("Redis not initialized. Call init() first.")
        return cls._client

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """Get value by key."""
        return await cls.get_client().get(key)

    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set key-value pair.

        Args:
            key: Redis key
            value: Value to store
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key does not exist
            xx: Only set if key exists
        """
        return await cls.get_client().set(
            key, value, ex=ex, px=px, nx=nx, xx=xx
        )

    @classmethod
    async def delete(cls, *keys: str) -> int:
        """Delete one or more keys."""
        return await cls.get_client().delete(*keys)

    @classmethod
    async def exists(cls, *keys: str) -> int:
        """Check if keys exist."""
        return await cls.get_client().exists(*keys)

    @classmethod
    async def expire(cls, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        return await cls.get_client().expire(key, seconds)

    @classmethod
    async def ttl(cls, key: str) -> int:
        """Get remaining TTL for a key."""
        return await cls.get_client().ttl(key)

    @classmethod
    async def incr(cls, key: str) -> int:
        """Increment key value by 1."""
        return await cls.get_client().incr(key)

    @classmethod
    async def incrby(cls, key: str, amount: int) -> int:
        """Increment key value by amount."""
        return await cls.get_client().incrby(key, amount)

    @classmethod
    async def hset(cls, name: str, key: str, value: Any) -> int:
        """Set hash field."""
        return await cls.get_client().hset(name, key, value)

    @classmethod
    async def hget(cls, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        return await cls.get_client().hget(name, key)

    @classmethod
    async def hgetall(cls, name: str) -> dict:
        """Get all hash fields."""
        return await cls.get_client().hgetall(name)

    @classmethod
    async def hdel(cls, name: str, *keys: str) -> int:
        """Delete hash fields."""
        return await cls.get_client().hdel(name, *keys)


async def get_redis() -> Redis:
    """
    Dependency for getting Redis client.
    """
    return RedisService.get_client()
