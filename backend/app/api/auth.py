
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    verify_password,
)
from app.db.session import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.execute(
        text("""
            SELECT id, password_hash
            FROM app_users
            WHERE LOWER(email) = LOWER(:email)
              AND is_active = TRUE
        """),
        {"email": credentials.email.strip()},
    ).mappings().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        valid_password = verify_password(
            credentials.password,
            user["password_hash"],
        )
    except (ValueError, Exception):
        valid_password = False

    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user["id"])

    return TokenResponse(access_token=token)


@router.get("/me")
def get_authenticated_user(
    current_user: dict = Depends(get_current_user),
):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
    }


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


@router.post("/change-password", status_code=200)
def change_own_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Troca de senha com verificação da anterior, sem devolvê-la ao cliente."""
    from app.core.security import hash_password
    try:
        saved = db.execute(
            text("SELECT password_hash FROM app_users WHERE id = :id FOR UPDATE"),
            {"id": current_user["id"]},
        ).scalar_one_or_none()
        if saved is None or not verify_password(payload.current_password.get_secret_value(), saved):
            raise HTTPException(status_code=401, detail="Senha atual incorreta")
        if payload.current_password == payload.new_password:
            raise HTTPException(status_code=422, detail="A nova senha deve ser diferente da atual")
        db.execute(
            text("UPDATE app_users SET password_hash = :hash WHERE id = :id"),
            {"hash": hash_password(payload.new_password.get_secret_value()), "id": current_user["id"]},
        )
        db.execute(
            text("""
                INSERT INTO user_audit_events (actor_id, target_user_id, action)
                VALUES (:id, :id, 'senha_alterada')
            """),
            {"id": current_user["id"]},
        )
        db.commit()
        return {"message": "Senha alterada. Faça login novamente."}
    except Exception:
        db.rollback()
        raise
