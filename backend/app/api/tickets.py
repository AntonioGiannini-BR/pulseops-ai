from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["Tickets"])
class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1)
    requester_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    priority: Literal["baixa", "media", "alta", "critica"] = "media"

@router.get("/")
def list_tickets(db: Session = Depends(get_db)):
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
            ORDER BY id
        """)
    )

    return [dict(row) for row in result.mappings().all()]

@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
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
        """),
        {"ticket_id": ticket_id}
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

    db: Session = Depends(get_db)

):

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
