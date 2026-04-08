"""
Export background tasks for ARQ task queue.

These tasks handle long-running export operations asynchronously.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from arq import ctx
from loguru import logger

from app.models.export_history import ExportFormat, ExportStatus, ExportType
from app.models.hotel import Hotel
from app.models.room import Room


async def process_hotel_export(ctx: Dict[str, Any], export_id: str, **kwargs) -> Dict[str, Any]:
    """
    Process hotel data export task.

    This task exports hotel data to the specified format and updates the ExportHistory record.

    Args:
        ctx: ARQ context containing redis and database connections
        export_id: Export history record ID
        **kwargs: Additional parameters
            - hotel_ids: List of hotel IDs to export (optional)
            - filter_criteria: JSON string of filter criteria (optional)
            - export_format: Export format (excel, csv, json, xml)
            - template_id: Template ID to use (optional)
            - operator_id: User ID who initiated the export

    Returns:
        Dict containing export result information
    """
    start_time = time.time()
    logger.info(f"Starting hotel export task: export_id={export_id}")

    # Get database session from context
    db = ctx.get("db")
    if db is None:
        logger.error("Database session not found in ARQ context")
        raise RuntimeError("Database session not available")

    try:
        # Import export_history service
        from app.services.export_history_service import ExportHistoryService

        export_service = ExportHistoryService()

        # Get export history record
        export_record = await export_service.get(db, export_id)
        if not export_record:
            raise ValueError(f"Export history not found: {export_id}")

        # Update status to processing
        await export_service.update_status(db, export_id, ExportStatus.PROCESSING)
        await db.commit()

        # Parse parameters
        hotel_ids = kwargs.get("hotel_ids")
        if isinstance(hotel_ids, str):
            hotel_ids = json.loads(hotel_ids) if hotel_ids else None

        filter_criteria = kwargs.get("filter_criteria")
        if filter_criteria and isinstance(filter_criteria, str):
            filter_criteria = json.loads(filter_criteria)

        export_format = kwargs.get("export_format", ExportFormat.EXCEL)
        if isinstance(export_format, str):
            export_format = ExportFormat(export_format)

        # Query hotels
        from sqlalchemy import select

        query = select(Hotel)
        if hotel_ids:
            query = query.where(Hotel.id.in_(hotel_ids))
        if filter_criteria:
            # Apply filter criteria
            if filter_criteria.get("brand_id"):
                query = query.where(Hotel.brand_id == filter_criteria["brand_id"])
            if filter_criteria.get("status"):
                query = query.where(Hotel.status == filter_criteria["status"])
            if filter_criteria.get("name"):
                query = query.where(Hotel.name.like(f"%{filter_criteria['name']}%"))

        result = await db.execute(query)
        hotels = list(result.scalars().all())

        # Process export based on format
        if export_format == ExportFormat.EXCEL:
            file_path, file_size, row_count = await _export_hotels_to_excel(hotels, export_record.file_name)
        elif export_format == ExportFormat.CSV:
            file_path, file_size, row_count = await _export_hotels_to_csv(hotels, export_record.file_name)
        elif export_format == ExportFormat.JSON:
            file_path, file_size, row_count = await _export_hotels_to_json(hotels, export_record.file_name)
        elif export_format == ExportFormat.XML:
            file_path, file_size, row_count = await _export_hotels_to_xml(hotels, export_record.file_name)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Update export record with results
        await export_service.update_status(
            db,
            export_id,
            ExportStatus.COMPLETED,
            file_path=file_path,
            file_size=file_size,
            total_rows=row_count,
            total_hotels=len(hotels),
            total_rooms=0,
            processing_time=processing_time,
            download_url=f"/api/v1/exports/download/{export_id}",
        )
        await db.commit()

        logger.info(
            f"Hotel export completed: export_id={export_id}, "
            f"hotels={len(hotels)}, rows={row_count}, time={processing_time:.2f}s"
        )

        return {
            "export_id": export_id,
            "status": "completed",
            "hotels_exported": len(hotels),
            "rows_exported": row_count,
            "file_path": file_path,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.exception(f"Hotel export failed: export_id={export_id}, error={str(e)}")

        # Update export record with error
        try:
            from app.services.export_history_service import ExportHistoryService

            export_service = ExportHistoryService()
            await export_service.update_status(
                db,
                export_id,
                ExportStatus.FAILED,
                error_message=str(e),
            )
            await db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update export status: {update_error}")

        raise


async def process_room_export(ctx: Dict[str, Any], export_id: str, **kwargs) -> Dict[str, Any]:
    """
    Process room data export task.

    This task exports room data to the specified format and updates the ExportHistory record.

    Args:
        ctx: ARQ context containing redis and database connections
        export_id: Export history record ID
        **kwargs: Additional parameters
            - hotel_ids: List of hotel IDs whose rooms to export (optional)
            - room_ids: List of specific room IDs to export (optional)
            - filter_criteria: JSON string of filter criteria (optional)
            - export_format: Export format (excel, csv, json, xml)
            - template_id: Template ID to use (optional)
            - operator_id: User ID who initiated the export

    Returns:
        Dict containing export result information
    """
    start_time = time.time()
    logger.info(f"Starting room export task: export_id={export_id}")

    # Get database session from context
    db = ctx.get("db")
    if db is None:
        logger.error("Database session not found in ARQ context")
        raise RuntimeError("Database session not available")

    try:
        from app.services.export_history_service import ExportHistoryService

        export_service = ExportHistoryService()

        # Get export history record
        export_record = await export_service.get(db, export_id)
        if not export_record:
            raise ValueError(f"Export history not found: {export_id}")

        # Update status to processing
        await export_service.update_status(db, export_id, ExportStatus.PROCESSING)
        await db.commit()

        # Parse parameters
        hotel_ids = kwargs.get("hotel_ids")
        if isinstance(hotel_ids, str):
            hotel_ids = json.loads(hotel_ids) if hotel_ids else None

        room_ids = kwargs.get("room_ids")
        if isinstance(room_ids, str):
            room_ids = json.loads(room_ids) if room_ids else None

        filter_criteria = kwargs.get("filter_criteria")
        if filter_criteria and isinstance(filter_criteria, str):
            filter_criteria = json.loads(filter_criteria)

        export_format = kwargs.get("export_format", ExportFormat.EXCEL)
        if isinstance(export_format, str):
            export_format = ExportFormat(export_format)

        # Query rooms with hotel info
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = select(Room).options(selectinload(Room.hotel))
        if room_ids:
            query = query.where(Room.id.in_(room_ids))
        elif hotel_ids:
            query = query.where(Room.hotel_id.in_(hotel_ids))

        if filter_criteria:
            # Apply filter criteria
            if filter_criteria.get("room_type"):
                query = query.where(Room.room_type == filter_criteria["room_type"])
            if filter_criteria.get("status"):
                query = query.where(Room.status == filter_criteria["status"])

        result = await db.execute(query)
        rooms = list(result.scalars().all())

        # Process export based on format
        if export_format == ExportFormat.EXCEL:
            file_path, file_size, row_count = await _export_rooms_to_excel(rooms, export_record.file_name)
        elif export_format == ExportFormat.CSV:
            file_path, file_size, row_count = await _export_rooms_to_csv(rooms, export_record.file_name)
        elif export_format == ExportFormat.JSON:
            file_path, file_size, row_count = await _export_rooms_to_json(rooms, export_record.file_name)
        elif export_format == ExportFormat.XML:
            file_path, file_size, row_count = await _export_rooms_to_xml(rooms, export_record.file_name)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Count unique hotels
        unique_hotel_ids = set(room.hotel_id for room in rooms)

        # Update export record with results
        await export_service.update_status(
            db,
            export_id,
            ExportStatus.COMPLETED,
            file_path=file_path,
            file_size=file_size,
            total_rows=row_count,
            total_hotels=len(unique_hotel_ids),
            total_rooms=len(rooms),
            processing_time=processing_time,
            download_url=f"/api/v1/exports/download/{export_id}",
        )
        await db.commit()

        logger.info(
            f"Room export completed: export_id={export_id}, "
            f"hotels={len(unique_hotel_ids)}, rooms={len(rooms)}, "
            f"rows={row_count}, time={processing_time:.2f}s"
        )

        return {
            "export_id": export_id,
            "status": "completed",
            "hotels_exported": len(unique_hotel_ids),
            "rooms_exported": len(rooms),
            "rows_exported": row_count,
            "file_path": file_path,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.exception(f"Room export failed: export_id={export_id}, error={str(e)}")

        # Update export record with error
        try:
            from app.services.export_history_service import ExportHistoryService

            export_service = ExportHistoryService()
            await export_service.update_status(
                db,
                export_id,
                ExportStatus.FAILED,
                error_message=str(e),
            )
            await db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update export status: {update_error}")

        raise


# Helper functions for export formats

async def _export_hotels_to_excel(hotels: List[Hotel], file_name: str) -> tuple:
    """Export hotels to Excel format."""
    import os
    from openpyxl import Workbook

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Hotels"

    # Header row
    headers = ["Hotel ID", "Name", "Brand", "Status", "City", "Address", "Contact", "Phone"]
    ws.append(headers)

    # Data rows
    for hotel in hotels:
        ws.append([
            hotel.id,
            hotel.name,
            hotel.brand_id if hasattr(hotel, "brand_id") else "",
            hotel.status.value if hasattr(hotel, "status") else "",
            getattr(hotel, "city", ""),
            getattr(hotel, "address", ""),
            getattr(hotel, "contact_name", ""),
            getattr(hotel, "phone", ""),
        ])

    wb.save(file_path)
    file_size = os.path.getsize(file_path)

    return file_path, file_size, len(hotels)


async def _export_hotels_to_csv(hotels: List[Hotel], file_name: str) -> tuple:
    """Export hotels to CSV format."""
    import os
    import csv

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header row
        writer.writerow(["Hotel ID", "Name", "Brand", "Status", "City", "Address", "Contact", "Phone"])
        # Data rows
        for hotel in hotels:
            writer.writerow([
                hotel.id,
                hotel.name,
                hotel.brand_id if hasattr(hotel, "brand_id") else "",
                hotel.status.value if hasattr(hotel, "status") else "",
                getattr(hotel, "city", ""),
                getattr(hotel, "address", ""),
                getattr(hotel, "contact_name", ""),
                getattr(hotel, "phone", ""),
            ])

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(hotels)


async def _export_hotels_to_json(hotels: List[Hotel], file_name: str) -> tuple:
    """Export hotels to JSON format."""
    import os
    import json

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.json")

    data = []
    for hotel in hotels:
        hotel_dict = {
            "id": hotel.id,
            "name": hotel.name,
            "brand_id": hotel.brand_id if hasattr(hotel, "brand_id") else None,
            "status": hotel.status.value if hasattr(hotel, "status") else None,
            "city": getattr(hotel, "city", None),
            "address": getattr(hotel, "address", None),
            "contact_name": getattr(hotel, "contact_name", None),
            "phone": getattr(hotel, "phone", None),
        }
        data.append(hotel_dict)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(hotels)


async def _export_hotels_to_xml(hotels: List[Hotel], file_name: str) -> tuple:
    """Export hotels to XML format."""
    import os
    import xml.etree.ElementTree as ET

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.xml")

    root = ET.Element("Hotels")
    for hotel in hotels:
        hotel_elem = ET.SubElement(root, "Hotel")
        ET.SubElement(hotel_elem, "Id").text = hotel.id
        ET.SubElement(hotel_elem, "Name").text = hotel.name
        if hasattr(hotel, "brand_id"):
            ET.SubElement(hotel_elem, "BrandId").text = hotel.brand_id
        if hasattr(hotel, "status"):
            ET.SubElement(hotel_elem, "Status").text = hotel.status.value
        ET.SubElement(hotel_elem, "City").text = getattr(hotel, "city", "")
        ET.SubElement(hotel_elem, "Address").text = getattr(hotel, "address", "")
        ET.SubElement(hotel_elem, "ContactName").text = getattr(hotel, "contact_name", "")
        ET.SubElement(hotel_elem, "Phone").text = getattr(hotel, "phone", "")

    tree = ET.ElementTree(root)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(hotels)


async def _export_rooms_to_excel(rooms: List[Room], file_name: str) -> tuple:
    """Export rooms to Excel format."""
    import os
    from openpyxl import Workbook

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Rooms"

    # Header row
    headers = ["Room ID", "Hotel ID", "Hotel Name", "Room Type", "Status", "Floor", "Square Meters", "Max Occupancy"]
    ws.append(headers)

    # Data rows
    for room in rooms:
        hotel_name = room.hotel.name if room.hotel else ""
        ws.append([
            room.id,
            room.hotel_id,
            hotel_name,
            getattr(room, "room_type", ""),
            getattr(room, "status", ""),
            getattr(room, "floor", ""),
            getattr(room, "square_meters", ""),
            getattr(room, "max_occupancy", ""),
        ])

    wb.save(file_path)
    file_size = os.path.getsize(file_path)

    return file_path, file_size, len(rooms)


async def _export_rooms_to_csv(rooms: List[Room], file_name: str) -> tuple:
    """Export rooms to CSV format."""
    import os
    import csv

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header row
        writer.writerow(["Room ID", "Hotel ID", "Hotel Name", "Room Type", "Status", "Floor", "Square Meters", "Max Occupancy"])
        # Data rows
        for room in rooms:
            hotel_name = room.hotel.name if room.hotel else ""
            writer.writerow([
                room.id,
                room.hotel_id,
                hotel_name,
                getattr(room, "room_type", ""),
                getattr(room, "status", ""),
                getattr(room, "floor", ""),
                getattr(room, "square_meters", ""),
                getattr(room, "max_occupancy", ""),
            ])

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(rooms)


async def _export_rooms_to_json(rooms: List[Room], file_name: str) -> tuple:
    """Export rooms to JSON format."""
    import os
    import json

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.json")

    data = []
    for room in rooms:
        room_dict = {
            "id": room.id,
            "hotel_id": room.hotel_id,
            "hotel_name": room.hotel.name if room.hotel else None,
            "room_type": getattr(room, "room_type", None),
            "status": getattr(room, "status", None),
            "floor": getattr(room, "floor", None),
            "square_meters": getattr(room, "square_meters", None),
            "max_occupancy": getattr(room, "max_occupancy", None),
        }
        data.append(room_dict)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(rooms)


async def _export_rooms_to_xml(rooms: List[Room], file_name: str) -> tuple:
    """Export rooms to XML format."""
    import os
    import xml.etree.ElementTree as ET

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"{file_name}.xml")

    root = ET.Element("Rooms")
    for room in rooms:
        room_elem = ET.SubElement(root, "Room")
        ET.SubElement(room_elem, "Id").text = room.id
        ET.SubElement(room_elem, "HotelId").text = room.hotel_id
        ET.SubElement(room_elem, "HotelName").text = room.hotel.name if room.hotel else ""
        ET.SubElement(room_elem, "RoomType").text = getattr(room, "room_type", "")
        ET.SubElement(room_elem, "Status").text = getattr(room, "status", "")
        ET.SubElement(room_elem, "Floor").text = str(getattr(room, "floor", ""))
        ET.SubElement(room_elem, "SquareMeters").text = str(getattr(room, "square_meters", ""))
        ET.SubElement(room_elem, "MaxOccupancy").text = str(getattr(room, "max_occupancy", ""))

    tree = ET.ElementTree(root)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)

    file_size = os.path.getsize(file_path)
    return file_path, file_size, len(rooms)
