"""
Translation review API endpoints.

Provides endpoints for reviewing translations with:
- Review status management (pending/approved/rejected)
- Batch review operations
- Comparison view (original / booking reference / translated)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.middleware.exception import BadRequestError, NotFoundError
from app.models.translation import ReviewStatus, TranslationHistory
from app.models.user import User
from app.schemas._translation import TranslationHistoryResponse
from app.schemas.response import ApiResponse, PagedData, PagedResponse
from app.services.translation_history import translation_history

router = APIRouter()


class BatchReviewRequest(BaseModel):
    """Request body for batch review operation."""

    ids: List[int] = Query(..., description="List of translation history IDs to review")
    action: str = Query(..., description="Action: 'approve', 'reject', or 'update'")
    review_notes: Optional[str] = Field(None, description="Review notes for rejection")


class TranslationUpdateRequest(BaseModel):
    """Request body for updating a translation."""

    translated_text: str = Query(..., description="Updated translated text")
    review_notes: Optional[str] = Field(None, description="Optional review notes")


@router.get(
    "/pending",
    response_model=PagedResponse[TranslationHistoryResponse],
    summary="List pending reviews",
    description="Get list of translations pending review.",
)
async def list_pending_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    search: Optional[str] = Query(None, description="Search in source/target text"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of translations pending review.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **search**: Search in source text or translated text
    """
    skip = (page - 1) * page_size

    records, total = await translation_history.get_pending_reviews(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
        search=search,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    items = [TranslationHistoryResponse.model_validate(r) for r in records]

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/by-status",
    response_model=PagedResponse[TranslationHistoryResponse],
    summary="List reviews by status",
    description="Get list of translations filtered by review status.",
)
async def list_reviews_by_status(
    status: ReviewStatus = Query(..., description="Review status to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of translations by review status.

    - **status**: Filter by review status (pending/approved/rejected)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    skip = (page - 1) * page_size

    records, total = await translation_history.get_by_review_status(
        db,
        status=status,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    items = [TranslationHistoryResponse.model_validate(r) for r in records]

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{history_id}",
    response_model=ApiResponse[TranslationHistoryResponse],
    summary="Get translation for review",
    description="Get detailed translation record for review.",
)
async def get_translation_for_review(
    history_id: int = Path(..., description="Translation history ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific translation history record for review.

    - **history_id**: Translation history ID
    """
    record = await translation_history.get(db, history_id)

    if not record:
        raise NotFoundError(
            message="Translation record not found",
            details={"id": history_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TranslationHistoryResponse.model_validate(record),
    )


@router.put(
    "/{history_id}",
    response_model=ApiResponse[TranslationHistoryResponse],
    summary="Update translation",
    description="Update the translated text for a translation record.",
)
async def update_translation(
    history_id: int = Path(..., description="Translation history ID"),
    request: TranslationUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update translated text for a translation record.

    - **history_id**: Translation history ID
    - **translated_text**: New translated text
    - **review_notes**: Optional review notes
    """
    record = await translation_history.get(db, history_id)

    if not record:
        raise NotFoundError(
            message="Translation record not found",
            details={"id": history_id},
        )

    # Update the translated text
    record.translated_text = request.translated_text
    if request.review_notes:
        record.review_notes = request.review_notes

    db.add(record)
    await db.flush()
    await db.refresh(record)

    return ApiResponse(
        code=200,
        message="Translation updated successfully",
        data=TranslationHistoryResponse.model_validate(record),
    )


@router.post(
    "/batch",
    response_model=ApiResponse[dict],
    summary="Batch review",
    description="Batch approve or reject translations.",
)
async def batch_review(
    request: BatchReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch approve or reject translations.

    - **ids**: List of translation history IDs
    - **action**: 'approve', 'reject', or 'update'
    - **review_notes**: Optional notes for rejection
    """
    if not request.ids:
        raise BadRequestError(message="No translation IDs provided")

    if request.action not in ("approve", "reject"):
        raise BadRequestError(
            message="Invalid action. Must be 'approve' or 'reject'",
        )

    updated_count = 0
    errors = []

    for history_id in request.ids:
        record = await translation_history.get(db, history_id)
        if not record:
            errors.append({"id": history_id, "error": "Not found"})
            continue

        if request.action == "approve":
            record.review_status = ReviewStatus.APPROVED
        elif request.action == "reject":
            record.review_status = ReviewStatus.REJECTED

        record.reviewed_by = current_user.id
        record.reviewed_at = datetime.utcnow()
        if request.review_notes:
            record.review_notes = request.review_notes

        db.add(record)
        updated_count += 1

    await db.commit()

    return ApiResponse(
        code=200,
        message=f"Batch {request.action} completed: {updated_count} updated, {len(errors)} failed",
        data={
            "updated": updated_count,
            "errors": errors,
        },
    )


@router.post(
    "/{history_id}/approve",
    response_model=ApiResponse[TranslationHistoryResponse],
    summary="Approve translation",
    description="Approve a specific translation.",
)
async def approve_translation(
    history_id: int = Path(..., description="Translation history ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a specific translation.

    - **history_id**: Translation history ID
    """
    record = await translation_history.get(db, history_id)

    if not record:
        raise NotFoundError(
            message="Translation record not found",
            details={"id": history_id},
        )

    record.review_status = ReviewStatus.APPROVED
    record.reviewed_by = current_user.id
    record.reviewed_at = datetime.utcnow()

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ApiResponse(
        code=200,
        message="Translation approved successfully",
        data=TranslationHistoryResponse.model_validate(record),
    )


@router.post(
    "/{history_id}/reject",
    response_model=ApiResponse[TranslationHistoryResponse],
    summary="Reject translation",
    description="Reject a specific translation.",
)
async def reject_translation(
    history_id: int = Path(..., description="Translation history ID"),
    review_notes: Optional[str] = Query(None, description="Reason for rejection"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reject a specific translation.

    - **history_id**: Translation history ID
    - **review_notes**: Optional reason for rejection
    """
    record = await translation_history.get(db, history_id)

    if not record:
        raise NotFoundError(
            message="Translation record not found",
            details={"id": history_id},
        )

    record.review_status = ReviewStatus.REJECTED
    record.reviewed_by = current_user.id
    record.reviewed_at = datetime.utcnow()
    if review_notes:
        record.review_notes = review_notes

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ApiResponse(
        code=200,
        message="Translation rejected successfully",
        data=TranslationHistoryResponse.model_validate(record),
    )


@router.get(
    "/stats/summary",
    response_model=ApiResponse[dict],
    summary="Get review statistics",
    description="Get summary of translation review statistics.",
)
async def get_review_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get review statistics including counts by status.
    """
    stats = await translation_history.get_review_stats(db)

    return ApiResponse(
        code=200,
        message="success",
        data=stats,
    )