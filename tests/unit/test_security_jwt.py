"""Unit tests for signed JWT creation, claim enforcement, and password hashing."""

from datetime import timedelta
import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    raw = "GoogleSeniorDev2026!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert ":" in hashed  # salt:key format
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_issuance_and_decoding():
    token = create_access_token(
        subject="usr-test-123",
        claims={"school_id": "sch-001", "role": "teacher"},
    )
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "usr-test-123"
    assert payload["school_id"] == "sch-001"
    assert payload["role"] == "teacher"
    assert payload["iss"] == "learningbridge-auth"
    assert payload["aud"] == "learningbridge-api"


def test_jwt_expired_token_rejected():
    expired_token = create_access_token(
        subject="usr-test-123",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    with pytest.raises(AuthenticationError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value.message).lower()
