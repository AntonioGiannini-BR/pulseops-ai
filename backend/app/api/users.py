"""Administração de contas com RBAC, validação e auditoria no PostgreSQL.

Não há cadastro público: administradores criam somente analistas/solicitantes.
Nenhuma senha ou hash é devolvido pela API ou persistido na auditoria.
"""
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db


router = APIRouter(prefix="/users", tags=["User Management"])
admin_only = require_roles("admin")

USER_FIELDS = """
    id, full_name, email, role, department_id, is_active, created_at
"""


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["analista", "solicitante"]
    department_id: int | None = Field(default=None, gt=0)

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = " ".join(value.split())
        if len(name) < 2:
            raise ValueError("Informe um nome válido")
        return name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Informe um e-mail válido")
        return normalized


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


def _audit(db: Session, *, actor_id: int, target_id: int, action: str) -> None:
    db.execute(
        text("""
            INSERT INTO user_audit_events (actor_id, target_user_id, action)
            VALUES (:actor_id, :target_id, :action)
        """),
        {"actor_id": actor_id, "target_id": target_id, "action": action},
    )


@router.get("/")
def list_users(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: dict = Depends(admin_only),
):
    """Lista apenas o que o administrador precisa, sem credenciais."""
    rows = db.execute(
        text(f"""
            SELECT {USER_FIELDS}
            FROM app_users
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
        """),
        {"limit": limit, "offset": offset},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_only),
):
    """Cria usuário ativo com senha hash e auditoria na mesma transação."""
    if payload.department_id is not None:
        department = db.execute(
            text("SELECT 1 FROM departments WHERE id = :department_id"),
            {"department_id": payload.department_id},
        ).scalar_one_or_none()
        if department is None:
            raise HTTPException(status_code=422, detail="Departamento não encontrado")
    try:
        row = db.execute(
            text(f"""
                INSERT INTO app_users (
                    full_name, email, password_hash, role,
                    department_id, is_active
                )
                VALUES (
                    :name, :email, :password_hash, :role,
                    :department_id, TRUE
                )
                RETURNING {USER_FIELDS}
            """),
            {
                "name": payload.full_name,
                "email": payload.email,
                "password_hash": hash_password(payload.password),
                "role": payload.role,
                "department_id": payload.department_id,
            },
        ).mappings().one()
        _audit(
            db, actor_id=current_user["id"], target_id=row["id"], action="conta_criada"
        )
        db.commit()
        return dict(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="E-mail já utilizado ou dados inválidos",
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_only),
):
    """Bloqueia contas sem excluir histórico, preservando administradores."""
    try:
        row = db.execute(
            text(f"SELECT {USER_FIELDS} FROM app_users WHERE id = :id FOR UPDATE"),
            {"id": user_id},
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        if row["role"] == "admin" or row["id"] == current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Contas administrativas não podem ser alteradas por esta rota",
            )
        if row["is_active"] == payload.is_active:
            db.rollback()
            return dict(row)
        updated = db.execute(
            text(f"""
                UPDATE app_users SET is_active = :is_active
                WHERE id = :id RETURNING {USER_FIELDS}
            """),
            {"id": user_id, "is_active": payload.is_active},
        ).mappings().one()
        _audit(
            db,
            actor_id=current_user["id"],
            target_id=user_id,
            action="conta_reativada" if payload.is_active else "conta_desativada",
        )
        db.commit()
        return dict(updated)
    except Exception:
        db.rollback()
        raise


@router.get("/audit")
def recent_user_audit(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(admin_only),
):
    """Últimos eventos administrativos, sem senhas ou detalhes sensíveis."""
    rows = db.execute(text("""
        SELECT e.id, e.actor_id, e.target_user_id, e.action, e.created_at,
               a.email AS actor_email, t.email AS target_email
        FROM user_audit_events e
        LEFT JOIN app_users a ON a.id = e.actor_id
        LEFT JOIN app_users t ON t.id = e.target_user_id
        ORDER BY e.id DESC
        LIMIT 50
    """)).mappings().all()
    return [dict(row) for row in rows]
