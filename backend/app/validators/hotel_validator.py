"""
Hotel data validator.

Validates hotel data for completeness, format, and business rules.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


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


class HotelValidator:
    """
    Validator for hotel data.

    Provides validation for:
    - Hotel data completeness
    - Expedia ID format
    - Address information
    - Contact information
    """

    # Expedia hotel ID format: typically alphanumeric, 6-20 characters
    EXPEDIA_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{6,20}$")

    # Email pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Phone pattern (international format support)
    PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{6,20}$")

    # Website URL pattern
    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)? "  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    # Country codes (ISO 3166-1 alpha-2)
    VALID_COUNTRY_CODES = {
        "CN", "US", "GB", "JP", "KR", "AU", "CA", "DE", "FR", "IT",
        "ES", "TH", "SG", "MY", "ID", "VN", "PH", "IN", "RU", "UK",
    }

    # Valid hotel brands
    VALID_BRANDS = {"atour", "atour_x", "zhotel", "ahaus"}

    # Valid hotel statuses
    VALID_STATUSES = {"draft", "pending_review", "approved", "published", "suspended"}

    def __init__(self) -> None:
        """Initialize the hotel validator."""
        pass

    def validate_hotel_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate hotel data completeness.

        Args:
            data: Hotel data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True)

        # Required string fields
        required_strings = {
            "name_cn": "Hotel name (Chinese)",
            "province": "Province",
            "city": "City",
            "address_cn": "Address (Chinese)",
        }

        for field_name, field_label in required_strings.items():
            value = data.get(field_name)
            if not value or (isinstance(value, str) and not value.strip()):
                result.add_error(field_name, f"{field_label} is required", value)

        # Country code validation
        country_code = data.get("country_code", "CN")
        if country_code not in self.VALID_COUNTRY_CODES:
            result.add_error(
                "country_code",
                f"Invalid country code: {country_code}. Must be ISO 3166-1 alpha-2",
                country_code,
            )

        # Brand validation
        brand = data.get("brand")
        if brand and brand not in self.VALID_BRANDS:
            result.add_error(
                "brand",
                f"Invalid brand: {brand}. Valid brands: {', '.join(self.VALID_BRANDS)}",
                brand,
            )

        # Status validation
        status = data.get("status")
        if status and status not in self.VALID_STATUSES:
            result.add_error(
                "status",
                f"Invalid status: {status}. Valid statuses: {', '.join(self.VALID_STATUSES)}",
                status,
            )

        # Optional fields with format validation
        self._validate_email(data, result)
        self._validate_phone(data, result)
        self._validate_website(data, result)
        self._validate_geolocation(data, result)

        # Expedia ID validation (if provided)
        self.validate_expedia_id(data, result)

        return result

    def validate_expedia_id(
        self, data: Dict[str, Any], result: Optional[ValidationResult] = None
    ) -> ValidationResult:
        """
        Validate Expedia ID format.

        Args:
            data: Hotel data dictionary
            result: Existing validation result to append errors to

        Returns:
            ValidationResult with validation status and errors
        """
        if result is None:
            result = ValidationResult(is_valid=True)

        expedia_hotel_id = data.get("expedia_hotel_id")

        if expedia_hotel_id:
            if not self.EXPEDIA_ID_PATTERN.match(expedia_hotel_id):
                result.add_error(
                    "expedia_hotel_id",
                    "Expedia Hotel ID must be 6-20 alphanumeric characters",
                    expedia_hotel_id,
                )

        expedia_chain_code = data.get("expedia_chain_code")
        if expedia_chain_code and len(expedia_chain_code) > 50:
            result.add_error(
                "expedia_chain_code",
                "Expedia Chain Code must not exceed 50 characters",
                expedia_chain_code,
            )

        expedia_property_code = data.get("expedia_property_code")
        if expedia_property_code and len(expedia_property_code) > 50:
            result.add_error(
                "expedia_property_code",
                "Expedia Property Code must not exceed 50 characters",
                expedia_property_code,
            )

        return result

    def validate_address(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate address information.

        Args:
            data: Hotel data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True)

        # Required address fields
        address_cn = data.get("address_cn")
        if not address_cn or not address_cn.strip():
            result.add_error(
                "address_cn", "Address (Chinese) is required", address_cn
            )
        elif len(address_cn) > 500:
            result.add_error(
                "address_cn",
                "Address (Chinese) must not exceed 500 characters",
                address_cn,
            )

        address_en = data.get("address_en")
        if address_en and len(address_en) > 500:
            result.add_error(
                "address_en",
                "Address (English) must not exceed 500 characters",
                address_en,
            )

        # Postal code validation (optional but format check if provided)
        postal_code = data.get("postal_code")
        if postal_code:
            # Basic postal code format check (varies by country)
            # CN: 6 digits, US: 5 or 9 digits, etc.
            postal_pattern = re.compile(r"^[A-Za-z0-9\s\-]{3,20}$")
            if not postal_pattern.match(postal_code):
                result.add_error(
                    "postal_code",
                    "Invalid postal code format",
                    postal_code,
                )

        # City and province validation
        city = data.get("city")
        if city and len(city) > 100:
            result.add_error("city", "City must not exceed 100 characters", city)

        province = data.get("province")
        if province and len(province) > 100:
            result.add_error("province", "Province must not exceed 100 characters", province)

        district = data.get("district")
        if district and len(district) > 100:
            result.add_error("district", "District must not exceed 100 characters", district)

        return result

    def validate_contact(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate contact information.

        Args:
            data: Hotel data dictionary

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True)

        self._validate_email(data, result)
        self._validate_phone(data, result)
        self._validate_website(data, result)

        return result

    def _validate_email(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate email field."""
        email = data.get("email")
        if email and not self.EMAIL_PATTERN.match(email):
            result.add_error("email", "Invalid email format", email)

    def _validate_phone(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate phone field."""
        phone = data.get("phone")
        if phone:
            # Remove spaces and dashes for validation
            cleaned = re.sub(r"[\s\-()]", "", phone)
            if not self.PHONE_PATTERN.match(phone) or len(cleaned) < 6:
                result.add_error(
                    "phone",
                    "Invalid phone number format. Expected: +XX XXXX XXXX or XXX-XXX-XXXX",
                    phone,
                )

    def _validate_website(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate website URL field."""
        website = data.get("website")
        if website and not self.URL_PATTERN.match(website):
            result.add_error("website", "Invalid website URL format", website)

    def _validate_geolocation(self, data: Dict[str, Any], result: ValidationResult) -> None:
        """Validate geolocation fields."""
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is not None:
            try:
                lat = float(latitude)
                if lat < -90 or lat > 90:
                    result.add_error(
                        "latitude",
                        "Latitude must be between -90 and 90",
                        latitude,
                    )
            except (TypeError, ValueError):
                result.add_error("latitude", "Latitude must be a valid number", latitude)

        if longitude is not None:
            try:
                lng = float(longitude)
                if lng < -180 or lng > 180:
                    result.add_error(
                        "longitude",
                        "Longitude must be between -180 and 180",
                        longitude,
                    )
            except (TypeError, ValueError):
                result.add_error("longitude", "Longitude must be a valid number", longitude)

        # Both should be provided together
        if (latitude is None) != (longitude is None):
            result.add_error(
                "geolocation",
                "Both latitude and longitude must be provided together",
                {"latitude": latitude, "longitude": longitude},
            )

    def validate_bulk(
        self, hotels: List[Dict[str, Any]]
    ) -> Dict[int, ValidationResult]:
        """
        Validate multiple hotel records.

        Args:
            hotels: List of hotel data dictionaries

        Returns:
            Dictionary mapping index to ValidationResult
        """
        results: Dict[int, ValidationResult] = {}
        for i, hotel in enumerate(hotels):
            results[i] = self.validate_hotel_data(hotel)
        return results
