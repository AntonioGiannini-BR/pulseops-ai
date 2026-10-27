from app.api.deps import get_current_user, require_roles
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["Tickets"], dependencies=[Depends(get_current_user)])
class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1)
    requester_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    priority: Literal["baixa", "media", "alta", "critica"] = "media"

@router.get("/")
def list_tickets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = db.execute(
        text("""
            SELECT
                id,
                title,
                description,
                priority,
                status,
                requester_id,
                category_id,
                opened_at
            FROM tickets
            WHERE (:is_staff OR requester_id = :user_id)
            ORDER BY id
        """),
        {
            "is_staff": current_user["role"] in ("admin", "analista"),
            "user_id": current_user["id"],
        },
    )

    return [dict(row) for row in result.mappings().all()]

@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = db.execute(
        text("""
            SELECT
                id,
                title,
                description,
                priority,
                status,
                requester_id,
                category_id,
                opened_at
            FROM tickets
            WHERE id = :ticket_id
              AND (:is_staff OR requester_id = :user_id)
        """),
        {
            "ticket_id": ticket_id,
            "is_staff": current_user["role"] in ("admin", "analista"),
            "user_id": current_user["id"],
        }
    )

    ticket = result.mappings().first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado"
        )

    return dict(ticket)

@router.post("/", status_code=201)

def create_ticket(

    ticket: TicketCreate,

    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)

):

    if current_user["role"] not in ("admin", "analista", "solicitante"):
        raise HTTPException(
            status_code=403,
            detail="Perfil sem permissão para criar chamados",
        )

    if (
        current_user["role"] == "solicitante"
        and ticket.requester_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não pode criar chamados em nome de outro usuário",
        )

    if not ticket.title.strip() or not ticket.description.strip():

        raise HTTPException(

            status_code=422,

            detail="Título e descrição não podem estar vazios"

        )

    try:

        result = db.execute(

            text("""

                INSERT INTO tickets (

                    title,

                    description,

                    requester_id,

                    category_id,

                    priority

                )

                VALUES (

                    :title,

                    :description,

                    :requester_id,

                    :category_id,

                    :priority

                )

                RETURNING

                    id,

                    title,

                    description,

                    requester_id,

                    category_id,

                    priority,

                    status,

                    opened_at

            """),

            {

                "title": ticket.title.strip(),

                "description": ticket.description.strip(),

                "requester_id": ticket.requester_id,

                "category_id": ticket.category_id,

                "priority": ticket.priority

            }

        )

        new_ticket = dict(result.mappings().one())

        db.commit()

        return new_ticket

    except IntegrityError:

        db.rollback()

        raise HTTPException(

            status_code=400,

            detail="Dados inválidos ou usuário/categoria inexistente"

        )

# PATCH - Atualizar status e prioridade de um chamado

class TicketUpdate(BaseModel):
    status: Literal[
        "aberto",
        "em_triagem",
        "em_atendimento",
        "resolvido",
        "fechado",
    ] | None = None

    priority: Literal[
        "baixa",
        "media",
        "alta",
        "critica",
    ] | None = None


@router.patch("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    ticket: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "analista")),
):
    changes = ticket.model_dump(exclude_unset=True)

    if not changes or any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=422,
            detail="Informe status ou prioridade com um valor válido",
        )

    result = db.execute(
        text("""
            UPDATE tickets
            SET
                status = COALESCE(:status, status),
                priority = COALESCE(:priority, priority),
                updated_at = NOW()
            WHERE id = :ticket_id
            RETURNING
                id,
                title,
                description,
                status,
                priority,
                requester_id,
                category_id,
                opened_at,
                updated_at
        """),
        {
            "ticket_id": ticket_id,
            "status": changes.get("status"),
            "priority": changes.get("priority"),
        },
    )

    updated_ticket = result.mappings().first()

    if updated_ticket is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    db.commit()
    return dict(updated_ticket)


class TicketAssignment(BaseModel):
    assignee_id: int = Field(gt=0)


@router.patch("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    """Atribui ou reatribui um ticket a um analista ativo."""

    analyst = db.execute(
        text("""
            SELECT id
            FROM app_users
            WHERE id = :user_id
              AND role = 'analista'
              AND is_active = TRUE
        """),
        {"user_id": assignment.assignee_id},
    ).scalar_one_or_none()

    if analyst is None:
        raise HTTPException(
            status_code=422,
            detail="Analista inexistente, inativo ou sem permissão",
        )

    result = db.execute(
        text("""
            UPDATE tickets
            SET
                assignee_id = :assignee_id,
                updated_at = NOW()
            WHERE id = :ticket_id
            RETURNING
                id,
                title,
                status,
                priority,
                requester_id,
                assignee_id,
                updated_at
        """),
        {
            "ticket_id": ticket_id,
            "assignee_id": assignment.assignee_id,
        },
    )

    updated_ticket = result.mappings().first()

    if updated_ticket is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    db.commit()
    return dict(updated_ticket)
