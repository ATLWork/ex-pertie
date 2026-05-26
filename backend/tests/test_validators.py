"""
Tests for data validation components.
"""

import pytest
from datetime import datetime

from app.validators.validation_engine import (
    ValidationEngine,
    ValidationResult,
    ValidationError,
    ValidationRule,
    RuleType,
    validate,
)
from app.validators.hotel_validator import HotelValidator


class TestValidationEngine:
    """Test cases for ValidationEngine."""

    def test_add_rule_required(self):
        """Test adding required rule."""
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.REQUIRED)

        result = engine.validate({"name": "John"})
        assert result.is_valid is True

        result = engine.validate({})
        assert result.is_valid is False
        assert any(e.field == "name" for e in result.errors)

    def test_add_rule_type(self):
        """Test adding type rule."""
        engine = ValidationEngine()
        engine.add_rule("age", RuleType.TYPE, expected_type=int)

        # Valid cases
        result = engine.validate({"age": 25})
        assert result.is_valid is True

        result = engine.validate({"age": "25"})
        assert result.is_valid is True

        result = engine.validate({"age": "25.5"})
        assert result.is_valid is False

    def test_add_rule_range(self):
        """Test adding range rule."""
        engine = ValidationEngine()
        engine.add_rule("age", RuleType.RANGE, min_value=0, max_value=150)

        result = engine.validate({"age": 25})
        assert result.is_valid is True

        result = engine.validate({"age": -1})
        assert result.is_valid is False

        result = engine.validate({"age": 200})
        assert result.is_valid is False

    def test_add_rule_length(self):
        """Test adding length rule."""
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.LENGTH, min_value=1, max_value=100)

        result = engine.validate({"name": "John"})
        assert result.is_valid is True

        result = engine.validate({"name": ""})
        assert result.is_valid is False

        result = engine.validate({"name": "x" * 200})
        assert result.is_valid is False

    def test_add_rule_pattern(self):
        """Test adding pattern rule."""
        engine = ValidationEngine()
        engine.add_rule("email", RuleType.PATTERN, pattern=r"^[\w.-]+@[\w.-]+\.\w+$")

        result = engine.validate({"email": "test@example.com"})
        assert result.is_valid is True

        result = engine.validate({"email": "invalid"})
        assert result.is_valid is False

    def test_add_rule_enum(self):
        """Test adding enum rule."""
        engine = ValidationEngine()
        engine.add_rule("status", RuleType.ENUM, enum_values=["draft", "published", "deleted"])

        result = engine.validate({"status": "draft"})
        assert result.is_valid is True

        result = engine.validate({"status": "invalid"})
        assert result.is_valid is False

    def test_add_rule_custom(self):
        """Test adding custom rule."""
        engine = ValidationEngine()
        engine.add_rule("password", RuleType.CUSTOM, custom_func=lambda x: len(x) >= 8)

        result = engine.validate({"password": "longpassword"})
        assert result.is_valid is True

        result = engine.validate({"password": "short"})
        assert result.is_valid is False

    def test_add_rules_multiple(self):
        """Test adding multiple rules."""
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.REQUIRED)
        engine.add_rule("age", RuleType.TYPE, expected_type=int)
        engine.add_rule("email", RuleType.PATTERN, pattern=r"^[\w.-]+@[\w.-]+\.\w+$")

        result = engine.validate({"name": "John", "age": 30, "email": "john@example.com"})
        assert result.is_valid is True

        result = engine.validate({"name": "John", "age": "old", "email": "invalid"})
        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_clear_rules(self):
        """Test clearing all rules."""
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.REQUIRED)

        result = engine.validate({})
        assert result.is_valid is False

        engine.clear_rules()

        result = engine.validate({})
        assert result.is_valid is True

    def test_validate_field_single(self):
        """Test validating single field."""
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.REQUIRED)
        engine.add_rule("name", RuleType.LENGTH, min_value=2)

        result = engine.validate_field("name", "John")
        assert result.is_valid is True

        result = engine.validate_field("name", "")
        assert result.is_valid is False

    def test_from_dict(self):
        """Test creating engine from dict configuration."""
        config = [
            {"field": "name", "rule_type": "required"},
            {"field": "age", "rule_type": "type", "expected_type": "int"},
            {"field": "score", "rule_type": "range", "min_value": 0, "max_value": 100},
        ]
        engine = ValidationEngine.from_dict(config)

        result = engine.validate({"name": "John", "age": 25, "score": 85})
        assert result.is_valid is True

        result = engine.validate({"name": "John", "age": 25, "score": 150})
        assert result.is_valid is False


class TestValidationResult:
    """Test cases for ValidationResult."""

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult(is_valid=True)
        result.add_error("name", "Name is required", "name")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].message == "Name is required"

    def test_get_field_errors(self):
        """Test getting errors for specific field."""
        result = ValidationResult(is_valid=True)
        result.add_error("name", "Name is required")
        result.add_error("name", "Name too short")
        result.add_error("email", "Invalid email")

        name_errors = result.get_field_errors("name")
        assert len(name_errors) == 2

        email_errors = result.get_field_errors("email")
        assert len(email_errors) == 1

        other_errors = result.get_field_errors("other")
        assert len(other_errors) == 0

    def test_to_dict(self):
        """Test converting result to dict."""
        result = ValidationResult(is_valid=True)
        result.add_error("name", "Name is required")

        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["error_count"] == 1
        assert len(d["errors"]) == 1


class TestValidationError:
    """Test cases for ValidationError."""

    def test_to_dict(self):
        """Test converting error to dict."""
        error = ValidationError(
            field="email",
            message="Invalid email format",
            value="invalid",
            rule_type="pattern",
        )

        d = error.to_dict()
        assert d["field"] == "email"
        assert d["message"] == "Invalid email format"
        assert d["value"] == "invalid"
        assert d["rule_type"] == "pattern"


class TestValidateFunction:
    """Test cases for validate convenience function."""

    def test_validate_quick(self):
        """Test quick validate function."""
        rules = [
            {"field": "name", "rule_type": "required"},
            {"field": "age", "rule_type": "range", "min_value": 0, "max_value": 150},
        ]

        result = validate({"name": "John", "age": 25}, rules)
        assert result.is_valid is True

        result = validate({"name": "John", "age": -5}, rules)
        assert result.is_valid is False


class TestHotelValidator:
    """Test cases for HotelValidator."""

    def test_validate_hotel_data_valid(self):
        """Test validation with valid hotel data."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "name_en": "Test Hotel",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_hotel_data_missing_required(self):
        """Test validation with missing required fields."""
        validator = HotelValidator()

        data = {
            "name_en": "Test Hotel",
            # Missing name_cn, province, city, address_cn
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "name_cn" for e in result.errors)
        assert any(e.field == "province" for e in result.errors)
        assert any(e.field == "city" for e in result.errors)
        assert any(e.field == "address_cn" for e in result.errors)

    def test_validate_hotel_data_invalid_country(self):
        """Test validation with invalid country code."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "XX",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "country_code" for e in result.errors)

    def test_validate_hotel_data_invalid_brand(self):
        """Test validation with invalid brand."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "brand": "invalid_brand",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "brand" for e in result.errors)

    def test_validate_hotel_data_invalid_status(self):
        """Test validation with invalid status."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "status": "invalid_status",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "status" for e in result.errors)

    def test_validate_expedia_id_valid(self):
        """Test Expedia ID validation with valid ID."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "expedia_hotel_id": "EXP123456",  # Valid: 6-20 alphanumeric chars
        }

        result = validator.validate_expedia_id(data)

        assert result.is_valid is True

    def test_validate_expedia_id_invalid(self):
        """Test Expedia ID validation with invalid ID."""
        validator = HotelValidator()

        data = {
            "expedia_hotel_id": "abc",  # Too short (need 6-20 chars)
        }

        result = validator.validate_expedia_id(data)

        assert result.is_valid is False
        assert any(e.field == "expedia_hotel_id" for e in result.errors)

    def test_validate_email_valid(self):
        """Test email validation with valid email."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "email": "test@atour.com",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid email."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "email": "invalid-email",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "email" for e in result.errors)

    def test_validate_geolocation_valid(self):
        """Test geolocation validation with valid coordinates."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "latitude": 31.2304,
            "longitude": 121.4737,
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is True

    def test_validate_geolocation_invalid(self):
        """Test geolocation validation with invalid coordinates."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "latitude": 91,  # Invalid: must be -90 to 90
            "longitude": 121.4737,
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "latitude" for e in result.errors)

    def test_validate_geolocation_partial(self):
        """Test geolocation validation with only one coordinate."""
        validator = HotelValidator()

        data = {
            "name_cn": "测试酒店",
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
            "latitude": 31.2304,
            # longitude missing
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "geolocation" for e in result.errors)

    def test_validate_address(self):
        """Test address validation."""
        validator = HotelValidator()

        # Valid address
        data = {
            "address_cn": "浦东新区某路123号",
        }
        result = validator.validate_address(data)
        assert result.is_valid is True

        # Address too long
        data = {
            "address_cn": "x" * 600,
        }
        result = validator.validate_address(data)
        assert result.is_valid is False
        assert any(e.field == "address_cn" for e in result.errors)

    def test_validate_contact(self):
        """Test contact information validation."""
        validator = HotelValidator()

        # Valid contact
        data = {
            "email": "test@atour.com",
            "phone": "+86-21-12345678",
            "website": "https://www.atour.com",
        }
        result = validator.validate_contact(data)
        assert result.is_valid is True

    def test_validate_bulk(self):
        """Test bulk validation."""
        validator = HotelValidator()

        hotels = [
            {
                "name_cn": "酒店A",
                "province": "上海",
                "city": "上海",
                "address_cn": "某路",
                "country_code": "CN",
            },
            {
                "name_en": "Hotel B",
                # Missing required Chinese fields
            },
        ]

        results = validator.validate_bulk(hotels)

        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False


class TestHotelValidatorEdgeCases:
    """Edge case tests for HotelValidator."""

    def test_empty_data(self):
        """Test validation with empty data."""
        validator = HotelValidator()

        data = {}
        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_whitespace_only_fields(self):
        """Test validation with whitespace-only fields."""
        validator = HotelValidator()

        data = {
            "name_cn": "   ",  # Just whitespace
            "province": "上海市",
            "city": "上海",
            "address_cn": "浦东新区某路123号",
            "country_code": "CN",
        }

        result = validator.validate_hotel_data(data)

        assert result.is_valid is False
        assert any(e.field == "name_cn" for e in result.errors)

    def test_all_valid_brands(self):
        """Test all valid brand values."""
        validator = HotelValidator()

        for brand in ["atour", "atour_x", "zhotel", "ahaus"]:
            data = {
                "name_cn": "测试酒店",
                "province": "上海市",
                "city": "上海",
                "address_cn": "浦东新区某路123号",
                "country_code": "CN",
                "brand": brand,
            }
            result = validator.validate_hotel_data(data)
            assert result.is_valid is True

    def test_all_valid_statuses(self):
        """Test all valid status values."""
        validator = HotelValidator()

        for status in ["draft", "pending_review", "approved", "published", "suspended"]:
            data = {
                "name_cn": "测试酒店",
                "province": "上海市",
                "city": "上海",
                "address_cn": "浦东新区某路123号",
                "country_code": "CN",
                "status": status,
            }
            result = validator.validate_hotel_data(data)
            assert result.is_valid is True