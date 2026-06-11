"""
Translation Cache Service.

Chain of Responsibility: Redis → SQLite → None.
Automatically falls back to SQLite when Redis is unavailable.
Falls back to no-cache when both are unavailable.

Implements T033: Translation Result Cache Service
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.redis import RedisService
from app.core.database import get_db_context
from app.schemas.translation import TranslationSource
from app.services.translation.sqlite_cache_backend import SQLiteCacheBackend


class _RedisBackend:
    async def get(self, key: str) -> Optional[str]:
        return await RedisService.get(key)

    async def set(self, key: str, value: str, ttl: int) -> bool:
        await RedisService.set(key, value, ex=ttl)
        return True

    async def delete(self, key: str) -> bool:
        await RedisService.delete(key)
        return True

    async def clear_all(self) -> int:
        client = RedisService.get_client()
        keys = []
        async for key in client.scan_iter(match="translation:*"):
            keys.append(key)
        if keys:
            await RedisService.delete(*keys)
            return len(keys)
        return 0

    async def get_stats(self) -> Dict[str, Any]:
        client = RedisService.get_client()
        count = sum(1 async for _ in client.scan_iter(match="translation:*"))
        return {"total_cached": count, "backend": "redis"}


class _SqliteBackend:
    def __init__(self):
        self._backend = SQLiteCacheBackend()
    
    async def get(self, key: str) -> Optional[str]:
        async with get_db_context() as db:
            return await self._backend.get(db, key)

    async def set(self, key: str, value: str, ttl: int) -> bool:
        async with get_db_context() as db:
            # value 是 JSON 字符串，解析后调用 structured backend.set
            data = json.loads(value)
            return await self._backend.set(
                db=db,
                cache_key=key,
                ttl=ttl,
                text=data.get("original_text", ""),
                source_lang=data.get("source_lang", ""),
                target_lang=data.get("target_lang", ""),
                translated_text=data.get("translated_text", ""),
                source=data.get("source", "N/A"),
                confidence=data.get("confidence"),
                metadata=data.get("metadata"),
            )

    async def delete(self, key: str) -> bool:
        async with get_db_context() as db:
            return await self._backend.delete(db, key)

    async def clear_all(self) -> int:
        async with get_db_context() as db:
            success = await self._backend.clear_all(db)
            return -1 if success else 0  # -1 signals success but unknown count

    async def get_stats(self) -> Dict[str, Any]:
        async with get_db_context() as db:
            s = await self._backend.stats(db)
            return {"total_cached": s.get("total_cached", 0), "backend": "sqlite"}


class TranslationCacheService:
    """
    Chain-based translation cache service (Redis → SQLite).

    Cache Structure:
        - Key: translation:{source_lang}:{target_lang}:{hash}
        - Value: JSON string with translation result
        - TTL: Configurable (default 24 hours)
    """

    CACHE_KEY_PREFIX = "translation"
    DEFAULT_TTL = 86400  # 24 hours

    def __init__(self, ttl: Optional[int] = None):
        """
        Initialize cache service.

        Args:
            ttl: Cache TTL in seconds (default from settings)
        """
        self.ttl = ttl or settings.TRANSLATION_CACHE_TTL or self.DEFAULT_TTL
        self._redis = _RedisBackend()
        self._sqlite = _SqliteBackend()

    async def _try_backends(self, fn_name, *args, default=None):
        """尝试Redis→SQLite，返回第一个成功的结果"""
        for backend, name in [(self._redis, "redis"), (self._sqlite, "sqlite")]:
            try:
                fn = getattr(backend, fn_name)
                result = await fn(*args)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"{name} {fn_name} failed: {e}, trying next backend")
        return default

    def _generate_cache_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        use_ai_enhance: bool = False,
    ) -> str:
        """
        Generate cache key for translation.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            use_ai_enhance: Whether AI enhancement was used

        Returns:
            Cache key string
        """
        # Normalize text for consistent hashing
        normalized_text = text.strip().lower()
        text_hash = hashlib.md5(normalized_text.encode("utf-8")).hexdigest()[:16]

        # Include enhancement flag in key
        enhance_flag = "ai" if use_ai_enhance else "mt"

        return (
            f"{self.CACHE_KEY_PREFIX}:"
            f"{source_lang.lower()}:"
            f"{target_lang.lower()}:"
            f"{enhance_flag}:"
            f"{text_hash}"
        )

    def _serialize_cache_value(
        self,
        translated_text: str,
        source: TranslationSource,
        original_text: str,
        source_lang: str,
        target_lang: str,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Serialize translation result for caching.

        Args:
            translated_text: Translated text
            source: Translation source
            original_text: Original text
            source_lang: Source language
            target_lang: Target language
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            JSON string
        """
        value = {
            "translated_text": translated_text,
            "source": source.value,
            "original_text": original_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": confidence,
            "metadata": metadata or {},
        }
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_cache_value(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Deserialize cached value.

        Args:
            value: Cached JSON string

        Returns:
            Deserialized dictionary or None
        """
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    async def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        use_ai_enhance: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached translation if exists.

        Args:
            text: Original text
            source_lang: Source language
            target_lang: Target language
            use_ai_enhance: Whether AI enhancement is expected

        Returns:
            Cached translation result or None
        """
        try:
            key = self._generate_cache_key(text, source_lang, target_lang, use_ai_enhance)
            cached = await self._try_backends("get", key, default=None)

            if cached:
                result = self._deserialize_cache_value(cached)
                if result:
                    logger.debug(
                        f"Cache hit for translation",
                        extra={
                            "key": key,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                        },
                    )
                    result["cached"] = True
                    return result

            return None

        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def set(
        self,
        text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        source: TranslationSource,
        use_ai_enhance: bool = False,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Cache translation result.

        Args:
            text: Original text
            translated_text: Translated text
            source_lang: Source language
            target_lang: Target language
            source: Translation source
            use_ai_enhance: Whether AI enhancement was used
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            True if cached successfully
        """
        try:
            key = self._generate_cache_key(text, source_lang, target_lang, use_ai_enhance)
            value = self._serialize_cache_value(
                translated_text=translated_text,
                source=source,
                original_text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=confidence,
                metadata=metadata,
            )

            success = await self._try_backends("set", key, value, self.ttl, default=False)

            logger.debug(
                f"Cached translation",
                extra={
                    "key": key,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "ttl": self.ttl,
                },
            )
            return success

        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    async def delete(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        use_ai_enhance: bool = False,
    ) -> bool:
        """
        Delete cached translation.

        Args:
            text: Original text
            source_lang: Source language
            target_lang: Target language
            use_ai_enhance: Whether AI enhancement was used

        Returns:
            True if deleted successfully
        """
        try:
            key = self._generate_cache_key(text, source_lang, target_lang, use_ai_enhance)
            return await self._try_backends("delete", key, default=False)
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False

    async def get_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        use_ai_enhance: bool = False,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get multiple cached translations.

        Args:
            texts: List of texts
            source_lang: Source language
            target_lang: Target language
            use_ai_enhance: Whether AI enhancement is expected

        Returns:
            Dictionary mapping text to cached result
        """
        results = {}
        for text in texts:
            results[text] = await self.get(text, source_lang, target_lang, use_ai_enhance)
        return results

    async def set_batch(
        self,
        items: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
        use_ai_enhance: bool = False,
    ) -> int:
        """
        Cache multiple translations.

        Args:
            items: List of translation items with text, translated_text, source, etc.
            source_lang: Source language
            target_lang: Target language
            use_ai_enhance: Whether AI enhancement was used

        Returns:
            Number of successfully cached items
        """
        count = 0
        for item in items:
            success = await self.set(
                text=item.get("text", ""),
                translated_text=item.get("translated_text", ""),
                source_lang=source_lang,
                target_lang=target_lang,
                source=item.get("source", TranslationSource.MACHINE),
                use_ai_enhance=use_ai_enhance,
                confidence=item.get("confidence"),
                metadata=item.get("metadata"),
            )
            if success:
                count += 1
        return count

    async def clear_all(self) -> int:
        """
        Clear all translation cache.

        Returns:
            Number of keys deleted
        """
        try:
            return await self._try_backends("clear_all", default=0)
        except Exception as e:
            logger.error(f"Failed to clear translation cache: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        try:
            stats = await self._try_backends("get_stats", default={"total_cached": 0, "error": "all backends unavailable"})
            stats.update({
                "ttl_seconds": self.ttl,
                "key_prefix": self.CACHE_KEY_PREFIX,
            })
            return stats
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "total_cached": 0,
                "error": str(e),
            }

    async def active_backend(self) -> str:
        """
        Get the name of the currently active backend.

        Returns:
            "redis", "sqlite", or "none"
        """
        try:
            client = RedisService.get_client()
            await client.ping()
            return "redis"
        except Exception:
            pass

        try:
            async with get_db_context() as db:
                if await self._sqlite._backend.is_available(db):
                    return "sqlite"
        except Exception:
            pass

        return "none"


# Singleton instance
_cache_service: Optional[TranslationCacheService] = None


def get_cache_service() -> TranslationCacheService:
    """
    Get or create cache service instance.

    Returns:
        TranslationCacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = TranslationCacheService()
    return _cache_service
