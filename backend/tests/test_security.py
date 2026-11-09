from app.core.security import hash_password, verify_password


def test_password_hash():
    password = "SenhaForte123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2")


def test_correct_password():
    hashed = hash_password("SenhaForte123!")

    assert verify_password("SenhaForte123!", hashed) is True


def test_incorrect_password():
    hashed = hash_password("SenhaForte123!")

    assert verify_password("SenhaErrada123!", hashed) is False

from app.core.security import create_access_token, decode_access_token

def test_create_and_decode_token():
    token = create_access_token(1)
    assert decode_access_token(token) == 1


def test_invalid_token():
    import pytest
    with pytest.raises(ValueError):
        decode_access_token("token.invalido.aqui")


def test_expired_token():
    import jwt
    import pytest
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(ValueError):
        decode_access_token(token)
