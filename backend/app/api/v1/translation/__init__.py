"""
Translation API module.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from loguru import logger

from app.schemas.response import ApiResponse
from app.schemas.translation import (
    BatchTranslateRequest,
    BatchTranslationResult,
    TranslateRequest,
    TranslationHistoryResponse,
    TranslationResult,
)
from app.services.translation import get_orchestrator
from app.services.translation.orchestrator import TranslationOrchestrator

from app.api.v1.translation import rules, references, glossary

router = APIRouter()

# Include sub-routers
router.include_router(rules.router, prefix="/rules", tags=["translation-rules"])
router.include_router(references.router, prefix="/references", tags=["translation-references"])
router.include_router(glossary.router, prefix="/glossary", tags=["glossary"])


def get_translation_orchestrator() -> TranslationOrchestrator:
    """Dependency to get translation orchestrator."""
    return get_orchestrator()


@router.post(
    "/translate",
    response_model=ApiResponse[TranslationResult],
    status_code=status.HTTP_200_OK,
    summary="Translate single text",
    description="Translate a single text from source language to target language with optional AI enhancement.",
    responses={
        200: {"description": "Translation successful"},
        400: {"description": "Invalid request"},
        500: {"description": "Translation service error"},
    },
)
async def translate_text(
    request: TranslateRequest,
    orchestrator: TranslationOrchestrator = Depends(get_translation_orchestrator),
) -> ApiResponse[TranslationResult]:
    """
    Translate a single text.

    - **text**: Text to translate (1-5000 characters)
    - **source_lang**: Source language code (default: zh)
    - **target_lang**: Target language code (default: en)
    - **use_cache**: Whether to use cached results (default: true)
    - **use_ai_enhance**: Whether to apply AI enhancement (default: true)
    - **context**: Additional context for translation (optional)
    """
    logger.info(
        f"Translation request received",
        extra={
            "text_length": len(request.text),
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "use_cache": request.use_cache,
            "use_ai_enhance": request.use_ai_enhance,
        },
    )

    result = await orchestrator.translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        use_cache=request.use_cache,
        use_ai_enhance=request.use_ai_enhance,
        context=request.context,
    )

    return ApiResponse(
        code=200,
        message="Translation successful",
        data=result,
    )


@router.post(
    "/batch",
    response_model=ApiResponse[BatchTranslationResult],
    status_code=status.HTTP_200_OK,
    summary="Batch translate texts",
    description="Translate multiple texts in a single request with optimized batch processing.",
    responses={
        200: {"description": "Batch translation successful"},
        400: {"description": "Invalid request"},
        500: {"description": "Translation service error"},
    },
)
async def batch_translate(
    request: BatchTranslateRequest,
    orchestrator: TranslationOrchestrator = Depends(get_translation_orchestrator),
) -> ApiResponse[BatchTranslationResult]:
    """
    Batch translate multiple texts.

    - **texts**: List of texts to translate (1-100 texts, each 1-5000 characters)
    - **source_lang**: Source language code (default: zh)
    - **target_lang**: Target language code (default: en)
    - **use_cache**: Whether to use cached results (default: true)
    - **use_ai_enhance**: Whether to apply AI enhancement (default: true)
    """
    logger.info(
        f"Batch translation request received",
        extra={
            "text_count": len(request.texts),
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
        },
    )

    result = await orchestrator.batch_translate(
        texts=request.texts,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        use_cache=request.use_cache,
        use_ai_enhance=request.use_ai_enhance,
    )

    return ApiResponse(
        code=200,
        message=f"Translated {result.total} texts, {result.cached_count} from cache",
        data=result,
    )


@router.get(
    "/history",
    response_model=ApiResponse[TranslationHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get translation history",
    description="Retrieve paginated translation history records.",
)
async def get_translation_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(default=None, description="Filter by source language"),
    target_lang: Optional[str] = Query(default=None, description="Filter by target language"),
) -> ApiResponse[TranslationHistoryResponse]:
    """
    Get translation history with pagination.

    Note: This endpoint is a placeholder. The actual implementation
    will require database models for translation history,
    which will be implemented in Phase 3.
    """
    # Placeholder implementation
    # TODO: Implement with database query when translation history model is ready

    history_response = TranslationHistoryResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )

    return ApiResponse(
        code=200,
        message="Translation history retrieved",
        data=history_response,
    )


@router.get(
    "/health",
    summary="Check translation services health",
    description="Check the health status of all translation-related services.",
)
async def check_translation_health(
    orchestrator: TranslationOrchestrator = Depends(get_translation_orchestrator),
) -> ApiResponse[dict]:
    """
    Check health of translation services.

    Returns the status of:
    - Tencent Cloud Translation API
    - DeepSeek AI Service
    - Redis Cache
    """
    status = await orchestrator.health_check()

    return ApiResponse(
        code=200,
        message="Health check completed",
        data=status,
    )


@router.delete(
    "/cache",
    summary="Clear translation cache",
    description="Clear all cached translations.",
    responses={
        200: {"description": "Cache cleared successfully"},
        500: {"description": "Failed to clear cache"},
    },
)
async def clear_translation_cache(
    orchestrator: TranslationOrchestrator = Depends(get_translation_orchestrator),
) -> ApiResponse[dict]:
    """
    Clear all translation cache.

    This endpoint should be used with caution and typically
    only by administrators.
    """
    from app.services.translation import get_cache_service

    cache_service = get_cache_service()
    deleted_count = await cache_service.clear_all()

    return ApiResponse(
        code=200,
        message=f"Cleared {deleted_count} cached translations",
        data={"deleted_count": deleted_count},
    )


@router.get(
    "/cache/stats",
    summary="Get translation cache statistics",
    description="Get statistics about the translation cache.",
)
async def get_cache_stats() -> ApiResponse[dict]:
    """
    Get translation cache statistics.

    Returns:
    - total_cached: Number of cached translations
    - ttl_seconds: Cache TTL
    """
    from app.services.translation import get_cache_service

    cache_service = get_cache_service()
    stats = await cache_service.get_stats()

    return ApiResponse(
        code=200,
        message="Cache statistics retrieved",
        data=stats,
    )
