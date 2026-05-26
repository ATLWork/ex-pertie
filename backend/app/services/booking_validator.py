"""
Booking data validators for hotel and room data.
"""

import re
from typing import List, Optional, Tuple

from app.models.booking import BookingSource


class ValidationError:
    """Validation error details."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # error, warning, info

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity,
        }


class BookingHotelValidator:
    """
    Validator for Booking hotel data.
    """

    # Required fields
    REQUIRED_FIELDS = ["name_en", "city", "address", "country_code"]

    # Email validation pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Phone validation pattern (international format)
    PHONE_PATTERN = re.compile(r"^\+?[0-9]{6,20}$")

    # Latitude range
    LATITUDE_RANGE = (-90, 90)

    # Longitude range
    LONGITUDE_RANGE = (-180, 180)

    # Allowed country codes
    ALLOWED_COUNTRY_CODES = ["CN", "TW", "HK", "MO", "JP", "KR", "SG", "MY", "TH", "VN", "PH", "ID"]

    def validate_name_en(self, name_en: Optional[str]) -> List[ValidationError]:
        """Validate English hotel name."""
        errors = []
        if not name_en:
            errors.append(ValidationError("name_en", "Hotel English name is required"))
            return errors

        # Check length
        if len(name_en) < 3:
            errors.append(ValidationError("name_en", "Hotel name must be at least 3 characters"))
        if len(name_en) > 255:
            errors.append(ValidationError("name_en", "Hotel name must not exceed 255 characters"))

        # Check for Latin characters only
        if not self._is_latin_only(name_en):
            errors.append(ValidationError(
                "name_en",
                "Hotel name must contain only Latin characters",
                severity="error"
            ))

        # Check for phone number pattern (common mistake)
        if re.search(r"\d{5,}", name_en):
            errors.append(ValidationError(
                "name_en",
                "Hotel name should not contain long digit sequences (possible phone number)",
                severity="warning"
            ))

        return errors

    def validate_email(self, email: Optional[str]) -> List[ValidationError]:
        """Validate email address."""
        errors = []
        if not email:
            return errors

        if not self.EMAIL_PATTERN.match(email):
            errors.append(ValidationError("email", "Invalid email format"))
        return errors

    def validate_phone(self, phone: Optional[str]) -> List[ValidationError]:
        """Validate phone number."""
        errors = []
        if not phone:
            return errors

        # Remove common separators for validation
        clean_phone = re.sub(r"[\s\-()]", "", phone)
        if not self.PHONE_PATTERN.match(clean_phone):
            errors.append(ValidationError(
                "phone",
                "Phone number should be in international format (e.g., +86xxxxxxxx)"
            ))
        return errors

    def validate_geolocation(self, latitude: Optional[float], longitude: Optional[float]) -> List[ValidationError]:
        """Validate latitude and longitude."""
        errors = []
        if latitude is None or longitude is None:
            return errors

        if not (self.LATITUDE_RANGE[0] <= latitude <= self.LATITUDE_RANGE[1]):
            errors.append(ValidationError(
                "latitude",
                f"Latitude must be between {self.LATITUDE_RANGE[0]} and {self.LATITUDE_RANGE[1]}"
            ))

        if not (self.LONGITUDE_RANGE[0] <= longitude <= self.LONGITUDE_RANGE[1]):
            errors.append(ValidationError(
                "longitude",
                f"Longitude must be between {self.LONGITUDE_RANGE[0]} and {self.LONGITUDE_RANGE[1]}"
            ))

        return errors

    def validate_country_code(self, country_code: Optional[str]) -> List[ValidationError]:
        """Validate country code."""
        errors = []
        if not country_code:
            return errors

        if country_code.upper() not in self.ALLOWED_COUNTRY_CODES:
            errors.append(ValidationError(
                "country_code",
                f"Country code must be one of: {', '.join(self.ALLOWED_COUNTRY_CODES)}",
                severity="warning"
            ))
        return errors

    def validate_star_rating(self, star_rating: Optional[float]) -> List[ValidationError]:
        """Validate star rating."""
        errors = []
        if star_rating is None:
            return errors

        if not (0 <= star_rating <= 5):
            errors.append(ValidationError(
                "star_rating",
                "Star rating must be between 0 and 5"
            ))
        return errors

    def _is_latin_only(self, text: str) -> bool:
        """Check if text contains only Latin characters."""
        latin_chars = sum(1 for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c in " -,'.")
        return latin_chars == len(text)

    def validate_hotel(self, hotel_data: dict) -> Tuple[bool, List[ValidationError]]:
        """
        Validate complete hotel data.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        all_errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not hotel_data.get(field):
                all_errors.append(ValidationError(
                    field,
                    f"Required field '{field}' is missing or empty"
                ))

        # Validate individual fields
        all_errors.extend(self.validate_name_en(hotel_data.get("name_en")))
        all_errors.extend(self.validate_email(hotel_data.get("email")))
        all_errors.extend(self.validate_phone(hotel_data.get("phone")))
        all_errors.extend(self.validate_geolocation(
            hotel_data.get("latitude"),
            hotel_data.get("longitude")
        ))
        all_errors.extend(self.validate_country_code(hotel_data.get("country_code")))
        all_errors.extend(self.validate_star_rating(hotel_data.get("star_rating")))

        # Check for errors (not warnings)
        has_errors = any(e.severity == "error" for e in all_errors)
        return not has_errors, all_errors


class BookingRoomValidator:
    """
    Validator for Booking room data.
    """

    # Room type codes that require kitchen
    KITCHEN_REQUIRED_TYPES = ["3", "5000", "8"]  # Apartment, Aparthotel, Condominium

    # Bed type AmenityCode mapping for Booking.com
    BED_TYPE_CODES = {
        "200": "King",
        "249": "Double",
        "203": "Twin",
        "204": "Single",
        "102": "Sofa bed",
        "211": "Bunk bed",
    }

    # Room type codes
    ROOM_TYPE_CODES = {
        "1": "Standard Room",
        "2": "Superior Room",
        "3": "Apartment",
        "4": "Suite",
        "22": "Lodge",
        "35": "Villa",
        "5000": "Aparthotel",
        "5006": "Holiday home",
        "5009": "Holiday park",
    }

    def validate_room_name(self, room_name: Optional[str]) -> List[ValidationError]:
        """Validate room name."""
        errors = []
        if not room_name:
            errors.append(ValidationError("room_name", "Room name is required"))
        return errors

    def validate_occupancy(
        self,
        max_occupancy: Optional[int],
        standard_occupancy: Optional[int],
    ) -> List[ValidationError]:
        """Validate occupancy values."""
        errors = []
        if max_occupancy is None:
            errors.append(ValidationError("max_occupancy", "Max occupancy is required"))
            return errors

        if max_occupancy < 1 or max_occupancy > 30:
            errors.append(ValidationError(
                "max_occupancy",
                "Max occupancy must be between 1 and 30"
            ))

        if standard_occupancy is not None:
            if standard_occupancy < 1 or standard_occupancy > max_occupancy:
                errors.append(ValidationError(
                    "standard_occupancy",
                    "Standard occupancy must be between 1 and max occupancy"
                ))

        return errors

    def validate_bed_configuration(self, bed_type: Optional[str]) -> List[ValidationError]:
        """Validate bed type."""
        errors = []
        if not bed_type:
            errors.append(ValidationError("bed_type", "Bed type is required"))
        return errors

    def validate_kitchen_requirement(
        self,
        room_type: Optional[str],
        amenities: Optional[str],
    ) -> List[ValidationError]:
        """
        Validate kitchen requirement for certain room types.
        Apartment, Aparthotel, Condominium must have kitchen amenities.
        """
        errors = []
        if room_type not in self.KITCHEN_REQUIRED_TYPES:
            return errors

        if not amenities:
            errors.append(ValidationError(
                "amenities",
                f"Room type '{room_type}' requires kitchen amenities",
                severity="error"
            ))
            return errors

        # Check if kitchen-related amenities exist
        kitchen_terms = ["kitchen", "kitchenette", "厨房", "小厨房"]
        has_kitchen = any(term.lower() in amenities.lower() for term in kitchen_terms)

        if not has_kitchen:
            errors.append(ValidationError(
                "amenities",
                f"Room type '{room_type}' (Apartment/Aparthotel) must include kitchen facilities",
                severity="error"
            ))

        return errors

    def validate_room_size(self, room_size: Optional[float]) -> List[ValidationError]:
        """Validate room size."""
        errors = []
        if room_size is None:
            return errors

        if room_size < 10 or room_size > 1000:
            errors.append(ValidationError(
                "room_size",
                "Room size must be between 10 and 1000 square meters",
                severity="warning"
            ))
        return errors

    def validate_smoking_policy(self, smoking_policy: Optional[str]) -> List[ValidationError]:
        """Validate smoking policy."""
        errors = []
        if not smoking_policy:
            return errors

        valid_policies = ["smoking", "non-smoking", "both"]
        if smoking_policy.lower() not in valid_policies:
            errors.append(ValidationError(
                "smoking_policy",
                f"Smoking policy must be one of: {', '.join(valid_policies)}",
                severity="warning"
            ))
        return errors

    def validate_room(self, room_data: dict) -> Tuple[bool, List[ValidationError]]:
        """
        Validate complete room data.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        all_errors = []

        # Check required fields
        if not room_data.get("room_name"):
            all_errors.append(ValidationError(
                "room_name",
                "Required field 'room_name' is missing or empty"
            ))

        if not room_data.get("hotel_id"):
            all_errors.append(ValidationError(
                "hotel_id",
                "Required field 'hotel_id' is missing or empty"
            ))

        # Validate individual fields
        all_errors.extend(self.validate_room_name(room_data.get("room_name")))
        all_errors.extend(self.validate_occupancy(
            room_data.get("max_occupancy"),
            room_data.get("standard_occupancy")
        ))
        all_errors.extend(self.validate_bed_configuration(room_data.get("bed_type")))
        all_errors.extend(self.validate_kitchen_requirement(
            room_data.get("room_type"),
            room_data.get("amenities")
        ))
        all_errors.extend(self.validate_room_size(room_data.get("room_size")))
        all_errors.extend(self.validate_smoking_policy(room_data.get("smoking_policy")))

        # Check for errors (not warnings)
        has_errors = any(e.severity == "error" for e in all_errors)
        return not has_errors, all_errors


# Validator instances
hotel_validator = BookingHotelValidator()
room_validator = BookingRoomValidator()
