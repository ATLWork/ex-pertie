"""
Booking data validator.

Unified validator for hotel and room data that combines hotel and room validation
with cross-entity business rule validation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.validators.hotel_validator import HotelValidator
from app.validators.room_validator import RoomValidator


@dataclass
class BookingValidationError:
    """Represents a booking validation error."""

    entity_type: str  # "hotel" or "room"
    field: str
    message: str
    value: Optional[Any] = None
    entity_index: Optional[int] = None  # For bulk validation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_type": self.entity_type,
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "entity_index": self.entity_index,
        }


@dataclass
class BookingValidationResult:
    """Result of a booking validation operation."""

    is_valid: bool = True
    hotel_errors: List[BookingValidationError] = field(default_factory=list)
    room_errors: List[BookingValidationError] = field(default_factory=list)
    cross_entity_errors: List[BookingValidationError] = field(default_factory=list)

    def add_hotel_error(
        self,
        field: str,
        message: str,
        value: Optional[Any] = None,
        entity_index: Optional[int] = None,
    ) -> None:
        """Add a hotel validation error."""
        self.hotel_errors.append(
            BookingValidationError(
                entity_type="hotel",
                field=field,
                message=message,
                value=value,
                entity_index=entity_index,
            )
        )
        self.is_valid = False

    def add_room_error(
        self,
        field: str,
        message: str,
        value: Optional[Any] = None,
        entity_index: Optional[int] = None,
    ) -> None:
        """Add a room validation error."""
        self.room_errors.append(
            BookingValidationError(
                entity_type="room",
                field=field,
                message=message,
                value=value,
                entity_index=entity_index,
            )
        )
        self.is_valid = False

    def add_cross_entity_error(
        self,
        field: str,
        message: str,
        value: Optional[Any] = None,
        entity_index: Optional[int] = None,
    ) -> None:
        """Add a cross-entity validation error."""
        self.cross_entity_errors.append(
            BookingValidationError(
                entity_type="cross_entity",
                field=field,
                message=message,
                value=value,
                entity_index=entity_index,
            )
        )
        self.is_valid = False

    @property
    def errors(self) -> List[BookingValidationError]:
        """Get all errors combined."""
        return self.hotel_errors + self.room_errors + self.cross_entity_errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "hotel_errors": [e.to_dict() for e in self.hotel_errors],
            "room_errors": [e.to_dict() for e in self.room_errors],
            "cross_entity_errors": [e.to_dict() for e in self.cross_entity_errors],
            "total_errors": len(self.errors),
        }


class BookingValidator:
    """
    Unified validator for booking-related data.

    Combines hotel and room validation with cross-entity business rules:
    - Hotel data completeness and format validation
    - Room data completeness and format validation
    - Cross-entity validation (room belongs to valid hotel, etc.)
    """

    def __init__(self) -> None:
        """Initialize the booking validator."""
        self.hotel_validator = HotelValidator()
        self.room_validator = RoomValidator()

    def validate_hotel(self, data: Dict[str, Any]) -> BookingValidationResult:
        """
        Validate hotel data.

        Args:
            data: Hotel data dictionary

        Returns:
            BookingValidationResult with validation status and errors
        """
        result = BookingValidationResult()
        hotel_result = self.hotel_validator.validate_hotel_data(data)

        if not hotel_result.is_valid:
            for error in hotel_result.errors:
                result.add_hotel_error(error.field, error.message, error.value)

        return result

    def validate_room(
        self, data: Dict[str, Any], hotel_exists: bool = True
    ) -> BookingValidationResult:
        """
        Validate room data.

        Args:
            data: Room data dictionary
            hotel_exists: Whether the hotel referenced by hotel_id exists

        Returns:
            BookingValidationResult with validation status and errors
        """
        result = BookingValidationResult()
        room_result = self.room_validator.validate_room_data(data)

        if not room_result.is_valid:
            for error in room_result.errors:
                result.add_room_error(error.field, error.message, error.value)

        # Cross-entity validation: hotel must exist
        hotel_id = data.get("hotel_id")
        if not hotel_id:
            # This is already caught by room validator
            pass
        elif not hotel_exists:
            result.add_cross_entity_error(
                "hotel_id",
                f"Hotel with ID {hotel_id} does not exist",
                hotel_id,
            )

        return result

    def validate_hotel_room_pair(
        self,
        hotel_data: Dict[str, Any],
        room_data: Dict[str, Any],
    ) -> BookingValidationResult:
        """
        Validate a hotel and its associated room together.

        Args:
            hotel_data: Hotel data dictionary
            room_data: Room data dictionary

        Returns:
            BookingValidationResult with validation status and errors
        """
        result = BookingValidationResult()

        # Validate hotel
        hotel_result = self.validate_hotel(hotel_data)
        result.hotel_errors.extend(hotel_result.hotel_errors)

        # Validate room with hotel context
        room_result = self.validate_room(room_data, hotel_exists=True)
        result.room_errors.extend(room_result.room_errors)

        # Cross-entity validation: ensure room belongs to correct hotel
        if room_data.get("hotel_id") != hotel_data.get("id"):
            # If room has a hotel_id set, check it matches
            if room_data.get("hotel_id") and hotel_data.get("id"):
                if room_data["hotel_id"] != hotel_data["id"]:
                    result.add_cross_entity_error(
                        "hotel_id",
                        "Room's hotel_id does not match the hotel being created",
                        room_data.get("hotel_id"),
                    )

        # Validate total rooms consistency
        self._validate_room_totals(hotel_data, room_data, result)

        return result

    def _validate_room_totals(
        self,
        hotel_data: Dict[str, Any],
        room_data: Dict[str, Any],
        result: BookingValidationResult,
    ) -> None:
        """Validate room totals against hotel configuration."""
        total_rooms = room_data.get("total_rooms", 1)
        if total_rooms <= 0:
            result.add_room_error(
                "total_rooms",
                "Total rooms must be positive",
                total_rooms,
            )

    def validate_bulk_hotels(
        self, hotels: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[int, BookingValidationResult]], List[Dict[str, Any]]]:
        """
        Validate multiple hotel records.

        Args:
            hotels: List of hotel data dictionaries

        Returns:
            Tuple of (validation_results dict mapping index to result, errors list)
        """
        results: Dict[int, BookingValidationResult] = {}
        errors: List[Dict[str, Any]] = []

        for i, hotel in enumerate(hotels):
            try:
                result = self.validate_hotel(hotel)
                results[i] = result
                if not result.is_valid:
                    errors.append(
                        {
                            "index": i,
                            "hotel_id": hotel.get("id"),
                            "errors": [e.to_dict() for e in result.errors],
                        }
                    )
            except Exception as e:
                errors.append({"index": i, "hotel": hotel, "error": str(e)})

        return results, errors

    def validate_bulk_rooms(
        self,
        rooms: List[Dict[str, Any]],
        existing_hotel_ids: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[int, BookingValidationResult]], List[Dict[str, Any]]]:
        """
        Validate multiple room records.

        Args:
            rooms: List of room data dictionaries
            existing_hotel_ids: List of valid hotel IDs for cross-validation

        Returns:
            Tuple of (validation_results dict mapping index to result, errors list)
        """
        results: Dict[int, BookingValidationResult] = {}
        errors: List[Dict[str, Any]] = []
        existing_ids = set(existing_hotel_ids or [])

        for i, room in enumerate(rooms):
            try:
                hotel_id = room.get("hotel_id")
                hotel_exists = hotel_id in existing_ids if hotel_id else False
                result = self.validate_room(room, hotel_exists=hotel_exists)
                results[i] = result
                if not result.is_valid:
                    errors.append(
                        {
                            "index": i,
                            "room_id": room.get("id"),
                            "errors": [e.to_dict() for e in result.errors],
                        }
                    )
            except Exception as e:
                errors.append({"index": i, "room": room, "error": str(e)})

        return results, errors

    def validate_bulk_hotel_room_pairs(
        self,
        hotel_room_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    ) -> Tuple[List[Dict[int, BookingValidationResult]], List[Dict[str, Any]]]:
        """
        Validate multiple hotel-room pairs.

        Args:
            hotel_room_pairs: List of (hotel_data, room_data) tuples

        Returns:
            Tuple of (validation_results dict mapping index to result, errors list)
        """
        results: Dict[int, BookingValidationResult] = {}
        errors: List[Dict[str, Any]] = []

        for i, (hotel, room) in enumerate(hotel_room_pairs):
            try:
                result = self.validate_hotel_room_pair(hotel, room)
                results[i] = result
                if not result.is_valid:
                    errors.append(
                        {
                            "index": i,
                            "hotel_id": hotel.get("id"),
                            "room_id": room.get("id"),
                            "errors": [e.to_dict() for e in result.errors],
                        }
                    )
            except Exception as e:
                errors.append(
                    {
                        "index": i,
                        "hotel": hotel,
                        "room": room,
                        "error": str(e),
                    }
                )

        return results, errors


# Singleton instance
_booking_validator: Optional[BookingValidator] = None


def get_booking_validator() -> BookingValidator:
    """Get booking validator singleton."""
    global _booking_validator
    if _booking_validator is None:
        _booking_validator = BookingValidator()
    return _booking_validator