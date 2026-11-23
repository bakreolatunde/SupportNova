from auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token(subject="user-123", role="agent")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["role"] == "agent"


def test_invalid_token_returns_none():
    assert decode_access_token("not-a-real-token") is None
