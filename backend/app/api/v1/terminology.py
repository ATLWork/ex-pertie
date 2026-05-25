"""
Terminology API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.terminology import TerminologyCategory
from app.schemas.response import ApiResponse, PagedResponse, paged_response
from app.schemas.translation import (
    TerminologyCreate,
    TerminologyResponse,
    TerminologyUpdate,
    TerminologyQuery,
)
from app.services.terminology_service import terminology
from app.middleware.exception import NotFoundError, BadRequestError

router = APIRouter()


@router.get("", response_model=PagedResponse[TerminologyResponse])
async def list_terminologies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    domain: Optional[TerminologyCategory] = Query(None, description="Filter by domain"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term in name or source_text"),
    db: AsyncSession = Depends(get_db),
):
    """
    List terminology entries with pagination and filtering.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **domain**: Filter by domain category
    - **is_active**: Filter by active status
    - **search**: Search in name or source_text
    """
    query_params = TerminologyQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        domain=domain,
        is_active=is_active,
        search=search,
    )

    skip = (page - 1) * page_size
    items = await terminology.search(db, query_params=query_params, skip=skip, limit=page_size)
    total = await terminology.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[TerminologyResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[TerminologyResponse])
async def create_terminology(
    terminology_in: TerminologyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new terminology entry.

    - **name**: Terminology entry name
    - **source_text**: Original/source text
    - **translated_text**: Translated text
    - **source_lang**: Source language code (e.g., zh-CN)
    - **target_lang**: Target language code (e.g., en-US)
    - **domain**: Domain category (hotel, room, amenity, general)
    - **notes**: Additional notes
    - **is_active**: Whether the term is active
    """
    # Check if terminology entry with same name already exists for this language pair
    existing = await terminology.get_by_name(
        db,
        name=terminology_in.name,
        source_lang=terminology_in.source_lang,
        target_lang=terminology_in.target_lang,
    )
    if existing:
        raise BadRequestError(
            message="Terminology entry with this name already exists for this language pair",
            details={
                "name": terminology_in.name,
                "source_lang": terminology_in.source_lang,
                "target_lang": terminology_in.target_lang,
            },
        )

    entry = await terminology.create(db, obj_in=terminology_in)
    return ApiResponse(
        code=201,
        message="Terminology entry created successfully",
        data=TerminologyResponse.model_validate(entry),
    )


@router.post("/bulk", response_model=ApiResponse[list[TerminologyResponse]])
async def bulk_create_terminologies(
    items: list[TerminologyCreate],
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk create terminology entries.

    Creates multiple terminology entries in a single request.
    Useful for importing terminology from external sources.
    """
    if not items:
        raise BadRequestError(message="No items provided for bulk creation")

    entries = await terminology.bulk_create(db, items=items)
    return ApiResponse(
        code=201,
        message=f"Successfully created {len(entries)} terminology entries",
        data=[TerminologyResponse.model_validate(entry) for entry in entries],
    )


@router.get("/active", response_model=ApiResponse[list[TerminologyResponse]])
async def get_active_terminologies(
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    domain: Optional[TerminologyCategory] = Query(None, description="Filter by domain"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active terminology entries for a language pair.

    This endpoint returns active terms that can be used during
    translation for terminology consistency.
    """
    entries = await terminology.get_active_terms(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
        domain=domain,
    )
    return ApiResponse(
        code=200,
        message="success",
        data=[TerminologyResponse.model_validate(entry) for entry in entries],
    )


@router.get("/domains", response_model=ApiResponse[dict])
async def get_terminology_domains(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get count of terminology entries by domain.

    Returns a breakdown of terms by their domain.
    """
    domains = await terminology.get_domains(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=domains,
    )


@router.get("/lookup", response_model=ApiResponse[TerminologyResponse])
async def lookup_terminology_term(
    text: str = Query(..., description="Text to look up"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up a term in the terminology database.

    Returns the exact match if found, useful for checking if
    a specific term exists.
    """
    entry = await terminology.get_by_source_text(
        db,
        source_text=text,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    if not entry:
        return ApiResponse(
            code=200,
            message="Term not found in terminology",
            data=None,
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TerminologyResponse.model_validate(entry),
    )


@router.get("/lookup-in-text", response_model=ApiResponse[list[TerminologyResponse]])
async def lookup_terminology_in_text(
    text: str = Query(..., description="Text to search in"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find all terminology entries that appear in the given text.

    This endpoint is useful for identifying which terminology
    need to be applied during translation.
    """
    entries = await terminology.lookup_in_text(
        db,
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=[TerminologyResponse.model_validate(entry) for entry in entries],
    )


@router.get("/{terminology_id}", response_model=ApiResponse[TerminologyResponse])
async def get_terminology(
    terminology_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific terminology entry by ID.
    """
    entry = await terminology.get(db, id=terminology_id)
    if not entry:
        raise NotFoundError(
            message="Terminology entry not found",
            details={"id": terminology_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TerminologyResponse.model_validate(entry),
    )


@router.put("/{terminology_id}", response_model=ApiResponse[TerminologyResponse])
async def update_terminology(
    terminology_id: int,
    terminology_in: TerminologyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a terminology entry.

    Only provided fields will be updated.
    """
    entry = await terminology.get(db, id=terminology_id)
    if not entry:
        raise NotFoundError(
            message="Terminology entry not found",
            details={"id": terminology_id},
        )

    # Check name uniqueness if name or languages are being updated
    if terminology_in.name or terminology_in.source_lang or terminology_in.target_lang:
        new_name = terminology_in.name or entry.name
        new_source_lang = terminology_in.source_lang or entry.source_lang
        new_target_lang = terminology_in.target_lang or entry.target_lang

        if (
            new_name != entry.name
            or new_source_lang != entry.source_lang
            or new_target_lang != entry.target_lang
        ):
            existing = await terminology.get_by_name(
                db,
                name=new_name,
                source_lang=new_source_lang,
                target_lang=new_target_lang,
            )
            if existing and existing.id != terminology_id:
                raise BadRequestError(
                    message="Terminology entry with this name already exists for this language pair",
                    details={
                        "name": new_name,
                        "source_lang": new_source_lang,
                        "target_lang": new_target_lang,
                    },
                )

    updated_entry = await terminology.update(db, db_obj=entry, obj_in=terminology_in)
    return ApiResponse(
        code=200,
        message="Terminology entry updated successfully",
        data=TerminologyResponse.model_validate(updated_entry),
    )


@router.delete("/{terminology_id}", response_model=ApiResponse[dict])
async def delete_terminology(
    terminology_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a terminology entry.
    """
    deleted = await terminology.delete(db, id=terminology_id)
    if not deleted:
        raise NotFoundError(
            message="Terminology entry not found",
            details={"id": terminology_id},
        )

    return ApiResponse(
        code=200,
        message="Terminology entry deleted successfully",
        data={"id": terminology_id},
    )


@router.post("/{terminology_id}/activate", response_model=ApiResponse[TerminologyResponse])
async def activate_terminology(
    terminology_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a terminology entry.
    """
    entry = await terminology.activate(db, id=terminology_id)
    if not entry:
        raise NotFoundError(
            message="Terminology entry not found",
            details={"id": terminology_id},
        )

    return ApiResponse(
        code=200,
        message="Terminology entry activated successfully",
        data=TerminologyResponse.model_validate(entry),
    )


@router.post("/{terminology_id}/deactivate", response_model=ApiResponse[TerminologyResponse])
async def deactivate_terminology(
    terminology_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a terminology entry.
    """
    entry = await terminology.deactivate(db, id=terminology_id)
    if not entry:
        raise NotFoundError(
            message="Terminology entry not found",
            details={"id": terminology_id},
        )

    return ApiResponse(
        code=200,
        message="Terminology entry deactivated successfully",
        data=TerminologyResponse.model_validate(entry),
    )