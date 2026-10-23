
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticação necessária ou token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise error

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError:
        raise error

    user = db.execute(
        text("""
            SELECT id, email, role
            FROM app_users
            WHERE id = :user_id
              AND is_active = TRUE
        """),
        {"user_id": user_id},
    ).mappings().first()

    if user is None:
        raise error

    return dict(user)
