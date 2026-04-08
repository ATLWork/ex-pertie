"""
Glossary API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.translation import GlossaryCategory
from app.schemas.response import ApiResponse, PagedResponse, paged_response
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


@router.get("/{glossary_id}", response_model=ApiResponse[GlossaryResponse])
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


@router.put("/{glossary_id}", response_model=ApiResponse[GlossaryResponse])
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


@router.delete("/{glossary_id}", response_model=ApiResponse[dict])
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


@router.post("/{glossary_id}/activate", response_model=ApiResponse[GlossaryResponse])
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


@router.post("/{glossary_id}/deactivate", response_model=ApiResponse[GlossaryResponse])
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
