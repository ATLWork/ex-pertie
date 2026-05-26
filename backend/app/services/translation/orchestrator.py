"""
Translation Workflow Orchestrator.

Implements T032: Translation Workflow Orchestrator

The orchestrator coordinates the complete translation workflow:
1. Check cache for existing translation
2. Query terminology database for replacements
3. Query reference library for similar translations
4. Call Tencent Cloud machine translation
5. Apply AI enhancement (optional)
6. Cache the result
7. Return the final translation
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.core.database import get_db
from app.schemas.translation import (
    BatchTranslationResult,
    TranslationResult,
    TranslationSource,
)
from app.services.translation.ai_client import DeepSeekClient, get_deepseek_client
from app.services.translation.cache_service import TranslationCacheService, get_cache_service
from app.services.translation.tencent_client import (
    TencentTranslateClient,
    get_tencent_client,
)


class TranslationOrchestrator:
    """
    Orchestrates the complete translation workflow.

    This is the main entry point for translation operations,
    coordinating between cache, machine translation, and AI enhancement.
    """

    def __init__(
        self,
        tencent_client: Optional[TencentTranslateClient] = None,
        ai_client: Optional[DeepSeekClient] = None,
        cache_service: Optional[TranslationCacheService] = None,
    ):
        """
        Initialize orchestrator with dependencies.

        Args:
            tencent_client: Tencent translation client
            ai_client: DeepSeek AI client
            cache_service: Translation cache service
        """
        self.tencent_client = tencent_client or get_tencent_client()
        self.ai_client = ai_client or get_deepseek_client()
        self.cache_service = cache_service or get_cache_service()
        self._glossary_service = None
        self._booking_reference_service = None

    @property
    def glossary_service(self):
        """Lazy load glossary service."""
        if self._glossary_service is None:
            from app.services.glossary import glossary
            self._glossary_service = glossary
        return self._glossary_service

    @property
    def booking_reference_service(self):
        """Lazy load booking reference service."""
        if self._booking_reference_service is None:
            from app.services.booking_reference_service import booking_reference
            self._booking_reference_service = booking_reference
        return self._booking_reference_service

    async def _apply_terminology_replacements(
        self,
        text: str,
        db,  # AsyncSession passed directly
        source_lang: str,
        target_lang: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Apply terminology replacements from glossary.

        Args:
            text: Text to process
            db: Database session
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Tuple of (processed_text, list of replacements applied)
        """
        # Get all active terms for this language pair
        terms = await self.glossary_service.get_active_terms(
            db, source_lang=source_lang, target_lang=target_lang
        )

        if not terms:
            return text, []

        replacements = []
        processed = text

        # Sort by term length descending to handle longer terms first
        # This prevents partial replacements (e.g., "高级大床房" before "大床")
        sorted_terms = sorted(terms, key=lambda t: len(t.term), reverse=True)

        for term in sorted_terms:
            if term.term in processed:
                replacement = term.translation
                processed = processed.replace(term.term, replacement)
                replacements.append({
                    "term": term.term,
                    "translation": replacement,
                    "category": term.category.value if term.category else None,
                })
                logger.debug(
                    f"Terminology replacement applied",
                    extra={"term": term.term, "translation": replacement},
                )

        return processed, replacements

    async def _query_reference_library(
        self,
        text: str,
        db,  # AsyncSession passed directly
        source_lang: str,
        target_lang: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query reference library for similar translations.

        Args:
            text: Text to look up
            db: Database session
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Reference data with ctrip_translation and booking_translation if found
        """
        # First try exact match
        ref = await self.booking_reference_service.find_by_source_text(
            db,
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        if ref:
            await self.booking_reference_service.increment_usage(db, id=ref.id)
            return {
                "source": "exact_match",
                "ctrip_translation": ref.ctrip_translation,
                "booking_translation": ref.booking_translation,
                "hotel_name": ref.hotel_name,
            }

        # Try similar matches
        similar_refs = await self.booking_reference_service.find_similar(
            db,
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            limit=3,
        )

        if similar_refs:
            # Return the most relevant similar reference
            best_ref = similar_refs[0]
            await self.booking_reference_service.increment_usage(db, id=best_ref.id)
            return {
                "source": "similar_match",
                "ctrip_translation": best_ref.ctrip_translation,
                "booking_translation": best_ref.booking_translation,
                "hotel_name": best_ref.hotel_name,
                "similarity_text": best_ref.source_text,
            }

        return None

    async def translate(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        use_cache: bool = True,
        use_ai_enhance: bool = True,
        context: Optional[str] = None,
        db=None,  # Optional AsyncSession for terminology/reference lookup
    ) -> TranslationResult:
        """
        Translate a single text through the complete workflow.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            use_cache: Whether to use cache
            use_ai_enhance: Whether to use AI enhancement
            context: Additional context for translation

        Returns:
            TranslationResult with final translation
        """
        start_time = time.time()
        original_text = text.strip()

        if not original_text:
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                source=TranslationSource.MACHINE,
                cached=False,
            )

        # Step 1: Check cache
        cached_result = None
        if use_cache:
            cached_result = await self.cache_service.get(
                text=original_text,
                source_lang=source_lang,
                target_lang=target_lang,
                use_ai_enhance=use_ai_enhance,
            )

        if cached_result:
            logger.debug(
                f"Translation cache hit",
                extra={"text_length": len(original_text), "source_lang": source_lang},
            )
            return TranslationResult(
                original_text=text,
                translated_text=cached_result["translated_text"],
                source_lang=source_lang,
                target_lang=target_lang,
                source=TranslationSource.CACHE,
                confidence=cached_result.get("confidence"),
                cached=True,
            )

        # Step 2: Query terminology database for replacements
        processed_text = original_text
        terminology_matches = []
        if db:
            try:
                processed_text, terminology_matches = await self._apply_terminology_replacements(
                    original_text, db, source_lang, target_lang
                )
                if terminology_matches:
                    logger.debug(
                        f"Applied {len(terminology_matches)} terminology replacements",
                        extra={"matches": [m["term"] for m in terminology_matches]},
                    )
            except Exception as e:
                logger.warning(f"Terminology lookup failed: {e}")

        # Step 3: Query reference library for similar translations
        reference_data = None
        if db:
            try:
                reference_data = await self._query_reference_library(
                    original_text, db, source_lang, target_lang
                )
                if reference_data:
                    logger.debug(
                        f"Found reference data",
                        extra={"source": reference_data.get("source"), "hotel": reference_data.get("hotel_name")},
                    )
            except Exception as e:
                logger.warning(f"Reference library lookup failed: {e}")

        # Step 4: Call machine translation
        try:
            mt_result = await self.tencent_client.translate(
                text=processed_text,
                source_lang=source_lang,
                target_lang=target_lang,
            )
            translated_text = mt_result.get("translated_text", "")
            source = TranslationSource.MACHINE

        except Exception as e:
            logger.error(f"Machine translation failed: {e}")
            # Return empty result on failure
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                source=TranslationSource.MACHINE,
                cached=False,
            )

        # Step 5: Apply AI enhancement (optional)
        if use_ai_enhance and translated_text:
            try:
                # Build context from reference data for AI enhancement
                enhancement_context = context or ""
                if reference_data:
                    ref_parts = []
                    if reference_data.get("ctrip_translation"):
                        ref_parts.append(f"Ctrip参考: {reference_data['ctrip_translation']}")
                    if reference_data.get("booking_translation"):
                        ref_parts.append(f"Booking参考: {reference_data['booking_translation']}")
                    if ref_parts:
                        enhancement_context = f"{enhancement_context}\n\n参考翻译:\n" + "\n".join(ref_parts)

                ai_result = await self.ai_client.enhance_translation(
                    original_text=original_text,
                    machine_translation=translated_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    context=enhancement_context,
                )
                enhanced_text = ai_result.get("enhanced_text", translated_text)
                if enhanced_text and enhanced_text != translated_text:
                    translated_text = enhanced_text
                    source = TranslationSource.AI_ENHANCED
                    logger.debug(
                        f"AI enhancement applied",
                        extra={
                            "changes": ai_result.get("changes", ""),
                            "text_length": len(translated_text),
                        },
                    )

            except Exception as e:
                logger.warning(f"AI enhancement failed, using MT result: {e}")
                # Continue with MT result

        # Step 6: Cache the result
        if use_cache and translated_text:
            await self.cache_service.set(
                text=original_text,
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                source=source,
                use_ai_enhance=use_ai_enhance,
                metadata={"processing_time_ms": (time.time() - start_time) * 1000},
            )

        elapsed_time = time.time() - start_time
        logger.info(
            f"Translation completed",
            extra={
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source": source.value,
                "original_length": len(original_text),
                "translated_length": len(translated_text),
                "elapsed_ms": elapsed_time * 1000,
            },
        )

        return TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            source=source,
            cached=False,
            booking_reference=reference_data.get("booking_translation") if reference_data else None,
            ctrip_reference=reference_data.get("ctrip_translation") if reference_data else None,
        )

    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str = "zh",
        target_lang: str = "en",
        use_cache: bool = True,
        use_ai_enhance: bool = True,
    ) -> BatchTranslationResult:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            use_cache: Whether to use cache
            use_ai_enhance: Whether to use AI enhancement

        Returns:
            BatchTranslationResult with all translations
        """
        start_time = time.time()
        results: List[TranslationResult] = []
        cached_count = 0
        failed_count = 0

        # Separate cached and uncached texts
        cached_texts = set()
        if use_cache:
            cache_results = await self.cache_service.get_batch(
                texts=texts,
                source_lang=source_lang,
                target_lang=target_lang,
                use_ai_enhance=use_ai_enhance,
            )

            for text, cached in cache_results.items():
                if cached:
                    results.append(
                        TranslationResult(
                            original_text=text,
                            translated_text=cached["translated_text"],
                            source_lang=source_lang,
                            target_lang=target_lang,
                            source=TranslationSource.CACHE,
                            confidence=cached.get("confidence"),
                            cached=True,
                        )
                    )
                    cached_texts.add(text)
                    cached_count += 1

        # Translate uncached texts
        uncached_texts = [t for t in texts if t not in cached_texts]

        if uncached_texts:
            # Process machine translations
            mt_results = await self.tencent_client.batch_translate(
                texts=uncached_texts,
                source_lang=source_lang,
                target_lang=target_lang,
            )

            # Prepare items for potential AI enhancement and caching
            items_to_cache = []

            for i, text in enumerate(uncached_texts):
                mt_result = mt_results[i] if i < len(mt_results) else {}
                translated_text = mt_result.get("translated_text", "")
                source = TranslationSource.MACHINE

                if mt_result.get("error"):
                    failed_count += 1

                results.append(
                    TranslationResult(
                        original_text=text,
                        translated_text=translated_text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        source=source,
                        cached=False,
                    )
                )

                items_to_cache.append({
                    "text": text,
                    "translated_text": translated_text,
                    "source": source,
                })

            # Cache all uncached translations
            if use_cache and items_to_cache:
                await self.cache_service.set_batch(
                    items=items_to_cache,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    use_ai_enhance=use_ai_enhance,
                )

        elapsed_time = time.time() - start_time
        logger.info(
            f"Batch translation completed",
            extra={
                "total": len(texts),
                "cached": cached_count,
                "failed": failed_count,
                "elapsed_ms": elapsed_time * 1000,
            },
        )

        return BatchTranslationResult(
            results=results,
            total=len(texts),
            cached_count=cached_count,
            failed_count=failed_count,
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of translation services.

        Returns:
            Health status dictionary
        """
        status = {
            "orchestrator": "healthy",
            "tencent": "unknown",
            "ai": "unknown",
            "cache": "unknown",
        }

        # Check Tencent translation
        try:
            if self.tencent_client.secret_id and self.tencent_client.secret_key:
                # Try a simple translation
                result = await self.tencent_client.translate(
                    text="test",
                    source_lang="zh",
                    target_lang="en",
                )
                status["tencent"] = "healthy" if result.get("translated_text") else "degraded"
            else:
                status["tencent"] = "not_configured"
        except Exception as e:
            status["tencent"] = f"error: {str(e)[:50]}"

        # Check AI service
        try:
            if self.ai_client.api_key:
                status["ai"] = "configured"
            else:
                status["ai"] = "not_configured"
        except Exception as e:
            status["ai"] = f"error: {str(e)[:50]}"

        # Check cache
        try:
            cache_stats = await self.cache_service.get_stats()
            status["cache"] = "healthy" if cache_stats.get("total_cached", 0) >= 0 else "degraded"
        except Exception as e:
            status["cache"] = f"error: {str(e)[:50]}"

        return status


# Singleton instance
_orchestrator: Optional[TranslationOrchestrator] = None


def get_orchestrator() -> TranslationOrchestrator:
    """
    Get or create orchestrator instance.

    Returns:
        TranslationOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TranslationOrchestrator()
    return _orchestrator
