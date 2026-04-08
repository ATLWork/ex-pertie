"""
Validation Engine - Configurable data validation rule engine.

Provides a flexible validation system with the following rule types:
- required: Required field validation
- type: Type checking (string, int, float, bool, date, datetime)
- range: Numeric range validation
- length: String length validation
- pattern: Regular expression pattern matching
- enum: Enumeration value validation
- custom: Custom validation function

Example usage:
    engine = ValidationEngine()
    engine.add_rule("name", RuleType.REQUIRED)
    engine.add_rule("age", RuleType.TYPE, expected_type=int)
    engine.add_rule("score", RuleType.RANGE, min_value=0, max_value=100)
    result = engine.validate({"name": "John", "age": 25, "score": 85})
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class RuleType(str, Enum):
    """Supported validation rule types."""

    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    ENUM = "enum"
    CUSTOM = "custom"


class ValidationError:
    """
    Represents a validation error.

    Attributes:
        field: The field name that failed validation
        message: Human-readable error message
        value: The value that failed validation
        rule_type: The type of rule that failed
    """

    def __init__(
        self,
        field: str,
        message: str,
        value: Any = None,
        rule_type: Optional[str] = None,
    ) -> None:
        """
        Initialize a validation error.

        Args:
            field: Field name that failed validation
            message: Error message describing the failure
            value: The invalid value (optional)
            rule_type: Type of validation rule that failed (optional)
        """
        self.field = field
        self.message = message
        self.value = value
        self.rule_type = rule_type

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.

        Returns:
            Dictionary representation of the error
        """
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "rule_type": self.rule_type,
        }

    def __repr__(self) -> str:
        return f"ValidationError(field={self.field!r}, message={self.message!r})"


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors
        field_errors: Dictionary mapping field names to their errors
    """

    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    field_errors: Dict[str, List[ValidationError]] = field(default_factory=dict)

    def add_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        rule_type: Optional[str] = None,
    ) -> None:
        """
        Add a validation error.

        Args:
            field: Field name that failed validation
            message: Error message
            value: The invalid value
            rule_type: Type of rule that failed
        """
        error = ValidationError(field=field, message=message, value=value, rule_type=rule_type)
        self.errors.append(error)
        self.is_valid = False

        # Also track by field
        if field not in self.field_errors:
            self.field_errors[field] = []
        self.field_errors[field].append(error)

    def get_field_errors(self, field: str) -> List[ValidationError]:
        """
        Get all errors for a specific field.

        Args:
            field: Field name

        Returns:
            List of errors for the field
        """
        return self.field_errors.get(field, [])

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation of the validation result
        """
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "errors": [e.to_dict() for e in self.errors],
            "field_errors": {f: [e.to_dict() for e in es] for f, es in self.field_errors.items()},
        }

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, error_count={len(self.errors)})"


@dataclass
class ValidationRule:
    """
    A validation rule definition.

    Attributes:
        field: Field name to validate
        rule_type: Type of validation rule
        message: Custom error message (optional)
        expected_type: For TYPE rule - the expected type
        min_value: For RANGE/LENGTH rules - minimum value/length
        max_value: For RANGE/LENGTH rules - maximum value/length
        pattern: For PATTERN rule - regular expression pattern
        enum_values: For ENUM rule - allowed values
        custom_func: For CUSTOM rule - validation function
    """

    field: str
    rule_type: RuleType
    message: Optional[str] = None
    # Type validation
    expected_type: Optional[type] = None
    # Range validation
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    # Pattern validation
    pattern: Optional[str] = None
    # Enum validation
    enum_values: Optional[List[Any]] = None
    # Custom validation
    custom_func: Optional[Callable[[Any], bool]] = None
    # Severity level: "error" (default) or "warning"
    severity: str = "error"

    def __post_init__(self) -> None:
        """Validate rule configuration after initialization."""
        if self.rule_type == RuleType.TYPE and self.expected_type is None:
            raise ValueError(f"Rule for field '{self.field}' requires expected_type")
        if self.rule_type == RuleType.PATTERN and self.pattern is None:
            raise ValueError(f"Rule for field '{self.field}' requires pattern")
        if self.rule_type == RuleType.ENUM and self.enum_values is None:
            raise ValueError(f"Rule for field '{self.field}' requires enum_values")
        if self.rule_type == RuleType.CUSTOM and self.custom_func is None:
            raise ValueError(f"Rule for field '{self.field}' requires custom_func")

    def get_error_message(self, default_message: str) -> str:
        """
        Get error message, using custom message if provided.

        Args:
            default_message: Default error message

        Returns:
            Error message to use
        """
        return self.message if self.message else default_message


class ValidationEngine:
    """
    Configurable validation rule engine.

    Supports the following rule types:
    - required: Field must be present and not empty
    - type: Field value must be of the specified type
    - range: Numeric value must be within specified range
    - length: String length must be within specified range
    - pattern: String must match the regular expression pattern
    - enum: Value must be one of the specified enum values
    - custom: Value must pass the custom validation function

    Example:
        engine = ValidationEngine()
        engine.add_rule("name", RuleType.REQUIRED)
        engine.add_rule("age", RuleType.TYPE, expected_type=int)
        engine.add_rule("email", RuleType.PATTERN, pattern=r"^[\\w.-]+@[\\w.-]+\\.\\w+$")

        result = engine.validate({"name": "John", "age": "25", "email": "john@example.com"})
    """

    # Supported type mappings
    TYPE_MAPPING = {
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "bool": bool,
        "boolean": bool,
        "date": datetime,
        "datetime": datetime,
    }

    def __init__(self) -> None:
        """Initialize the validation engine."""
        self.rules: List[ValidationRule] = []

    def add_rule(
        self,
        field: str,
        rule_type: Union[RuleType, str],
        **kwargs,
    ) -> "ValidationEngine":
        """
        Add a validation rule.

        Args:
            field: Field name to validate
            rule_type: Type of validation rule
            **kwargs: Additional rule parameters

        Returns:
            Self for method chaining

        Raises:
            ValueError: If rule configuration is invalid
        """
        if isinstance(rule_type, str):
            rule_type = RuleType(rule_type)

        # Process type mapping if needed
        if rule_type == RuleType.TYPE and "expected_type" in kwargs:
            expected = kwargs["expected_type"]
            if isinstance(expected, str):
                kwargs["expected_type"] = self.TYPE_MAPPING.get(expected, expected)

        rule = ValidationRule(field=field, rule_type=rule_type, **kwargs)
        self.rules.append(rule)
        return self

    def add_rules(self, rules: List[ValidationRule]) -> "ValidationEngine":
        """
        Add multiple validation rules at once.

        Args:
            rules: List of validation rules

        Returns:
            Self for method chaining
        """
        self.rules.extend(rules)
        return self

    def clear_rules(self) -> None:
        """Clear all validation rules."""
        self.rules.clear()

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against all configured rules.

        Args:
            data: Dictionary of data to validate

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True)

        for rule in self.rules:
            self._validate_rule(data, rule, result)

        return result

    def _validate_rule(
        self, data: Dict[str, Any], rule: ValidationRule, result: ValidationResult
    ) -> None:
        """
        Validate a single rule against the data.

        Args:
            data: Data dictionary
            rule: Validation rule to apply
            result: Validation result to update
        """
        value = data.get(rule.field)
        rule_type = rule.rule_type

        try:
            if rule_type == RuleType.REQUIRED:
                self._validate_required(value, rule, result)
            elif rule_type == RuleType.TYPE:
                self._validate_type(value, rule, result)
            elif rule_type == RuleType.RANGE:
                self._validate_range(value, rule, result)
            elif rule_type == RuleType.LENGTH:
                self._validate_length(value, rule, result)
            elif rule_type == RuleType.PATTERN:
                self._validate_pattern(value, rule, result)
            elif rule_type == RuleType.ENUM:
                self._validate_enum(value, rule, result)
            elif rule_type == RuleType.CUSTOM:
                self._validate_custom(value, rule, result)
        except Exception as e:
            # Catch unexpected errors during validation
            result.add_error(
                rule.field,
                f"Validation error: {str(e)}",
                value=value,
                rule_type=rule_type.value,
            )

    def _validate_required(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a field is required and not empty."""
        is_empty = value is None or (isinstance(value, str) and not value.strip())

        if is_empty:
            result.add_error(
                rule.field,
                rule.get_error_message(f"Field '{rule.field}' is required"),
                value=value,
                rule_type=RuleType.REQUIRED.value,
            )

    def _validate_type(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a field is of the expected type."""
        if value is None:
            # Skip type validation for None values (use required rule for that)
            return

        expected_type = rule.expected_type

        # Handle type checking
        if expected_type == bool:
            # Special handling for boolean - check for common boolean representations
            if isinstance(value, bool):
                return
            if isinstance(value, str) and value.lower() in ("true", "false", "1", "0", "yes", "no"):
                return
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be a boolean (true/false)"
                ),
                value=value,
                rule_type=RuleType.TYPE.value,
            )
        elif expected_type == int:
            # Handle numeric types
            if isinstance(value, int) and not isinstance(value, bool):
                return
            # Try to convert string to int
            if isinstance(value, str):
                try:
                    int(value)
                    return
                except ValueError:
                    pass
            result.add_error(
                rule.field,
                rule.get_error_message(f"Field '{rule.field}' must be an integer"),
                value=value,
                rule_type=RuleType.TYPE.value,
            )
        elif expected_type == float:
            # Handle float type - accept both int and float
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return
            # Try to convert string to float
            if isinstance(value, str):
                try:
                    float(value)
                    return
                except ValueError:
                    pass
            result.add_error(
                rule.field,
                rule.get_error_message(f"Field '{rule.field}' must be a number"),
                value=value,
                rule_type=RuleType.TYPE.value,
            )
        elif expected_type == datetime:
            # Handle datetime type - check if value is a datetime or parseable string
            if isinstance(value, datetime):
                return
            if isinstance(value, str):
                # Try common datetime formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%d",
                ]
                for fmt in formats:
                    try:
                        datetime.strptime(value, fmt)
                        return
                    except ValueError:
                        continue
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be a valid datetime"
                ),
                value=value,
                rule_type=RuleType.TYPE.value,
            )
        else:
            # General type checking
            if not isinstance(value, expected_type):
                type_name = expected_type.__name__
                result.add_error(
                    rule.field,
                    rule.get_error_message(f"Field '{rule.field}' must be of type {type_name}"),
                    value=value,
                    rule_type=RuleType.TYPE.value,
                )

    def _validate_range(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a numeric value is within range."""
        if value is None:
            return

        # Try to convert to number
        try:
            num_value = float(value) if rule.min_value is not None or rule.max_value is not None else None
        except (TypeError, ValueError):
            result.add_error(
                rule.field,
                rule.get_error_message(f"Field '{rule.field}' must be a number for range validation"),
                value=value,
                rule_type=RuleType.RANGE.value,
            )
            return

        if num_value is None:
            return

        # Check minimum
        if rule.min_value is not None and num_value < rule.min_value:
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be at least {rule.min_value}"
                ),
                value=value,
                rule_type=RuleType.RANGE.value,
            )

        # Check maximum
        if rule.max_value is not None and num_value > rule.max_value:
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be at most {rule.max_value}"
                ),
                value=value,
                rule_type=RuleType.RANGE.value,
            )

    def _validate_length(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a string length is within range."""
        if value is None:
            return

        if not isinstance(value, str):
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be a string for length validation"
                ),
                value=value,
                rule_type=RuleType.LENGTH.value,
            )
            return

        length = len(value)

        # Check minimum
        if rule.min_value is not None and length < rule.min_value:
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be at least {rule.min_value} characters"
                ),
                value=value,
                rule_type=RuleType.LENGTH.value,
            )

        # Check maximum
        if rule.max_value is not None and length > rule.max_value:
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be at most {rule.max_value} characters"
                ),
                value=value,
                rule_type=RuleType.LENGTH.value,
            )

    def _validate_pattern(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a string matches a regular expression pattern."""
        if value is None:
            return

        if not isinstance(value, str):
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be a string for pattern validation"
                ),
                value=value,
                rule_type=RuleType.PATTERN.value,
            )
            return

        if rule.pattern is None:
            return

        try:
            if not re.match(rule.pattern, value):
                result.add_error(
                    rule.field,
                    rule.get_error_message(
                        f"Field '{rule.field}' does not match the required pattern"
                    ),
                    value=value,
                    rule_type=RuleType.PATTERN.value,
                )
        except re.error as e:
            result.add_error(
                rule.field,
                f"Invalid regex pattern: {e}",
                value=rule.pattern,
                rule_type=RuleType.PATTERN.value,
            )

    def _validate_enum(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate that a value is one of the allowed enum values."""
        if value is None:
            return

        if rule.enum_values is None:
            return

        if value not in rule.enum_values:
            allowed = ", ".join(str(v) for v in rule.enum_values)
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' must be one of: {allowed}"
                ),
                value=value,
                rule_type=RuleType.ENUM.value,
            )

    def _validate_custom(
        self, value: Any, rule: ValidationRule, result: ValidationResult
    ) -> None:
        """Validate using a custom validation function."""
        if rule.custom_func is None:
            return

        try:
            is_valid = rule.custom_func(value)
            if not is_valid:
                result.add_error(
                    rule.field,
                    rule.get_error_message(f"Field '{rule.field}' failed custom validation"),
                    value=value,
                    rule_type=RuleType.CUSTOM.value,
                )
        except Exception as e:
            result.add_error(
                rule.field,
                rule.get_error_message(
                    f"Field '{rule.field}' custom validation error: {str(e)}"
                ),
                value=value,
                rule_type=RuleType.CUSTOM.value,
            )

    def validate_field(self, field: str, value: Any) -> ValidationResult:
        """
        Validate a single field value against its rules.

        Args:
            field: Field name
            value: Field value

        Returns:
            ValidationResult for the field
        """
        result = ValidationResult(is_valid=True)
        data = {field: value}

        for rule in self.rules:
            if rule.field == field:
                self._validate_rule(data, rule, result)

        return result

    @classmethod
    def from_dict(cls, rules_config: List[Dict[str, Any]]) -> "ValidationEngine":
        """
        Create a ValidationEngine from a list of rule configurations.

        Args:
            rules_config: List of rule configuration dictionaries

        Returns:
            Configured ValidationEngine instance

        Example:
            config = [
                {"field": "name", "rule_type": "required"},
                {"field": "age", "rule_type": "type", "expected_type": "int"},
                {"field": "email", "rule_type": "pattern", "pattern": r"^[\\w.-]+@[\\w.-]+\\.\\w+$"}
            ]
            engine = ValidationEngine.from_dict(config)
        """
        engine = cls()
        for rule_config in rules_config:
            field = rule_config.pop("field")
            rule_type = rule_config.pop("rule_type")
            engine.add_rule(field, rule_type, **rule_config)
        return engine


# Convenience function for quick validation
def validate(
    data: Dict[str, Any],
    rules: List[Dict[str, Any]],
) -> ValidationResult:
    """
    Validate data with rules defined as dictionaries.

    Args:
        data: Data dictionary to validate
        rules: List of rule configurations

    Returns:
        ValidationResult with validation status and errors

    Example:
        rules = [
            {"field": "name", "rule_type": "required"},
            {"field": "age", "rule_type": "range", "min_value": 0, "max_value": 150}
        ]
        result = validate({"name": "John", "age": 25}, rules)
    """
    engine = ValidationEngine.from_dict(rules)
    return engine.validate(data)
