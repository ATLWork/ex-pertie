"""
SQLite-based translation cache backend.

Stores cached translations in the database with TTL support.
Adapted to the actual TranslationCache model which uses structured
fields (text, translated_text, source_lang, etc.) rather than
a single value blob.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.translation_cache import TranslationCache


class SQLiteCacheBackend:
    """SQLite translation cache with TTL support.

    Provides the same get/set/delete interface as the Redis cache backend
    but uses the SQLite/PostgreSQL database for storage.
    """

    async def get(self, db: AsyncSession, cache_key: str) -> Optional[str]:
        """Get cached translation if not expired.

        Args:
            db: Database session
            cache_key: Cache key

        Returns:
            JSON string of cached result, or None if not found/expired
        """
        try:
            stmt = select(TranslationCache).where(
                TranslationCache.cache_key == cache_key,
                TranslationCache.ttl_expires_at > datetime.now(),
            )
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                return None

            logger.debug(f"SQLite cache hit: {cache_key}")

            # Reconstruct the JSON value from structured fields
            # to match the interface expected by cache_service
            value: Dict[str, Any] = {
                "translated_text": record.translated_text,
                "source": record.source,
                "original_text": record.text,
                "confidence": record.confidence,
            }

            if record.metadata_json:
                try:
                    value["metadata"] = json.loads(record.metadata_json)
                except (json.JSONDecodeError, TypeError):
                    value["metadata"] = {}
            else:
                value["metadata"] = {}

            return json.dumps(value, ensure_ascii=False)

        except Exception as e:
            logger.error(f"SQLite cache get error: {e}")
            return None

    async def set(
        self,
        db: AsyncSession,
        cache_key: str,
        ttl: int,
        text: str,
        source_lang: str,
        target_lang: str,
        translated_text: str,
        source: str = "N/A",
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set cache entry with TTL.

        Upserts based on cache_key: inserts if new, updates if exists.

        Args:
            db: Database session
            cache_key: Cache key
            ttl: Time-to-live in seconds
            text: Original source text
            source_lang: Source language code
            target_lang: Target language code
            translated_text: Translated text
            source: Translation source (MACHINE/AI_ENHANCED/CACHE/N/A)
            confidence: Confidence score (0.0-1.0)
            metadata: Optional metadata dict

        Returns:
            True if successful
        """
        try:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else None

            # Upsert: check for existing record first
            stmt = select(TranslationCache).where(
                TranslationCache.cache_key == cache_key
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record
                existing.text = text
                existing.source_lang = source_lang
                existing.target_lang = target_lang
                existing.translated_text = translated_text
                existing.source = source
                existing.confidence = confidence
                existing.metadata_json = metadata_str
                existing.ttl_expires_at = expires_at
            else:
                # Insert new record
                record = TranslationCache(
                    cache_key=cache_key,
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    translated_text=translated_text,
                    source=source,
                    confidence=confidence,
                    metadata_json=metadata_str,
                    ttl_expires_at=expires_at,
                )
                db.add(record)

            await db.commit()
            logger.debug(f"SQLite cache set: {cache_key} (TTL={ttl}s)")

            # Probabilistically purge expired entries (≈1% chance)
            await self._probabilistic_purge(db)

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"SQLite cache set error: {e}")
            return False

    async def delete(self, db: AsyncSession, cache_key: str) -> bool:
        """Delete cache entry.

        Args:
            db: Database session
            cache_key: Cache key

        Returns:
            True if successful
        """
        try:
            stmt = delete(TranslationCache).where(
                TranslationCache.cache_key == cache_key
            )
            await db.execute(stmt)
            await db.commit()
            logger.debug(f"SQLite cache deleted: {cache_key}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"SQLite cache delete error: {e}")
            return False

    async def _probabilistic_purge(self, db: AsyncSession, probability: float = 0.01) -> None:
        """Probabilistically purge expired cache entries.

        Called on each set() with a 1% default probability.
        This avoids a dedicated background cleanup task.
        """
        if random.random() > probability:
            return
        try:
            stmt = delete(TranslationCache).where(
                TranslationCache.ttl_expires_at <= datetime.now()
            )
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount:
                logger.debug(f"Probabilistic purge: removed {result.rowcount} expired entries")
        except Exception as e:
            await db.rollback()
            logger.warning(f"Probabilistic purge failed: {e}")

    async def is_available(self, db: AsyncSession) -> bool:
        """Check if SQLite/database is available.

        Performs a lightweight query to verify the database connection
        and the translation_cache table are accessible.

        Args:
            db: Database session

        Returns:
            True if database is available
        """
        try:
            stmt = select(func.count()).select_from(TranslationCache)
            await db.execute(stmt)
            return True
        except Exception:
            return False

    @classmethod
    async def stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """Get cache statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dict with 'total_cached', 'backend', 'oldest_entry'
        """
        try:
            active_stmt = select(func.count()).select_from(TranslationCache).where(
                TranslationCache.ttl_expires_at > datetime.now()
            )
            active_result = await db.execute(active_stmt)
            total_cached = active_result.scalar() or 0
            
            oldest_stmt = select(func.min(TranslationCache.created_at))
            oldest_result = await db.execute(oldest_stmt)
            oldest_entry = oldest_result.scalar()
            
            stats = {
                "total_cached": total_cached,
                "backend": "sqlite",
                "oldest_entry": oldest_entry,
            }
            logger.debug(f"Cache stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"total_cached": 0, "backend": "sqlite", "oldest_entry": None}

    @classmethod
    async def clear_all(cls, db: AsyncSession) -> bool:
        """Clear all cache entries.
        
        Args:
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            stmt = delete(TranslationCache)
            await db.execute(stmt)
            await db.commit()
            logger.info("All cache entries cleared")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Clear all error: {e}")
            return False