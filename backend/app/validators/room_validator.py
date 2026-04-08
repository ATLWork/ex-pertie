"""
Room data validator.

Validates room data for completeness, format, and business rules.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str, value: Optional[Any] = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, value=value))
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
        }


class RoomValidator:
    """
    Validator for room data.

    Provides validation for:
    - Room data completeness
    - Occupancy configuration
    - Bed type configuration
    - Room code format
    """

    # Room type code pattern: alphanumeric with dashes, 3-50 characters
    ROOM_CODE_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{3,50}$")

    # Bed type options
    VALID_BED_TYPES = {
        "king", "queen", "double", "twin", "single", "double_twin",
        "bunk", "futon", "sofa_bed", "murphy", "king_split",
    }

    # Smoking policy options
    VALID_SMOKING_POLICIES = {"smoking", "non_smoking", "both"}

    # Bathroom type options
    VALID_BATHROOM_TYPES = {
        "private", "shared", "ensuite", "communal", "half_bath",
    }

    # View type options
    VALID_VIEW_TYPES = {
        "city", "sea", "ocean", "garden", "pool", "mountain",
        "lake", "forest", "park", "river", "none", "standard",
    }

    def __init__(self) -> None:
        """Initialize the room validator."""
        pass

    def validate_room_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate room data completeness.

        Args:
            data: Room data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True)

        # Required fields
        required_fields = {
            "hotel_id": "Hotel ID",
            "room_type_code": "Room type code",
            "name_cn": "Room name (Chinese)",
            "max_occupancy": "Maximum occupancy",
            "standard_occupancy": "Standard occupancy",
            "total_rooms": "Total rooms",
        }

        for field_name, field_label in required_fields.items():
            value = data.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                result.add_error(field_name, f"{field_label} is required", value)

        # Room type code format validation
        room_type_code = data.get("room_type_code")
        if room_type_code:
            if not self.validate_room_code(room_type_code).is_valid:
                result.add_error(
                    "room_type_code",
                    "Room type code must be 3-50 alphanumeric characters (dashes and underscores allowed)",
                    room_type_code,
                )

        # Occupancy validation
        self.validate_occupancy(data, result)

        # Bed type validation (optional but if provided must be valid)
        bed_type = data.get("bed_type")
        if bed_type and bed_type.lower() not in self.VALID_BED_TYPES:
            result.add_error(
                "bed_type",
                f"Invalid bed type: {bed_type}. Valid types: {', '.join(sorted(self.VALID_BED_TYPES))}",
                bed_type,
            )

        # Room size validation (optional but must be positive if provided)
        room_size = data.get("room_size")
        if room_size is not None:
            try:
                size = float(room_size)
                if size <= 0:
                    result.add_error("room_size", "Room size must be positive", room_size)
                elif size > 10000:
                    result.add_error("room_size", "Room size seems unreasonably large", room_size)
            except (TypeError, ValueError):
                result.add_error("room_size", "Room size must be a valid number", room_size)

        # Total rooms validation
        total_rooms = data.get("total_rooms")
        if total_rooms is not None:
            try:
                total = int(total_rooms)
                if total <= 0:
                    result.add_error("total_rooms", "Total rooms must be positive", total_rooms)
                elif total > 10000:
                    result.add_error("total_rooms", "Total rooms seems unreasonably large", total_rooms)
            except (TypeError, ValueError):
                result.add_error("total_rooms", "Total rooms must be a valid integer", total_rooms)

        # Expedia ID validation (if provided)
        self._validate_expedia_room_id(data, result)

        # Name length validation
        name_cn = data.get("name_cn")
        if name_cn and len(name_cn) > 255:
            result.add_error("name_cn", "Room name (Chinese) must not exceed 255 characters", name_cn)

        name_en = data.get("name_en")
        if name_en and len(name_en) > 255:
            result.add_error("name_en", "Room name (English) must not exceed 255 characters", name_en)

        # Description length validation (if text fields)
        description_cn = data.get("description_cn")
        if description_cn and len(description_cn) > 10000:
            result.add_error("description_cn", "Description (Chinese) must not exceed 10000 characters", description_cn)

        description_en = data.get("description_en")
        if description_en and len(description_en) > 10000:
            result.add_error("description_en", "Description (English) must not exceed 10000 characters", description_en)

        # Floor range validation (if provided)
        floor_range = data.get("floor_range")
        if floor_range:
            # Basic format check: single floor or range like "3-5"
            floor_pattern = re.compile(r"^(\d+)(-\d+)?$")
            if not floor_pattern.match(floor_range):
                result.add_error("floor_range", "Invalid floor range format (expected: '3' or '3-5')", floor_range)

        return result

    def validate_occupancy(
        self, data: Dict[str, Any], result: Optional[ValidationResult] = None
    ) -> ValidationResult:
        """
        Validate occupancy configuration.

        Args:
            data: Room data dictionary
            result: Existing validation result to append errors to

        Returns:
            ValidationResult with validation status and errors
        """
        if result is None:
            result = ValidationResult(is_valid=True)

        max_occupancy = data.get("max_occupancy")
        standard_occupancy = data.get("standard_occupancy")

        # Validate max_occupancy range
        if max_occupancy is not None:
            try:
                max_occ = int(max_occupancy)
                if max_occ < 1:
                    result.add_error("max_occupancy", "Maximum occupancy must be at least 1", max_occupancy)
                elif max_occ > 20:
                    result.add_error("max_occupancy", "Maximum occupancy seems unreasonably high (max: 20)", max_occupancy)
            except (TypeError, ValueError):
                result.add_error("max_occupancy", "Maximum occupancy must be a valid integer", max_occupancy)

        # Validate standard_occupancy range
        if standard_occupancy is not None:
            try:
                std_occ = int(standard_occupancy)
                if std_occ < 1:
                    result.add_error("standard_occupancy", "Standard occupancy must be at least 1", standard_occupancy)
                elif std_occ > 10:
                    result.add_error("standard_occupancy", "Standard occupancy seems unreasonably high (max: 10)", standard_occupancy)
            except (TypeError, ValueError):
                result.add_error("standard_occupancy", "Standard occupancy must be a valid integer", standard_occupancy)

        # Standard occupancy should not exceed max occupancy
        if (
            max_occupancy is not None
            and standard_occupancy is not None
            and isinstance(max_occupancy, (int, str))
            and isinstance(standard_occupancy, (int, str))
        ):
            try:
                max_occ = int(max_occupancy)
                std_occ = int(standard_occupancy)
                if std_occ > max_occ:
                    result.add_error(
                        "standard_occupancy",
                        f"Standard occupancy ({std_occ}) cannot exceed maximum occupancy ({max_occ})",
                        standard_occupancy,
                    )
            except (TypeError, ValueError):
                pass  # Already handled above

        return result

    def validate_bed_type(
        self, data: Dict[str, Any], result: Optional[ValidationResult] = None
    ) -> ValidationResult:
        """
        Validate bed type configuration.

        Args:
            data: Room data dictionary
            result: Existing validation result to append errors to

        Returns:
            ValidationResult with validation status and errors
        """
        if result is None:
            result = ValidationResult(is_valid=True)

        bed_type = data.get("bed_type")

        if bed_type:
            # Normalize to lowercase for comparison
            normalized_bed_type = bed_type.lower().strip()
            if normalized_bed_type not in self.VALID_BED_TYPES:
                result.add_error(
                    "bed_type",
                    f"Invalid bed type: {bed_type}. Valid types: {', '.join(sorted(self.VALID_BED_TYPES))}",
                    bed_type,
                )

        return result

    def validate_room_code(
        self, room_code: str, result: Optional[ValidationResult] = None
    ) -> ValidationResult:
        """
        Validate room code format.

        Args:
            room_code: Room type code
            result: Existing validation result to append errors to

        Returns:
            ValidationResult with validation status and errors
        """
        if result is None:
            result = ValidationResult(is_valid=True)

        if not room_code:
            result.add_error("room_type_code", "Room type code is required", room_code)
            return result

        if not self.ROOM_CODE_PATTERN.match(room_code):
            result.add_error(
                "room_type_code",
                "Room type code must be 3-50 alphanumeric characters (dashes and underscores allowed)",
                room_code,
            )

        return result

    def _validate_expedia_room_id(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate Expedia room ID field."""
        expedia_room_id = data.get("expedia_room_id")
        if expedia_room_id:
            # Similar pattern to room code but 6-50 characters
            pattern = re.compile(r"^[A-Za-z0-9\-_]{6,50}$")
            if not pattern.match(expedia_room_id):
                result.add_error(
                    "expedia_room_id",
                    "Expedia Room ID must be 6-50 alphanumeric characters",
                    expedia_room_id,
                )

        expedia_room_type_code = data.get("expedia_room_type_code")
        if expedia_room_type_code and len(expedia_room_type_code) > 50:
            result.add_error(
                "expedia_room_type_code",
                "Expedia Room Type Code must not exceed 50 characters",
                expedia_room_type_code,
            )

    def validate_bulk(self, rooms: List[Dict[str, Any]]) -> Dict[int, ValidationResult]:
        """
        Validate multiple room records.

        Args:
            rooms: List of room data dictionaries

        Returns:
            Dictionary mapping index to ValidationResult
        """
        results: Dict[int, ValidationResult] = {}
        for i, room in enumerate(rooms):
            results[i] = self.validate_room_data(room)
        return results
