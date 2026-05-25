"""
Booking Reference API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.booking_reference import (
    BookingReferenceCreate,
    BookingReferenceResponse,
    BookingReferenceUpdate,
    BookingReferenceQuery,
    BookingReferenceBulkCreate,
)
from app.schemas.response import ApiResponse, PagedResponse, paged_response
from app.services.booking_reference_service import booking_reference
from app.middleware.exception import NotFoundError, BadRequestError

router = APIRouter()


@router.get("", response_model=PagedResponse[BookingReferenceResponse])
async def list_booking_references(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    hotel_name: Optional[str] = Query(None, description="Filter by hotel name"),
    hotel_address: Optional[str] = Query(None, description="Filter by hotel address"),
    source_text: Optional[str] = Query(None, description="Filter by source text"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List booking references with pagination and filtering.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **hotel_name**: Filter by hotel name (partial match)
    - **hotel_address**: Filter by hotel address (partial match)
    - **source_text**: Filter by source text (partial match)
    - **is_active**: Filter by active status
    """
    query_params = BookingReferenceQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        hotel_name=hotel_name,
        hotel_address=hotel_address,
        source_text=source_text,
        is_active=is_active,
    )

    skip = (page - 1) * page_size
    items = await booking_reference.search(
        db, query_params=query_params, skip=skip, limit=page_size
    )
    total = await booking_reference.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[BookingReferenceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[BookingReferenceResponse])
async def create_booking_reference(
    ref_in: BookingReferenceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking reference.

    - **source_text**: Original text in source language
    - **ctrip_translation**: Translation from Ctrip
    - **booking_translation**: Translation from Booking.com
    - **source_lang**: Source language code (e.g., zh-CN)
    - **target_lang**: Target language code (e.g., en-US)
    - **hotel_name**: Associated hotel name (optional)
    - **hotel_address**: Associated hotel address (optional)
    """
    ref = await booking_reference.create(db, obj_in=ref_in)
    return ApiResponse(
        code=201,
        message="Booking reference created successfully",
        data=BookingReferenceResponse.model_validate(ref),
    )


@router.post("/bulk", response_model=ApiResponse[list[BookingReferenceResponse]])
async def bulk_create_booking_references(
    bulk_in: BookingReferenceBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk create booking references.

    Creates multiple booking reference entries in a single request.
    Useful for importing reference data from external sources.
    """
    if not bulk_in.items:
        raise BadRequestError(message="No items provided for bulk creation")

    refs = await booking_reference.bulk_create(db, obj_in=bulk_in)
    return ApiResponse(
        code=201,
        message=f"Successfully created {len(refs)} booking references",
        data=[BookingReferenceResponse.model_validate(ref) for ref in refs],
    )


@router.post("/upsert", response_model=ApiResponse[list[BookingReferenceResponse]])
async def upsert_booking_references(
    bulk_in: BookingReferenceBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk upsert booking references (insert or update on conflict).

    If a reference with the same source_text, source_lang, and target_lang
    already exists, it will be updated. Otherwise, a new record will be created.
    """
    if not bulk_in.items:
        raise BadRequestError(message="No items provided for upsert")

    refs = await booking_reference.bulk_upsert(db, obj_in=bulk_in)
    return ApiResponse(
        code=201,
        message=f"Successfully upserted {len(refs)} booking references",
        data=[BookingReferenceResponse.model_validate(ref) for ref in refs],
    )


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_booking_reference_statistics(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for booking references.

    Returns total count, counts by source, top hotels, and usage statistics.
    """
    stats = await booking_reference.get_statistics(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=stats,
    )


@router.get("/match", response_model=ApiResponse[BookingReferenceResponse])
async def find_matching_reference(
    source_text: str = Query(..., description="Source text to match"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find the best matching booking reference for a source text.

    This endpoint is used during translation to find existing
    reference translations from the booking reference library.
    """
    ref = await booking_reference.find_by_source_text(
        db,
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
    )

    if not ref:
        return ApiResponse(
            code=200,
            message="No matching reference found",
            data=None,
        )

    # Increment usage count
    ref = await booking_reference.increment_usage(db, id=ref.id)

    return ApiResponse(
        code=200,
        message="success",
        data=BookingReferenceResponse.model_validate(ref),
    )


@router.get("/similar", response_model=ApiResponse[list[BookingReferenceResponse]])
async def find_similar_references(
    source_text: str = Query(..., description="Source text to search"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find similar booking references (contains search).

    Returns references that contain the search text, useful for
    finding partial matches or related translations.
    """
    refs = await booking_reference.find_similar(
        db,
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        limit=limit,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=[BookingReferenceResponse.model_validate(ref) for ref in refs],
    )


@router.get("/hotel/{hotel_name}", response_model=PagedResponse[BookingReferenceResponse])
async def get_references_by_hotel(
    hotel_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: str = Query(..., description="Source language code"),
    target_lang: str = Query(..., description="Target language code"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all booking references for a specific hotel.

    - **hotel_name**: Hotel name to filter by
    - **source_lang**: Source language code
    - **target_lang**: Target language code
    """
    skip = (page - 1) * page_size
    items = await booking_reference.find_by_hotel(
        db,
        hotel_name=hotel_name,
        source_lang=source_lang,
        target_lang=target_lang,
        skip=skip,
        limit=page_size,
    )

    # Get total count for the hotel
    query_params = BookingReferenceQuery(hotel_name=hotel_name, source_lang=source_lang, target_lang=target_lang)
    total = await booking_reference.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[BookingReferenceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ref_id}", response_model=ApiResponse[BookingReferenceResponse])
async def get_booking_reference(
    ref_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific booking reference by ID.
    """
    ref = await booking_reference.get(db, id=ref_id)
    if not ref:
        raise NotFoundError(
            message="Booking reference not found",
            details={"id": ref_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=BookingReferenceResponse.model_validate(ref),
    )


@router.put("/{ref_id}", response_model=ApiResponse[BookingReferenceResponse])
async def update_booking_reference(
    ref_id: int,
    ref_in: BookingReferenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a booking reference.

    Only provided fields will be updated.
    """
    ref = await booking_reference.get(db, id=ref_id)
    if not ref:
        raise NotFoundError(
            message="Booking reference not found",
            details={"id": ref_id},
        )

    updated_ref = await booking_reference.update(db, db_obj=ref, obj_in=ref_in)
    return ApiResponse(
        code=200,
        message="Booking reference updated successfully",
        data=BookingReferenceResponse.model_validate(updated_ref),
    )


@router.delete("/{ref_id}", response_model=ApiResponse[dict])
async def delete_booking_reference(
    ref_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a booking reference.
    """
    deleted = await booking_reference.delete(db, id=ref_id)
    if not deleted:
        raise NotFoundError(
            message="Booking reference not found",
            details={"id": ref_id},
        )

    return ApiResponse(
        code=200,
        message="Booking reference deleted successfully",
        data={"id": ref_id},
    )