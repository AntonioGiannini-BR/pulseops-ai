from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Comments"],
)


class TicketCommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False


def check_ticket_access(
    db: Session,
    ticket_id: int,
    current_user: dict,
) -> None:
    """Verifica se o usuário pode acessar o chamado."""

    is_staff = current_user["role"] in ("admin", "analista")

    ticket = db.execute(
        text("""
            SELECT id
            FROM tickets
            WHERE id = :ticket_id
              AND (:is_staff OR requester_id = :user_id)
        """),
        {
            "ticket_id": ticket_id,
            "is_staff": is_staff,
            "user_id": current_user["id"],
        },
    ).scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )


@router.post("/{ticket_id}/comments", status_code=201)
def create_ticket_comment(
    ticket_id: int,
    payload: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Adiciona um comentário público ou interno a um chamado."""

    check_ticket_access(db, ticket_id, current_user)

    is_staff = current_user["role"] in ("admin", "analista")

    if payload.is_internal and not is_staff:
        raise HTTPException(
            status_code=403,
            detail="Você não pode criar comentários internos",
        )

    body = payload.body.strip()

    if not body:
        raise HTTPException(
            status_code=422,
            detail="O comentário não pode estar vazio",
        )

    try:
        result = db.execute(
            text("""
                INSERT INTO ticket_comments (
                    ticket_id,
                    author_id,
                    body,
                    is_internal
                )
                VALUES (
                    :ticket_id,
                    :author_id,
                    :body,
                    :is_internal
                )
                RETURNING
                    id,
                    ticket_id,
                    author_id,
                    body,
                    is_internal,
                    created_at
            """),
            {
                "ticket_id": ticket_id,
                "author_id": current_user["id"],
                "body": body,
                "is_internal": payload.is_internal,
            },
        )

        comment = dict(result.mappings().one())

        db.commit()

        return comment

    except Exception:
        db.rollback()
        raise


@router.get("/{ticket_id}/comments")
def list_ticket_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista comentários respeitando a visibilidade de cada perfil."""

    check_ticket_access(db, ticket_id, current_user)

    is_staff = current_user["role"] in ("admin", "analista")

    result = db.execute(
        text("""
            SELECT
                id,
                ticket_id,
                author_id,
                body,
                is_internal,
                created_at
            FROM ticket_comments
            WHERE ticket_id = :ticket_id
              AND (:is_staff OR is_internal = FALSE)
            ORDER BY created_at ASC, id ASC
        """),
        {
            "ticket_id": ticket_id,
            "is_staff": is_staff,
        },
    )

    return [dict(row) for row in result.mappings().all()]
