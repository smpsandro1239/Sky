from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plain_text() -> None:
    password = "Correct-Horse-Battery-2026!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_is_valid_and_type_scoped() -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert decode_access_token(token + "tampered") is None


def test_access_token_rejects_wrong_token_type() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-123",
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    assert decode_access_token(token) is None


def test_access_token_rejects_expired_token() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-123",
            "type": "access",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    assert decode_access_token(token) is None


def test_access_token_rejects_missing_subject() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    assert decode_access_token(token) is None


def test_production_rejects_development_secret_even_when_long(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(
        settings,
        "secret_key",
        "dev-only-change-this-secret-key-rotate-before-production",
    )
    try:
        settings.validate_security()
    except RuntimeError as exc:
        assert "SKY_SECRET_KEY" in str(exc)
    else:
        raise AssertionError("A development secret must never be accepted in production")


def test_production_accepts_unique_secret_of_at_least_32_characters(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "secret_key", "production-secret-key-with-more-than-32-characters")
    settings.validate_security()
