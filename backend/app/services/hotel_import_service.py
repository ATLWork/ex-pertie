"""
Hotel import service.

Handles hotel data import from Excel/CSV files with validation and tracking.
"""

import csv
import hashlib
import json
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import openpyxl
except ImportError:
    openpyxl = None  # type: ignore

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hotel import Hotel
from app.models.import_history import ImportHistory, ImportStatus, ImportType
from app.parsers.excel_parser import HotelExcelParser
from app.schemas.hotel import HotelCreate
from app.services.hotel_service import HotelService, hotel_service
from app.validators.hotel_validator import HotelValidator, ValidationResult


class HotelImportService:
    """
    Service for hotel data import operations.

    Provides functionality to:
    - Import hotel data from Excel/CSV files
    - Validate hotel data before import
    - Track import history and errors
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

    def __init__(
        self,
        hotel_service: Optional[HotelService] = None,
        hotel_validator: Optional[HotelValidator] = None,
    ):
        """
        Initialize HotelImportService.

        Args:
            hotel_service: Optional HotelService instance. Defaults to global instance.
            hotel_validator: Optional HotelValidator instance. Defaults to new instance.
        """
        self.hotel_service = hotel_service or hotel_service
        self.validator = hotel_validator or HotelValidator()

    def _compute_file_hash(self, content: bytes) -> str:
        """
        Compute MD5 hash of file content.

        Args:
            content: File content bytes

        Returns:
            MD5 hash string
        """
        return hashlib.md5(content).hexdigest()

    def _normalize_boolean(self, value: Any) -> Optional[bool]:
        """
        Normalize boolean values from various representations.

        Args:
            value: Value to normalize

        Returns:
            Boolean value or None
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return bool(value)

        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "yes", "1", "t", "y"):
                return True
            if value_lower in ("false", "no", "0", "f", "n"):
                return False

        return None

    def _normalize_value(self, value: Any, field: str) -> Any:
        """
        Normalize value based on field type.

        Args:
            value: Value to normalize
            field: Field name

        Returns:
            Normalized value
        """
        if value is None or value == "":
            return None

        # Boolean fields
        if field in ("is_active",):
            return self._normalize_boolean(value)

        # Float fields
        if field in ("latitude", "longitude", "room_size"):
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        # Integer fields
        if field in ("postal_code",):
            # Keep as string but strip whitespace
            if isinstance(value, str):
                return value.strip()
            return str(value)

        # String fields - strip whitespace
        if isinstance(value, str):
            return value.strip()

        return value

    def _parse_excel_file(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Parse Excel file content using HotelExcelParser.

        Args:
            content: File content bytes

        Returns:
            List of row dictionaries
        """
        # Write to temp file for HotelExcelParser
        with BytesIO(content) as bio:
            parser = HotelExcelParser(file_path=bio)
            result = parser.parse()

        if not result.success:
            error_messages = [e.message for e in result.errors]
            raise ValueError(f"Failed to parse Excel file: {'; '.join(error_messages)}")

        return result.data

    def _parse_csv_file(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file content.

        Args:
            content: File content as string

        Returns:
            List of row dictionaries
        """
        reader = csv.reader(StringIO(content))
        headers = next(reader)

        if not headers:
            raise ValueError("CSV file has no headers")

        # Normalize headers to lowercase for matching
        normalized_headers = [h.lower().strip() for h in headers]

        # Column mappings for flexible parsing
        column_mappings = {
            # Basic Info
            "hotel_id": ["hotel_id", "hotelid", "id"],
            "name_cn": ["name_cn", "name_cn", "hotel_name_cn", "hotelnamecn", "name_c"],
            "name_en": ["name_en", "name_en", "hotel_name_en", "hotelnameen", "name_e"],
            "brand": ["brand", "brand_code", "hotel_brand"],
            "status": ["status", "hotel_status"],
            # Location Info
            "country_code": ["country_code", "countrycode", "country"],
            "province": ["province", "province_name"],
            "city": ["city", "city_name"],
            "district": ["district", "district_name"],
            "address_cn": ["address_cn", "address_c", "addresscn", "addr_cn"],
            "address_en": ["address_en", "address_e", "addressen", "addr_en"],
            "postal_code": ["postal_code", "postalcode", "zip", "zipcode"],
            # Contact Info
            "phone": ["phone", "tel", "telephone", "contact_phone"],
            "email": ["email", "email_address", "contact_email"],
            "website": ["website", "url", "hotel_website"],
            # Geolocation
            "latitude": ["latitude", "lat", "y"],
            "longitude": ["longitude", "lng", "lon", "x"],
            # Expedia specific
            "expedia_hotel_id": ["expedia_hotel_id", "expedia_hotelid", "expedia_id"],
            "expedia_chain_code": ["expedia_chain_code", "chain_code"],
            "expedia_property_code": ["expedia_property_code", "property_code"],
            # Timestamps
            "opened_at": ["opened_at", "open_date", "opening_date"],
            "renovated_at": ["renovated_at", "renovation_date"],
        }

        # Create header index mapping
        header_map: Dict[str, int] = {}
        for idx, header in enumerate(normalized_headers):
            for field_name, variations in column_mappings.items():
                if header in variations:
                    header_map[field_name] = idx
                    break

        # Read data rows
        rows: List[Dict[str, Any]] = []
        for row_idx, row in enumerate(reader):
            row_dict: Dict[str, Any] = {}
            is_empty = True

            for field_name, col_idx in header_map.items():
                if col_idx < len(row):
                    value = row[col_idx]
                    normalized = self._normalize_value(value, field_name)
                    row_dict[field_name] = normalized
                    if normalized is not None:
                        is_empty = False

            if not is_empty:
                rows.append(row_dict)

        return rows

    async def validate_before_import(
        self,
        db: AsyncSession,
        hotel_data: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate hotel data before import.

        Args:
            db: Database session
            hotel_data: Hotel data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        # Use HotelValidator for validation
        result = self.validator.validate_hotel_data(hotel_data)

        # Check for duplicate Expedia hotel ID
        expedia_hotel_id = hotel_data.get("expedia_hotel_id")
        if expedia_hotel_id:
            existing = await self.hotel_service.get_hotel_by_expedia_id(
                db, expedia_hotel_id=expedia_hotel_id
            )
            if existing:
                result.add_error(
                    "expedia_hotel_id",
                    f"Hotel with Expedia ID {expedia_hotel_id} already exists",
                    expedia_hotel_id,
                )

        return result

    async def import_single(
        self,
        db: AsyncSession,
        hotel_data: Dict[str, Any],
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Tuple[Optional[Hotel], ValidationResult]:
        """
        Import a single hotel.

        Args:
            db: Database session
            hotel_data: Hotel data dictionary
            operator_id: Optional operator ID for audit
            operator_name: Optional operator name for audit

        Returns:
            Tuple of (created Hotel or None, ValidationResult)
        """
        # Validate
        validation_result = await self.validate_before_import(db, hotel_data)

        if not validation_result.is_valid:
            return None, validation_result

        try:
            # Convert to HotelCreate schema
            # Filter out fields that are not in HotelCreate
            hotel_create = HotelCreate(**hotel_data)
            hotel = await self.hotel_service.create_hotel(db, hotel_in=hotel_create)
            return hotel, validation_result

        except Exception as e:
            validation_result.add_error("_system", f"Import failed: {str(e)}")
            return None, validation_result

    async def import_from_file(
        self,
        db: AsyncSession,
        file_content: bytes,
        file_name: str,
        file_path: str,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        operator_ip: Optional[str] = None,
    ) -> Tuple[ImportHistory, List[Dict[str, Any]]]:
        """
        Import hotel data from Excel/CSV file.

        Args:
            db: Database session
            file_content: File content bytes
            file_name: Original file name
            file_path: Storage path for the file
            operator_id: Optional operator ID for audit
            operator_name: Optional operator name for audit
            operator_ip: Optional operator IP for audit

        Returns:
            Tuple of (ImportHistory record, list of row results)
        """
        # Compute file hash
        file_hash = self._compute_file_hash(file_content)
        file_size = len(file_content)

        # Determine file type
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {file_ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        is_excel = file_ext in {".xlsx", ".xls"}
        is_csv = file_ext == ".csv"

        # Create import history record
        import_history = ImportHistory(
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            import_type=ImportType.HOTEL,
            status=ImportStatus.PROCESSING,
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            skipped_rows=0,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_ip=operator_ip,
            started_at=datetime.utcnow(),
        )
        db.add(import_history)
        await db.flush()

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        row_results: List[Dict[str, Any]] = []
        start_time = datetime.utcnow()

        try:
            # Parse file
            if is_excel:
                rows = self._parse_excel_file(file_content)
            else:
                content = file_content.decode("utf-8")
                rows = self._parse_csv_file(content)

            total_rows = len(rows)
            import_history.total_rows = total_rows

            # Process each row
            for idx, row_data in enumerate(rows):
                row_num = idx + 2  # Excel row number (1-indexed, header is row 1)
                row_result: Dict[str, Any] = {
                    "row": row_num,
                    "success": False,
                    "errors": [],
                    "warnings": [],
                }

                try:
                    # Check if row has any data
                    if not any(v is not None for v in row_data.values()):
                        row_result["warnings"] = [{"field": "_system", "message": "Empty row skipped"}]
                        warnings.append({
                            "row": row_num,
                            "message": "Empty row skipped",
                        })
                        import_history.skipped_rows += 1
                        row_results.append(row_result)
                        continue

                    # Validate
                    validation_result = await self.validate_before_import(db, row_data)

                    if not validation_result.is_valid:
                        row_result["errors"] = validation_result.to_dict()["errors"]
                        errors.append({
                            "row": row_num,
                            "data": row_data,
                            "errors": validation_result.to_dict()["errors"],
                        })
                        import_history.failed_rows += 1
                    else:
                        # Import hotel
                        hotel, _ = await self.import_single(
                            db,
                            row_data,
                            operator_id=operator_id,
                            operator_name=operator_name,
                        )

                        if hotel:
                            row_result["success"] = True
                            row_result["hotel_id"] = hotel.id
                            import_history.success_rows += 1
                        else:
                            import_history.failed_rows += 1

                except Exception as e:
                    row_result["errors"] = [{"field": "_system", "message": str(e)}]
                    errors.append({
                        "row": row_num,
                        "data": row_data,
                        "errors": [{"field": "_system", "message": str(e)}],
                    })
                    import_history.failed_rows += 1

                row_results.append(row_result)

            # Update status
            if import_history.failed_rows == 0 and import_history.skipped_rows == 0:
                import_history.status = ImportStatus.COMPLETED
            elif import_history.success_rows == 0:
                import_history.status = ImportStatus.FAILED
            else:
                import_history.status = ImportStatus.PARTIAL

            # Calculate processing time
            end_time = datetime.utcnow()
            import_history.completed_at = end_time
            import_history.processing_time = (end_time - start_time).total_seconds()

            # Store error and warning logs
            if errors:
                import_history.error_log = json.dumps(errors, ensure_ascii=False)
            if warnings:
                import_history.warning_log = json.dumps(warnings, ensure_ascii=False)

            await db.flush()

        except Exception as e:
            import_history.status = ImportStatus.FAILED
            import_history.error_log = json.dumps([{"row": "file", "message": str(e)}], ensure_ascii=False)
            import_history.completed_at = datetime.utcnow()
            import_history.processing_time = (datetime.utcnow() - start_time).total_seconds()
            await db.flush()
            raise

        return import_history, row_results

    async def get_import_history(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ImportHistory], int]:
        """
        Get hotel import history records.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of ImportHistory, total count)
        """
        result = await db.execute(
            select(ImportHistory)
            .where(ImportHistory.import_type == ImportType.HOTEL)
            .order_by(ImportHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        records = list(result.scalars().all())

        count_result = await db.execute(
            select(ImportHistory).where(ImportHistory.import_type == ImportType.HOTEL)
        )
        total = len(list(count_result.scalars().all()))

        return records, total

    async def get_import_history_by_id(
        self,
        db: AsyncSession,
        import_id: str,
    ) -> Optional[ImportHistory]:
        """
        Get a specific import history record.

        Args:
            db: Database session
            import_id: Import history ID

        Returns:
            ImportHistory instance or None
        """
        result = await db.execute(
            select(ImportHistory).where(ImportHistory.id == import_id)
        )
        return result.scalar_one_or_none()


# Singleton instance
_hotel_import_service: Optional[HotelImportService] = None


def get_hotel_import_service() -> HotelImportService:
    """Get hotel import service singleton."""
    global _hotel_import_service
    if _hotel_import_service is None:
        _hotel_import_service = HotelImportService()
    return _hotel_import_service
