from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_plain_text() -> None:
    password = "Correct-Horse-Battery-2026!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_is_valid_and_type_scoped() -> None:
    token = create_access_token("user-123")
    assert decode_access_token(token)["sub"] == "user-123"
    assert decode_access_token(token + "tampered") is None
