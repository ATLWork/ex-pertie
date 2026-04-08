"""
Translation Reference API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.translation import ReferenceSource
from app.schemas.response import ApiResponse, PagedResponse, paged_response
from app.schemas.translation import (
    TranslationReferenceCreate,
    TranslationReferenceResponse,
    TranslationReferenceUpdate,
    TranslationReferenceQuery,
    TranslationReferenceBulkCreate,
)
from app.services.translation_reference import translation_reference
from app.middleware.exception import NotFoundError, BadRequestError

router = APIRouter()


@router.get("", response_model=PagedResponse[TranslationReferenceResponse])
async def list_translation_references(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    source: Optional[ReferenceSource] = Query(None, description="Filter by source"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    db: AsyncSession = Depends(get_db),
):
    """
    List translation references with pagination and filtering.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **source**: Filter by reference source
    - **min_confidence**: Minimum confidence score filter
    """
    query_params = TranslationReferenceQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        source=source,
        min_confidence=min_confidence,
    )

    skip = (page - 1) * page_size
    items = await translation_reference.search(
        db, query_params=query_params, skip=skip, limit=page_size
    )
    total = await translation_reference.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[TranslationReferenceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[TranslationReferenceResponse])
async def create_translation_reference(
    ref_in: TranslationReferenceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new translation reference.

    - **source_text**: Original text
    - **translated_text**: Translated text
    - **source_lang**: Source language code (e.g., zh-CN)
    - **target_lang**: Target language code (e.g., en-US)
    - **context**: Optional context information
    - **confidence**: Confidence score (0-1, default 1.0)
    - **source**: Reference source (manual, imported, ai)
    """
    ref = await translation_reference.create(db, obj_in=ref_in)
    return ApiResponse(
        code=201,
        message="Translation reference created successfully",
        data=TranslationReferenceResponse.model_validate(ref),
    )


@router.post("/bulk", response_model=ApiResponse[list[TranslationReferenceResponse]])
async def bulk_create_translation_references(
    bulk_in: TranslationReferenceBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk create translation references.

    Creates multiple translation reference entries in a single request.
    Useful for importing reference data from external sources.
    """
    if not bulk_in.items:
        raise BadRequestError(message="No items provided for bulk creation")

    refs = await translation_reference.bulk_create(db, obj_in=bulk_in)
    return ApiResponse(
        code=201,
        message=f"Successfully created {len(refs)} translation references",
        data=[TranslationReferenceResponse.model_validate(ref) for ref in refs],
    )


@router.get("/match", response_model=ApiResponse[TranslationReferenceResponse])
async def find_matching_reference(
    source_text: str = Query(..., description="Source text to match"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    min_confidence: float = Query(0.8, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find the best matching reference for a source text.

    This endpoint is used during translation to find existing
    high-quality translations from the reference library.
    """
    ref = await translation_reference.find_match(
        db,
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        min_confidence=min_confidence,
    )

    if not ref:
        return ApiResponse(
            code=200,
            message="No matching reference found",
            data=None,
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TranslationReferenceResponse.model_validate(ref),
    )


@router.get("/similar", response_model=ApiResponse[list[TranslationReferenceResponse]])
async def find_similar_references(
    source_text: str = Query(..., description="Source text to search"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find similar references (contains search).

    Returns references that contain the search text, useful for
    finding partial matches or related translations.
    """
    refs = await translation_reference.find_similar(
        db,
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        limit=limit,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=[TranslationReferenceResponse.model_validate(ref) for ref in refs],
    )


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_reference_statistics(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for translation references.

    Returns counts by source, average confidence, and total count.
    """
    stats = await translation_reference.get_statistics(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=stats,
    )


@router.get("/{ref_id}", response_model=ApiResponse[TranslationReferenceResponse])
async def get_translation_reference(
    ref_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific translation reference by ID.
    """
    ref = await translation_reference.get(db, id=ref_id)
    if not ref:
        raise NotFoundError(
            message="Translation reference not found",
            details={"id": ref_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TranslationReferenceResponse.model_validate(ref),
    )


@router.put("/{ref_id}", response_model=ApiResponse[TranslationReferenceResponse])
async def update_translation_reference(
    ref_id: int,
    ref_in: TranslationReferenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a translation reference.

    Only provided fields will be updated.
    """
    ref = await translation_reference.get(db, id=ref_id)
    if not ref:
        raise NotFoundError(
            message="Translation reference not found",
            details={"id": ref_id},
        )

    updated_ref = await translation_reference.update(db, db_obj=ref, obj_in=ref_in)
    return ApiResponse(
        code=200,
        message="Translation reference updated successfully",
        data=TranslationReferenceResponse.model_validate(updated_ref),
    )


@router.delete("/{ref_id}", response_model=ApiResponse[dict])
async def delete_translation_reference(
    ref_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a translation reference.
    """
    deleted = await translation_reference.delete(db, id=ref_id)
    if not deleted:
        raise NotFoundError(
            message="Translation reference not found",
            details={"id": ref_id},
        )

    return ApiResponse(
        code=200,
        message="Translation reference deleted successfully",
        data={"id": ref_id},
    )


@router.patch("/{ref_id}/confidence", response_model=ApiResponse[TranslationReferenceResponse])
async def update_reference_confidence(
    ref_id: int,
    confidence: float = Query(..., ge=0.0, le=1.0, description="New confidence score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Update confidence score for a reference.

    This endpoint is useful for adjusting confidence based on
    user feedback or quality assessment.
    """
    ref = await translation_reference.update_confidence(db, id=ref_id, confidence=confidence)
    if not ref:
        raise NotFoundError(
            message="Translation reference not found",
            details={"id": ref_id},
        )

    return ApiResponse(
        code=200,
        message="Confidence score updated successfully",
        data=TranslationReferenceResponse.model_validate(ref),
    )
