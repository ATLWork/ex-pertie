"""
Export API endpoints.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.middleware.exception import BadRequestError, NotFoundError
from app.models.user import User
from app.schemas.export import (
    ExportDetailResponse,
    ExportFormat,
    ExportHistoryResponse,
    ExportInitiateResponse,
    ExportListQuery,
    ExportStatus,
    ExportType,
    HotelExportRequest,
    RoomExportRequest,
)
from app.schemas.response import ApiResponse, PagedData, PagedResponse
from app.services.export_service import get_export_service

router = APIRouter()


@router.post("/hotels", response_model=ApiResponse[ExportInitiateResponse], status_code=201)
async def export_hotels(
    request: Request,
    export_request: HotelExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export hotel data.

    - **export_format**: Export file format (excel/csv/json)
    - **hotel_ids**: Optional list of hotel IDs to export (exports all if empty)
    - **use_template**: Whether to use Expedia template format
    """
    export_service = get_export_service()

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Create export record
    export_record = await export_service.create_export_record(
        db,
        export_type=ExportType.HOTEL,
        export_format=export_request.export_format,
        hotel_ids=export_request.hotel_ids,
        use_template=export_request.use_template,
        template_id=export_request.template_id,
        operator_id=current_user.id,
        operator_name=current_user.username if hasattr(current_user, 'username') else None,
        operator_ip=client_ip,
    )

    return ApiResponse(
        code=201,
        message="Export task created successfully",
        data=ExportInitiateResponse(
            export_id=export_record.id,
            status=export_record.status,
            message="Export task is being processed",
        ),
    )


@router.post("/rooms", response_model=ApiResponse[ExportInitiateResponse], status_code=201)
async def export_rooms(
    request: Request,
    export_request: RoomExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export room data.

    - **export_format**: Export file format (excel/csv/json)
    - **hotel_ids**: Optional list of hotel IDs to filter rooms
    - **room_ids**: Optional list of room IDs to export
    - **use_template**: Whether to use Expedia template format
    """
    export_service = get_export_service()

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Create export record
    export_record = await export_service.create_export_record(
        db,
        export_type=ExportType.ROOM,
        export_format=export_request.export_format,
        hotel_ids=export_request.hotel_ids,
        use_template=export_request.use_template,
        template_id=export_request.template_id,
        operator_id=current_user.id,
        operator_name=current_user.username if hasattr(current_user, 'username') else None,
        operator_ip=client_ip,
    )

    return ApiResponse(
        code=201,
        message="Export task created successfully",
        data=ExportInitiateResponse(
            export_id=export_record.id,
            status=export_record.status,
            message="Export task is being processed",
        ),
    )


@router.get("/{export_id}", response_model=ApiResponse[ExportDetailResponse])
async def get_export_detail(
    export_id: str = Path(..., description="Export task ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get export task details.

    - **export_id**: Export task ID
    """
    export_service = get_export_service()
    export_record = await export_service.get_export_record(db, export_id=export_id)

    if not export_record:
        raise NotFoundError(
            message="Export task not found",
            details={"export_id": export_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=ExportDetailResponse(
            export_id=export_record.id,
            file_name=export_record.file_name,
            file_size=export_record.file_size,
            status=export_record.status,
            download_url=export_record.download_url,
            expires_at=export_record.expires_at,
            total_rows=export_record.total_rows,
            total_hotels=export_record.total_hotels,
            total_rooms=export_record.total_rooms,
            processing_time=export_record.processing_time,
            error_message=export_record.error_message,
        ),
    )


@router.get("", response_model=PagedResponse[ExportHistoryResponse])
async def list_exports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    export_type: Optional[ExportType] = Query(None, description="Filter by export type"),
    export_format: Optional[ExportFormat] = Query(None, description="Filter by format"),
    status: Optional[ExportStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List export history.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **export_type**: Filter by export type (hotel/room)
    - **export_format**: Filter by format (excel/csv/json)
    - **status**: Filter by status (pending/processing/completed/failed)
    """
    export_service = get_export_service()

    exports, total = await export_service.list_exports(
        db,
        page=page,
        page_size=page_size,
        export_type=export_type,
        export_format=export_format,
        status=status,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PagedResponse(
        code=200,
        message="success",
        data=PagedData(
            list=[ExportHistoryResponse.model_validate(e) for e in exports],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str = Path(..., description="Export task ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download export file.

    - **export_id**: Export task ID
    """
    export_service = get_export_service()
    export_record = await export_service.get_export_record(db, export_id=export_id)

    if not export_record:
        raise NotFoundError(
            message="Export task not found",
            details={"export_id": export_id},
        )

    if export_record.status != ExportStatus.COMPLETED:
        raise BadRequestError(
            message="Export is not ready for download",
            details={
                "export_id": export_id,
                "status": export_record.status.value,
            },
        )

    if export_record.expires_at and export_record.expires_at < export_record.started_at:
        raise BadRequestError(
            message="Export file has expired",
            details={"export_id": export_id},
        )

    if not export_record.file_path or not os.path.exists(export_record.file_path):
        raise NotFoundError(
            message="Export file not found",
            details={"export_id": export_id},
        )

    # Increment download count
    await export_service.increment_download_count(db, export_id=export_id)

    # Determine media type
    if export_record.export_format == ExportFormat.EXCEL:
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        extension = ".xlsx"
    elif export_record.export_format == ExportFormat.CSV:
        media_type = "text/csv"
        extension = ".csv"
    else:
        media_type = "application/json"
        extension = ".json"

    file_name = f"{export_record.file_name}{extension}"

    return FileResponse(
        path=export_record.file_path,
        media_type=media_type,
        filename=file_name,
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
