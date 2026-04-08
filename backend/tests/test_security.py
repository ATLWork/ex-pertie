"""
Tests for security utilities.
"""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_password_hash(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Same password, different hashes (bcrypt generates random salt)
        assert hash1 != hash2


class TestJWTokens:
    """Tests for JWT token generation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        user_id = "test-user-id"
        expires = timedelta(hours=1)
        token = create_access_token(subject=user_id, expires_delta=expires)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token = create_refresh_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_token("invalid_token")
        assert payload is None

    def test_verify_access_token(self):
        """Test verifying access token."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="access")
        assert verified_user_id == user_id

    def test_verify_refresh_token(self):
        """Test verifying refresh token."""
        user_id = "test-user-id"
        token = create_refresh_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="refresh")
        assert verified_user_id == user_id

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type."""
        user_id = "test-user-id"
        access_token = create_access_token(subject=user_id)

        # Try to verify access token as refresh token
        verified = verify_token(access_token, token_type="refresh")
        assert verified is None

    def test_token_with_additional_claims(self):
        """Test token with additional claims."""
        user_id = "test-user-id"
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        token = create_access_token(
            subject=user_id,
            additional_claims=additional_claims,
        )

        payload = decode_token(token)
        assert payload is not None
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
