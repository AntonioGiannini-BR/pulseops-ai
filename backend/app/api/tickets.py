from app.api.deps import get_current_user, require_roles
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ticket_history import record_ticket_history

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
                assignee_id,
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
                assignee_id,
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

        record_ticket_history(
            db,
            ticket_id=new_ticket["id"],
            actor_id=current_user["id"],
            action="criacao",
            old_value=None,
            new_value=new_ticket["status"],
        )

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
    model_config = ConfigDict(extra="forbid")

    priority: Literal[
        "baixa",
        "media",
        "alta",
        "critica",
    ]


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

    previous_priority = db.execute(
        text("""
            SELECT priority
            FROM tickets
            WHERE id = :ticket_id
            FOR UPDATE
        """),
        {"ticket_id": ticket_id},
    ).scalar_one_or_none()

    if previous_priority is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    result = db.execute(
        text("""
            UPDATE tickets
            SET
                priority = :priority,
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
            "priority": changes["priority"],
        },
    )

    updated_ticket = result.mappings().first()

    if updated_ticket is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    if previous_priority != updated_ticket["priority"]:
        record_ticket_history(
            db,
            ticket_id=ticket_id,
            actor_id=current_user["id"],
            action="mudanca_prioridade",
            old_value=previous_priority,
            new_value=updated_ticket["priority"],
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

    previous_assignee = db.execute(
        text("""
            SELECT assignee_id
            FROM tickets
            WHERE id = :ticket_id
            FOR UPDATE
        """),
        {"ticket_id": ticket_id},
    ).mappings().first()

    if previous_assignee is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
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

    old_assignee_id = previous_assignee["assignee_id"]
    new_assignee_id = updated_ticket["assignee_id"]

    if old_assignee_id != new_assignee_id:
        record_ticket_history(
            db,
            ticket_id=ticket_id,
            actor_id=current_user["id"],
            action="atribuicao",
            old_value=(
                str(old_assignee_id)
                if old_assignee_id is not None
                else None
            ),
            new_value=str(new_assignee_id),
        )

    db.commit()
    return dict(updated_ticket)


# Ciclo de vida dos chamados

class TicketStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "aberto",
        "em_triagem",
        "em_atendimento",
        "resolvido",
        "fechado",
    ]


ALLOWED_STATUS_TRANSITIONS = {
    "aberto": "em_triagem",
    "em_triagem": "em_atendimento",
    "em_atendimento": "resolvido",
    "resolvido": "fechado",
    "fechado": None,
}


@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "analista")),
):
    """Atualiza o status respeitando o ciclo de vida do chamado."""

    result = db.execute(
        text("""
            SELECT
                id,
                status,
                resolved_at,
                closed_at
            FROM tickets
            WHERE id = :ticket_id
            FOR UPDATE
        """),
        {"ticket_id": ticket_id},
    )

    ticket = result.mappings().first()

    if ticket is None:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    current_status = ticket["status"]
    new_status = payload.status

    expected_status = ALLOWED_STATUS_TRANSITIONS.get(current_status)

    if new_status != expected_status:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Transição inválida: "
                f"{current_status} -> {new_status}"
            ),
        )

    result = db.execute(
        text("""
            UPDATE tickets
            SET
                status = CAST(:new_status AS VARCHAR),
                resolved_at = CASE
                    WHEN CAST(:new_status AS VARCHAR) = 'resolvido'
                    THEN NOW()
                    ELSE resolved_at
                END,
                closed_at = CASE
                    WHEN CAST(:new_status AS VARCHAR) = 'fechado'
                    THEN NOW()
                    ELSE closed_at
                END,
                updated_at = NOW()
            WHERE id = :ticket_id
            RETURNING
                id,
                title,
                status,
                priority,
                requester_id,
                assignee_id,
                opened_at,
                resolved_at,
                closed_at,
                updated_at
        """),
        {
            "ticket_id": ticket_id,
            "new_status": new_status,
        },
    )

    updated_ticket = dict(result.mappings().one())

    record_ticket_history(
        db,
        ticket_id=ticket_id,
        actor_id=current_user["id"],
        action="mudanca_status",
        old_value=current_status,
        new_value=new_status,
    )

    db.commit()

    return updated_ticket


@router.get("/{ticket_id}/history")
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Consulta o histórico de um chamado respeitando as permissões."""

    ticket = db.execute(
        text("""
            SELECT id
            FROM tickets
            WHERE id = :ticket_id
              AND (:is_staff OR requester_id = :user_id)
        """),
        {
            "ticket_id": ticket_id,
            "is_staff": current_user["role"] in ("admin", "analista"),
            "user_id": current_user["id"],
        },
    ).scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado",
        )

    result = db.execute(
        text("""
            SELECT
                id,
                ticket_id,
                actor_id,
                action,
                old_value,
                new_value,
                details,
                created_at
            FROM ticket_history
            WHERE ticket_id = :ticket_id
            ORDER BY created_at ASC, id ASC
        """),
        {"ticket_id": ticket_id},
    )

    return [dict(row) for row in result.mappings().all()]
