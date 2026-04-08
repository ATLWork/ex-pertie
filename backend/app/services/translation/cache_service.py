"""
Translation Cache Service.

Implements T033: Translation Result Cache Service
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.redis import RedisService
from app.schemas.translation import TranslationSource


class TranslationCacheService:
    """
    Redis-based translation cache service.

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
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Serialize translation result for caching.

        Args:
            translated_text: Translated text
            source: Translation source
            original_text: Original text
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            JSON string
        """
        value = {
            "translated_text": translated_text,
            "source": source.value,
            "original_text": original_text,
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
            cached = await RedisService.get(key)

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
                confidence=confidence,
                metadata=metadata,
            )

            await RedisService.set(key, value, ex=self.ttl)

            logger.debug(
                f"Cached translation",
                extra={
                    "key": key,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "ttl": self.ttl,
                },
            )
            return True

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
            await RedisService.delete(key)
            return True
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
            client = RedisService.get_client()
            keys = []
            async for key in client.scan_iter(match=f"{self.CACHE_KEY_PREFIX}:*"):
                keys.append(key)

            if keys:
                await RedisService.delete(*keys)
                logger.info(f"Cleared {len(keys)} translation cache keys")
                return len(keys)
            return 0

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
            client = RedisService.get_client()
            count = 0
            async for _ in client.scan_iter(match=f"{self.CACHE_KEY_PREFIX}:*"):
                count += 1

            return {
                "total_cached": count,
                "ttl_seconds": self.ttl,
                "key_prefix": self.CACHE_KEY_PREFIX,
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "total_cached": 0,
                "error": str(e),
            }


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
