"""
CSV file parser for hotel and room data.

Parses .csv format files with flexible column mapping and error reporting.
"""

import csv
import logging
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class CSVParseError:
    """Represents a parsing error for a specific row."""

    row: int
    field: Optional[str] = None
    message: str = ""
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "row": self.row,
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }


@dataclass
class CSVParseResult:
    """Result of a CSV parsing operation."""

    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[CSVParseError] = field(default_factory=list)
    total_rows: int = 0
    success_rows: int = 0
    error_rows: int = 0

    def add_error(
        self, row: int, message: str, field: Optional[str] = None, value: Any = None
    ) -> None:
        """Add a parse error."""
        self.errors.append(
            CSVParseError(row=row, field=field, message=message, value=value)
        )
        self.success = False
        self.error_rows += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "errors": [e.to_dict() for e in self.errors],
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "error_rows": self.error_rows,
        }


class CSVParser:
    """
    Base class for CSV file parsing.

    Provides common functionality for parsing CSV files with flexible column mapping.

    Attributes:
        delimiter: CSV delimiter character (default: comma)
        quotechar: Quote character (default: double quote)
        encoding: File encoding (default: utf-8)
    """

    def __init__(
        self,
        delimiter: str = ",",
        quotechar: str = '"',
        encoding: str = "utf-8",
    ) -> None:
        """
        Initialize the CSV parser.

        Args:
            delimiter: CSV delimiter character (default: comma)
            quotechar: Quote character (default: double quote)
            encoding: File encoding (default: utf-8)
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self._headers: List[str] = []

    def _normalize_value(self, value: Any) -> Any:
        """
        Normalize a cell value.

        Args:
            value: Raw cell value

        Returns:
            Normalized value
        """
        if value is None:
            return None
        if isinstance(value, (int, float, bool)):
            return value
        # Convert to string and strip whitespace
        return str(value).strip()

    def _is_row_empty(self, row_values: List[Any]) -> bool:
        """
        Check if a row is empty (all values are None or empty).

        Args:
            row_values: List of cell values

        Returns:
            True if row is empty
        """
        return all(v is None or str(v).strip() == "" for v in row_values)

    def _read_headers(self, reader: csv.reader) -> List[str]:
        """
        Read headers from the first row.

        Args:
            reader: CSV reader iterator

        Returns:
            List of header strings
        """
        try:
            headers = next(reader)
        except StopIteration:
            return []

        return [
            str(h).strip() if h is not None else f"column_{i}"
            for i, h in enumerate(headers)
        ]

    def parse_content(self, content: str) -> CSVParseResult:
        """
        Parse CSV content from string.

        Args:
            content: CSV content as string

        Returns:
            CSVParseResult containing parsed data and any errors
        """
        result = CSVParseResult(success=True)

        try:
            # Parse content using StringIO
            reader = csv.reader(StringIO(content), delimiter=self.delimiter)

            # Read headers
            self._headers = self._read_headers(reader)
            logger.debug(f"CSV Headers: {self._headers}")

            if not self._headers:
                result.add_error(row=1, message="CSV file has no headers")
                return result

            # Get total rows for reporting
            all_rows = list(reader)
            result.total_rows = len(all_rows)

            # Process each row
            for row_idx, row_values in enumerate(all_rows, start=2):
                try:
                    # Skip empty rows
                    if self._is_row_empty(row_values):
                        continue

                    # Convert row to dictionary
                    row_dict: Dict[str, Any] = {}
                    for col_index, header in enumerate(self._headers):
                        if col_index < len(row_values):
                            row_dict[header] = self._normalize_value(
                                row_values[col_index]
                            )
                        else:
                            row_dict[header] = None

                    # Parse and validate row
                    parsed_row = self._parse_row(row_idx, row_dict)
                    if parsed_row is not None:
                        result.data.append(parsed_row)
                        result.success_rows += 1
                    else:
                        result.error_rows += 1

                except Exception as e:
                    logger.warning(f"Error parsing row {row_idx}: {e}")
                    result.add_error(
                        row=row_idx, message=f"Failed to parse row: {str(e)}"
                    )
                    result.error_rows += 1

        except Exception as e:
            logger.error(f"Failed to parse CSV content: {e}")
            result.success = False
            result.add_error(row=0, message=f"Failed to parse content: {str(e)}")

        logger.info(
            f"CSV Parse complete: {result.success_rows} success, {result.error_rows} errors"
        )
        return result

    def _parse_row(self, row_index: int, row_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse and validate a single row. Override in subclasses.

        Args:
            row_index: Row index (1-indexed)
            row_dict: Row data as dictionary

        Returns:
            Parsed row data or None if invalid
        """
        return row_dict

    @property
    def headers(self) -> List[str]:
        """Get the parsed headers."""
        return self._headers


class HotelCSVParser(CSVParser):
    """
    Parser for hotel data CSV files.

    Parses hotel information from CSV files with standard column mapping
    and business logic validation.
    """

    # Standard column mappings for hotel data
    COLUMN_MAPPINGS = {
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

    # Field types for conversion
    FIELD_TYPES = {
        "latitude": float,
        "longitude": float,
    }

    def __init__(
        self,
        delimiter: str = ",",
        quotechar: str = '"',
        encoding: str = "utf-8",
        column_mapping: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize the hotel CSV parser.

        Args:
            delimiter: CSV delimiter character
            quotechar: Quote character
            encoding: File encoding
            column_mapping: Custom column mapping (optional)
        """
        super().__init__(delimiter, quotechar, encoding)
        self.column_mapping = column_mapping or self.COLUMN_MAPPINGS
        self._normalized_headers: Dict[str, str] = {}

    def _normalize_headers(self, headers: List[str]) -> Dict[str, str]:
        """
        Normalize headers by mapping them to standard field names.

        Args:
            headers: Original headers from CSV file

        Returns:
            Mapping from original header to normalized field name
        """
        normalized: Dict[str, str] = {}
        for header in headers:
            header_lower = header.lower().strip()
            for field_name, variations in self.column_mapping.items():
                if header_lower in [v.lower() for v in variations]:
                    normalized[header] = field_name
                    break
        return normalized

    def _parse_row(self, row_index: int, row_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse and validate a hotel data row.

        Args:
            row_index: Row index (1-indexed)
            row_dict: Row data as dictionary

        Returns:
            Parsed hotel data or None if invalid
        """
        # Normalize headers on first row
        if not self._normalized_headers:
            self._normalized_headers = self._normalize_headers(list(row_dict.keys()))

        # Rename keys to normalized field names
        parsed_row: Dict[str, Any] = {}
        for original_key, value in row_dict.items():
            normalized_key = self._normalized_headers.get(original_key, original_key)
            parsed_row[normalized_key] = value

        # Apply field type conversions
        for field_name, field_type in self.FIELD_TYPES.items():
            if field_name in parsed_row and parsed_row[field_name] is not None:
                try:
                    if field_type == float:
                        parsed_row[field_name] = float(parsed_row[field_name])
                    elif field_type == int:
                        parsed_row[field_name] = int(parsed_row[field_name])
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert {field_name} to {field_type}")

        return parsed_row


class RoomCSVParser(CSVParser):
    """
    Parser for room data CSV files.

    Parses room/inventory information from CSV files with standard column mapping
    and business logic validation.
    """

    # Standard column mappings for room data
    COLUMN_MAPPINGS = {
        # Basic Info
        "room_id": ["room_id", "roomid", "id"],
        "hotel_id": ["hotel_id", "hotelid", "parent_hotel_id"],
        "room_type_code": ["room_type_code", "roomtypecode", "room_code", "type_code"],
        "name_cn": ["name_cn", "name_c", "room_name_cn", "roomnamecn"],
        "name_en": ["name_en", "name_e", "room_name_en", "roomnameen"],
        "description_cn": ["description_cn", "desc_cn", "descriptioncn"],
        "description_en": ["description_en", "desc_en", "descriptionen"],
        # Room Details
        "bed_type": ["bed_type", "bedtype", "bed"],
        "max_occupancy": ["max_occupancy", "maxocc", "occupancy_max"],
        "standard_occupancy": ["standard_occupancy", "stdocc", "occupancy_standard"],
        "room_size": ["room_size", "roomsize", "size"],
        "floor_range": ["floor_range", "floorrange", "floor"],
        "total_rooms": ["total_rooms", "totalrooms", "room_count", "rooms"],
        # Expedia specific
        "expedia_room_id": ["expedia_room_id", "expedia_roomid"],
        "expedia_room_type_code": ["expedia_room_type_code", "expedia_roomtypecode"],
        # Extension fields
        "amenities_cn": ["amenities_cn", "amenitiesc", "amenities_cn"],
        "amenities_en": ["amenities_en", "amenities_e", "amenities_en"],
        "view_type": ["view_type", "viewtype", "view"],
        "balcony": ["balcony", "has_balcony"],
        "smoking_policy": ["smoking_policy", "smoking", "smoke_policy"],
        "bathroom_type": ["bathroom_type", "bathroomtype", "bathroom"],
        "is_active": ["is_active", "active", "status"],
    }

    # Field types for conversion
    FIELD_TYPES = {
        "room_size": float,
        "max_occupancy": int,
        "standard_occupancy": int,
        "total_rooms": int,
        "balcony": bool,
        "is_active": bool,
    }

    def __init__(
        self,
        delimiter: str = ",",
        quotechar: str = '"',
        encoding: str = "utf-8",
        column_mapping: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize the room CSV parser.

        Args:
            delimiter: CSV delimiter character
            quotechar: Quote character
            encoding: File encoding
            column_mapping: Custom column mapping (optional)
        """
        super().__init__(delimiter, quotechar, encoding)
        self.column_mapping = column_mapping or self.COLUMN_MAPPINGS
        self._normalized_headers: Dict[str, str] = {}

    def _normalize_headers(self, headers: List[str]) -> Dict[str, str]:
        """
        Normalize headers by mapping them to standard field names.

        Args:
            headers: Original headers from CSV file

        Returns:
            Mapping from original header to normalized field name
        """
        normalized: Dict[str, str] = {}
        for header in headers:
            header_lower = header.lower().strip()
            for field_name, variations in self.column_mapping.items():
                if header_lower in [v.lower() for v in variations]:
                    normalized[header] = field_name
                    break
        return normalized

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

    def _parse_row(self, row_index: int, row_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse and validate a room data row.

        Args:
            row_index: Row index (1-indexed)
            row_dict: Row data as dictionary

        Returns:
            Parsed room data or None if invalid
        """
        # Normalize headers on first row
        if not self._normalized_headers:
            self._normalized_headers = self._normalize_headers(list(row_dict.keys()))

        # Rename keys to normalized field names
        parsed_row: Dict[str, Any] = {}
        for original_key, value in row_dict.items():
            normalized_key = self._normalized_headers.get(original_key, original_key)
            parsed_row[normalized_key] = value

        # Apply field type conversions
        for field_name, field_type in self.FIELD_TYPES.items():
            if field_name in parsed_row and parsed_row[field_name] is not None:
                try:
                    value = parsed_row[field_name]
                    if field_type == bool:
                        # Handle string boolean values
                        if isinstance(value, str):
                            parsed_row[field_name] = value.lower() in ("true", "yes", "1", "y")
                        else:
                            parsed_row[field_name] = bool(value)
                    elif field_type == float:
                        parsed_row[field_name] = float(value)
                    elif field_type == int:
                        parsed_row[field_name] = int(value)
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert {field_name} to {field_type}")

        return parsed_row