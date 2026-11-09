from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Gera um hash seguro para armazenar no banco."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica uma senha sem armazenar seu valor original."""
    return password_hasher.verify(password, hashed_password)



from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

def create_access_token(user_id: int) -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY não configurada")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> int:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY não configurada")
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
        if payload.get("type") != "access":
            raise ValueError("Tipo de token inválido")
        user_id = int(payload["sub"])
        if user_id <= 0:
            raise ValueError("ID inválido")
        return user_id
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise ValueError("Token inválido ou expirado") from exc
