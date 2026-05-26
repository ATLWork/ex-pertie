"""
Glossary API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.translation import GlossaryCategory, GlossaryReviewStatus
from app.models.user import User
from app.schemas.response import ApiResponse, PagedResponse, PagedData, paged_response
from app.schemas.translation import (
    GlossaryCreate,
    GlossaryResponse,
    GlossaryUpdate,
    GlossaryQuery,
    GlossaryBulkCreate,
)
from app.services.glossary import glossary
from app.middleware.exception import NotFoundError, BadRequestError

router = APIRouter()


# ============== Routes WITHOUT path parameters (must come first) ==============


@router.get("", response_model=PagedResponse[GlossaryResponse])
async def list_glossaries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    category: Optional[GlossaryCategory] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term in term or translation"),
    db: AsyncSession = Depends(get_db),
):
    """
    List glossary entries with pagination and filtering.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **category**: Filter by term category
    - **is_active**: Filter by active status
    - **search**: Search in term or translation
    """
    query_params = GlossaryQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        category=category,
        is_active=is_active,
        search=search,
    )

    skip = (page - 1) * page_size
    items = await glossary.search(db, query_params=query_params, skip=skip, limit=page_size)
    total = await glossary.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[GlossaryResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[GlossaryResponse])
async def create_glossary(
    glossary_in: GlossaryCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new glossary entry.

    - **term**: Term in source language
    - **translation**: Standard translation
    - **source_lang**: Source language code (e.g., zh-CN)
    - **target_lang**: Target language code (e.g., en-US)
    - **category**: Term category (hotel, room, amenity, general)
    - **notes**: Additional notes
    - **is_active**: Whether the term is active
    """
    # Check if term already exists for this language pair
    existing = await glossary.get_by_term(
        db,
        term=glossary_in.term,
        source_lang=glossary_in.source_lang,
        target_lang=glossary_in.target_lang,
    )
    if existing:
        raise BadRequestError(
            message="Glossary entry with this term already exists for this language pair",
            details={
                "term": glossary_in.term,
                "source_lang": glossary_in.source_lang,
                "target_lang": glossary_in.target_lang,
            },
        )

    entry = await glossary.create(db, obj_in=glossary_in)
    return ApiResponse(
        code=201,
        message="Glossary entry created successfully",
        data=GlossaryResponse.model_validate(entry),
    )


@router.post("/bulk", response_model=ApiResponse[list[GlossaryResponse]])
async def bulk_create_glossaries(
    bulk_in: GlossaryBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk create glossary entries.

    Creates multiple glossary entries in a single request.
    Useful for importing terminology from external sources.
    """
    if not bulk_in.items:
        raise BadRequestError(message="No items provided for bulk creation")

    entries = await glossary.bulk_create(db, obj_in=bulk_in)
    return ApiResponse(
        code=201,
        message=f"Successfully created {len(entries)} glossary entries",
        data=[GlossaryResponse.model_validate(entry) for entry in entries],
    )


@router.get("/active", response_model=ApiResponse[list[GlossaryResponse]])
async def get_active_glossaries(
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    category: Optional[GlossaryCategory] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active glossary entries for a language pair.

    This endpoint returns active terms that can be used during
    translation for terminology consistency.
    """
    entries = await glossary.get_active_terms(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
        category=category,
    )
    return ApiResponse(
        code=200,
        message="success",
        data=[GlossaryResponse.model_validate(entry) for entry in entries],
    )


@router.get("/categories", response_model=ApiResponse[dict])
async def get_glossary_categories(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get count of glossary entries by category.

    Returns a breakdown of terms by their category.
    """
    categories = await glossary.get_categories(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=categories,
    )


@router.get("/lookup", response_model=ApiResponse[GlossaryResponse])
async def lookup_glossary_term(
    text: str = Query(..., description="Text to look up"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up a term in the glossary.

    Returns the exact match if found, useful for checking if
    a specific term exists in the glossary.
    """
    entry = await glossary.lookup_term(
        db,
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    if not entry:
        return ApiResponse(
            code=200,
            message="Term not found in glossary",
            data=None,
        )

    return ApiResponse(
        code=200,
        message="success",
        data=GlossaryResponse.model_validate(entry),
    )


@router.get("/lookup-in-text", response_model=ApiResponse[list[GlossaryResponse]])
async def lookup_glossary_in_text(
    text: str = Query(..., description="Text to search in"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find all glossary terms that appear in the given text.

    This endpoint is useful for identifying which glossary terms
    need to be applied during translation.
    """
    entries = await glossary.lookup_in_text(
        db,
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=[GlossaryResponse.model_validate(entry) for entry in entries],
    )


# ============== Glossary Review Endpoints ==============


@router.get(
    "/review/pending",
    response_model=PagedResponse[GlossaryResponse],
    summary="List pending glossary reviews",
    description="Get list of glossary entries pending review.",
)
async def list_pending_glossary_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    category: Optional[GlossaryCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in term or translation"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of glossary entries pending review.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **category**: Filter by term category
    - **search**: Search in term or translation
    """
    skip = (page - 1) * page_size

    items, total = await glossary.get_pending_reviews(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
        category=category,
        search=search,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[GlossaryResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/review/by-status",
    response_model=PagedResponse[GlossaryResponse],
    summary="List glossary by review status",
    description="Get list of glossary entries filtered by review status.",
)
async def list_glossary_by_review_status(
    status: GlossaryReviewStatus = Query(..., description="Review status to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of glossary entries by review status.

    - **status**: Filter by review status (pending/approved/rejected)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    skip = (page - 1) * page_size

    items, total = await glossary.get_by_review_status(
        db,
        status=status,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[GlossaryResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/review/stats",
    response_model=ApiResponse[dict],
    summary="Get glossary review statistics",
    description="Get summary of glossary review statistics.",
)
async def get_glossary_review_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get review statistics for glossary entries.
    """
    stats = await glossary.get_review_stats(db)

    return ApiResponse(
        code=200,
        message="success",
        data=stats,
    )


# ============== Glossary Import/Export Endpoints ==============


@router.post(
    "/import",
    response_model=ApiResponse[dict],
    summary="Import glossary entries",
    description="Import glossary entries from CSV format.",
)
async def import_glossary(
    db: AsyncSession = Depends(get_db),
):
    """
    Import glossary entries from CSV.

    Expects a CSV file with columns:
    - term: Term in source language
    - translation: Standard translation
    - source_lang: Source language code
    - target_lang: Target language code
    - category: Term category (optional)
    - notes: Additional notes (optional)
    """
    # Note: File upload handling would require form data parsing
    # This is a placeholder for the import functionality
    return ApiResponse(
        code=200,
        message="Import functionality available via multipart form upload",
        data={"status": "pending_implementation"},
    )


@router.post(
    "/import/csv",
    response_model=ApiResponse[dict],
    summary="Import glossary from CSV",
    description="Import glossary entries from CSV content.",
)
async def import_glossary_csv(
    payload: dict = Body(..., description="JSON payload with csv_content field"),
    db: AsyncSession = Depends(get_db),
):
    """
    Import glossary entries from CSV string.

    CSV columns (first row must be header):
    - term: Term in source language (required)
    - translation: Standard translation (required)
    - source_lang: Source language code (required)
    - target_lang: Target language code (required)
    - category: Term category (optional, default: general)
    - notes: Additional notes (optional)
    """
    import csv
    import io

    csv_content = payload.get('csv_content', '')
    lines = csv_content.strip().split('\n')
    if len(lines) < 2:
        raise BadRequestError(message="CSV must have at least a header row and one data row")

    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            term = row.get('term', '').strip()
            translation = row.get('translation', '').strip()
            source_lang = row.get('source_lang', 'zh').strip()
            target_lang = row.get('target_lang', 'en').strip()
            category = row.get('category', 'general').strip() or 'general'
            notes = row.get('notes', '').strip() or None

            if not term or not translation:
                errors.append({"row": row_num, "error": "Missing required field (term or translation)"})
                continue

            # Check if term already exists
            existing = await glossary.get_by_term(db, term=term, source_lang=source_lang, target_lang=target_lang)
            if existing:
                errors.append({"row": row_num, "error": f"Term '{term}' already exists for this language pair"})
                continue

            # Create the entry
            entry = await glossary.create(
                db,
                obj_in=GlossaryCreate(
                    term=term,
                    translation=translation,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    category=GlossaryCategory(category) if category else GlossaryCategory.GENERAL,
                    notes=notes,
                    is_active=True,
                )
            )
            imported += 1

        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})

    return ApiResponse(
        code=200 if not errors else 207,
        message=f"Import completed: {imported} imported, {len(errors)} errors",
        data={"imported": imported, "errors": errors},
    )


@router.get(
    "/do-export",
    response_model=ApiResponse[dict],
    summary="Export glossary entries",
    description="Export glossary entries as CSV.",
)
async def export_glossary(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    category: Optional[GlossaryCategory] = Query(None, description="Filter by category"),
    status: Optional[GlossaryReviewStatus] = Query(None, description="Filter by review status"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export glossary entries as CSV.

    Returns CSV content with columns:
    - term, translation, source_lang, target_lang, category, notes, is_active, review_status
    """
    import csv
    import io

    # Build query parameters
    query_params = GlossaryQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        category=category,
    )

    # Get all matching entries (large exports might need pagination)
    items = await glossary.search(db, query_params=query_params, skip=0, limit=10000)

    # Filter by review status if specified
    if status:
        items = [item for item in items if item.review_status == status]

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['term', 'translation', 'source_lang', 'target_lang', 'category', 'notes', 'is_active', 'review_status'])

    for item in items:
        writer.writerow([
            item.term,
            item.translation,
            item.source_lang,
            item.target_lang,
            item.category.value,
            item.notes or '',
            'true' if item.is_active else 'false',
            item.review_status.value,
        ])

    csv_content = output.getvalue()

    return ApiResponse(
        code=200,
        message=f"Exported {len(items)} glossary entries",
        data={
            "count": len(items),
            "csv_content": csv_content,
        },
    )


# ============== Routes WITH path parameters (must come last) ==============


@router.get(
    "/{glossary_id}",
    response_model=ApiResponse[GlossaryResponse],
    summary="Get a glossary entry",
    description="Get a specific glossary entry by ID.",
)
async def get_glossary(
    glossary_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific glossary entry by ID.
    """
    entry = await glossary.get(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=GlossaryResponse.model_validate(entry),
    )


@router.put(
    "/{glossary_id}",
    response_model=ApiResponse[GlossaryResponse],
    summary="Update a glossary entry",
    description="Update a glossary entry by ID.",
)
async def update_glossary(
    glossary_id: int,
    glossary_in: GlossaryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a glossary entry.

    Only provided fields will be updated.
    """
    entry = await glossary.get(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    # Check term uniqueness if term or languages are being updated
    if glossary_in.term or glossary_in.source_lang or glossary_in.target_lang:
        new_term = glossary_in.term or entry.term
        new_source_lang = glossary_in.source_lang or entry.source_lang
        new_target_lang = glossary_in.target_lang or entry.target_lang

        if (
            new_term != entry.term
            or new_source_lang != entry.source_lang
            or new_target_lang != entry.target_lang
        ):
            existing = await glossary.get_by_term(
                db,
                term=new_term,
                source_lang=new_source_lang,
                target_lang=new_target_lang,
            )
            if existing and existing.id != glossary_id:
                raise BadRequestError(
                    message="Glossary entry with this term already exists for this language pair",
                    details={
                        "term": new_term,
                        "source_lang": new_source_lang,
                        "target_lang": new_target_lang,
                    },
                )

    updated_entry = await glossary.update(db, db_obj=entry, obj_in=glossary_in)
    return ApiResponse(
        code=200,
        message="Glossary entry updated successfully",
        data=GlossaryResponse.model_validate(updated_entry),
    )


@router.delete(
    "/{glossary_id}",
    response_model=ApiResponse[dict],
    summary="Delete a glossary entry",
    description="Delete a glossary entry by ID.",
)
async def delete_glossary(
    glossary_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a glossary entry.
    """
    deleted = await glossary.delete(db, id=glossary_id)
    if not deleted:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    return ApiResponse(
        code=200,
        message="Glossary entry deleted successfully",
        data={"id": glossary_id},
    )


@router.post(
    "/{glossary_id}/activate",
    response_model=ApiResponse[GlossaryResponse],
    summary="Activate a glossary entry",
    description="Activate a glossary entry by ID.",
)
async def activate_glossary(
    glossary_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a glossary entry.
    """
    entry = await glossary.activate(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    return ApiResponse(
        code=200,
        message="Glossary entry activated successfully",
        data=GlossaryResponse.model_validate(entry),
    )


@router.post(
    "/{glossary_id}/deactivate",
    response_model=ApiResponse[GlossaryResponse],
    summary="Deactivate a glossary entry",
    description="Deactivate a glossary entry by ID.",
)
async def deactivate_glossary(
    glossary_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a glossary entry.
    """
    entry = await glossary.deactivate(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    return ApiResponse(
        code=200,
        message="Glossary entry deactivated successfully",
        data=GlossaryResponse.model_validate(entry),
    )


@router.post(
    "/{glossary_id}/approve",
    response_model=ApiResponse[GlossaryResponse],
    summary="Approve glossary entry",
    description="Approve a glossary entry for use in translations.",
)
async def approve_glossary(
    glossary_id: int = Path(..., description="Glossary entry ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a glossary entry.

    - **glossary_id**: Glossary entry ID
    """
    entry = await glossary.get(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    entry.review_status = GlossaryReviewStatus.APPROVED
    entry.reviewed_by = current_user.id
    entry.reviewed_at = datetime.utcnow()

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return ApiResponse(
        code=200,
        message="Glossary entry approved successfully",
        data=GlossaryResponse.model_validate(entry),
    )


@router.post(
    "/{glossary_id}/reject",
    response_model=ApiResponse[GlossaryResponse],
    summary="Reject glossary entry",
    description="Reject a glossary entry.",
)
async def reject_glossary(
    glossary_id: int = Path(..., description="Glossary entry ID"),
    review_notes: Optional[str] = Query(None, description="Reason for rejection"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reject a glossary entry.

    - **glossary_id**: Glossary entry ID
    - **review_notes**: Optional reason for rejection
    """
    entry = await glossary.get(db, id=glossary_id)
    if not entry:
        raise NotFoundError(
            message="Glossary entry not found",
            details={"id": glossary_id},
        )

    entry.review_status = GlossaryReviewStatus.REJECTED
    entry.reviewed_by = current_user.id
    entry.reviewed_at = datetime.utcnow()
    if review_notes:
        entry.reviewed_notes = review_notes

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return ApiResponse(
        code=200,
        message="Glossary entry rejected",
        data=GlossaryResponse.model_validate(entry),
    )
