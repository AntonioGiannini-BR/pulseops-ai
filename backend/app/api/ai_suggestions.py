"""Sugestões de triagem com revisão humana e auditoria transacional."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.services.ai_triage import (
    InvalidProviderResponse,
    ProviderUnavailable,
    generate_proposal,
)
from app.services.ticket_history import record_ticket_history


router = APIRouter(prefix="/tickets", tags=["AI Triage"])
staff_only = require_roles("admin", "analista")


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["aprovada", "rejeitada"]


def _ticket_for_triage(db: Session, ticket_id: int, *, lock: bool = False):
    sql = """
        SELECT id, title, description, category_id, priority, status
        FROM tickets
        WHERE id = :ticket_id
    """
    if lock:
        sql += " FOR UPDATE"
    ticket = db.execute(text(sql), {"ticket_id": ticket_id}).mappings().first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return ticket


def _suggestions(db: Session, ticket_id: int):
    rows = db.execute(
        text("""
            SELECT id, ticket_id, suggested_category_id, suggested_priority,
                   summary, rationale, model_name, review_status,
                   reviewed_by_id, reviewed_at, created_at
            FROM ai_suggestions
            WHERE ticket_id = :ticket_id
            ORDER BY created_at DESC, id DESC
        """),
        {"ticket_id": ticket_id},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.get("/{ticket_id}/ai-suggestions")
def list_ai_suggestions(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(staff_only),
):
    """Somente analistas e administradores podem ver sugestões."""
    _ticket_for_triage(db, ticket_id)
    return _suggestions(db, ticket_id)


@router.post("/{ticket_id}/ai-suggestions", status_code=201)
def create_ai_suggestion(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(staff_only),
):
    """Solicita triagem. Não modifica prioridade/categoria do chamado."""
    ticket = _ticket_for_triage(db, ticket_id)
    if ticket["status"] in ("resolvido", "fechado"):
        raise HTTPException(status_code=409, detail="Chamado já concluído")

    pending = db.execute(
        text("""
            SELECT id FROM ai_suggestions
            WHERE ticket_id = :ticket_id AND review_status = 'pendente'
            LIMIT 1
        """),
        {"ticket_id": ticket_id},
    ).scalar_one_or_none()
    if pending is not None:
        raise HTTPException(
            status_code=409,
            detail="Revise a sugestão pendente antes de gerar outra",
        )

    categories = [
        dict(row)
        for row in db.execute(
            text("SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY id")
        ).mappings().all()
    ]
    if not categories:
        raise HTTPException(status_code=422, detail="Nenhuma categoria ativa")

    # Libera a transação/conexão antes de chamar o serviço externo.
    db.rollback()
    try:
        generated = generate_proposal(
            title=ticket["title"],
            description=ticket["description"],
            current_category_id=ticket["category_id"],
            categories=categories,
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InvalidProviderResponse as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    allowed_ids = {category["id"] for category in categories}
    if generated.proposal.suggested_category_id not in allowed_ids:
        raise HTTPException(status_code=502, detail="Categoria sugerida inválida")

    try:
        # O lock no chamado serializa geração e revisão concorrentes.
        current_ticket = _ticket_for_triage(db, ticket_id, lock=True)
        if current_ticket["status"] in ("resolvido", "fechado"):
            raise HTTPException(status_code=409, detail="Chamado já concluído")

        pending = db.execute(
            text("""
                SELECT id FROM ai_suggestions
                WHERE ticket_id = :ticket_id AND review_status = 'pendente'
                LIMIT 1
            """),
            {"ticket_id": ticket_id},
        ).scalar_one_or_none()
        if pending is not None:
            raise HTTPException(
                status_code=409,
                detail="Já existe uma sugestão pendente",
            )

        # Evita gravar uma categoria que foi desativada durante a chamada.
        active = db.execute(
            text("SELECT id FROM categories WHERE id = :id AND is_active = TRUE"),
            {"id": generated.proposal.suggested_category_id},
        ).scalar_one_or_none()
        if active is None:
            raise HTTPException(status_code=409, detail="Categoria sugerida foi desativada")

        result = db.execute(
            text("""
                INSERT INTO ai_suggestions (
                    ticket_id, suggested_category_id, suggested_priority,
                    summary, rationale, model_name
                ) VALUES (
                    :ticket_id, :category_id, :priority,
                    :summary, :rationale, :model_name
                )
                RETURNING id
            """),
            {
                "ticket_id": ticket_id,
                "category_id": generated.proposal.suggested_category_id,
                "priority": generated.proposal.suggested_priority,
                "summary": generated.proposal.summary,
                "rationale": generated.proposal.rationale,
                "model_name": generated.model_name,
            },
        )
        suggestion_id = result.scalar_one()
        record_ticket_history(
            db,
            ticket_id=ticket_id,
            actor_id=current_user["id"],
            action="ai_sugestao_criada",
            new_value=str(suggestion_id),
        )
        suggestion = db.execute(
            text("""
                SELECT id, ticket_id, suggested_category_id, suggested_priority,
                       summary, rationale, model_name, review_status,
                       reviewed_by_id, reviewed_at, created_at
                FROM ai_suggestions WHERE id = :id
            """),
            {"id": suggestion_id},
        ).mappings().one()
        db.commit()
        return dict(suggestion)
    except Exception:
        db.rollback()
        raise


@router.post("/{ticket_id}/ai-suggestions/{suggestion_id}/review")
def review_ai_suggestion(
    ticket_id: int,
    suggestion_id: int,
    payload: ReviewDecision,
    db: Session = Depends(get_db),
    current_user: dict = Depends(staff_only),
):
    """Somente a aprovação humana pode aplicar prioridade/categoria."""
    try:
        ticket = _ticket_for_triage(db, ticket_id, lock=True)
        suggestion = db.execute(
            text("""
                SELECT id, ticket_id, suggested_category_id,
                       suggested_priority, review_status
                FROM ai_suggestions
                WHERE id = :id AND ticket_id = :ticket_id
                FOR UPDATE
            """),
            {"id": suggestion_id, "ticket_id": ticket_id},
        ).mappings().first()
        if suggestion is None:
            raise HTTPException(status_code=404, detail="Sugestão não encontrada")
        if suggestion["review_status"] != "pendente":
            raise HTTPException(status_code=409, detail="Sugestão já revisada")

        if payload.decision == "aprovada":
            if ticket["status"] in ("resolvido", "fechado"):
                raise HTTPException(
                    status_code=409,
                    detail="Não é possível aplicar sugestões em chamados concluídos",
                )

            new_priority = suggestion["suggested_priority"] or ticket["priority"]
            new_category = suggestion["suggested_category_id"] or ticket["category_id"]

            if new_category != ticket["category_id"]:
                active = db.execute(
                    text("SELECT id FROM categories WHERE id = :id AND is_active = TRUE"),
                    {"id": new_category},
                ).scalar_one_or_none()
                if active is None:
                    raise HTTPException(status_code=409, detail="Categoria sugerida não está ativa")

            result = db.execute(
                text("""
                    UPDATE tickets AS t
                    SET priority = p.priority,
                        category_id = :category_id,
                        due_at = CASE
                            WHEN t.priority <> p.priority
                            THEN t.opened_at + p.resolution_minutes * INTERVAL '1 minute'
                            ELSE t.due_at
                        END,
                        updated_at = NOW()
                    FROM sla_policies AS p
                    WHERE t.id = :ticket_id AND p.priority = :priority
                    RETURNING t.id, t.priority, t.category_id, t.due_at
                """),
                {
                    "ticket_id": ticket_id,
                    "priority": new_priority,
                    "category_id": new_category,
                },
            ).mappings().first()
            if result is None:
                raise HTTPException(status_code=422, detail="Política de SLA não configurada")

            if ticket["priority"] != new_priority:
                record_ticket_history(
                    db,
                    ticket_id=ticket_id,
                    actor_id=current_user["id"],
                    action="mudanca_prioridade",
                    old_value=ticket["priority"],
                    new_value=new_priority,
                )
            if ticket["category_id"] != new_category:
                record_ticket_history(
                    db,
                    ticket_id=ticket_id,
                    actor_id=current_user["id"],
                    action="mudanca_categoria",
                    old_value=str(ticket["category_id"]),
                    new_value=str(new_category),
                )
            updated_ticket = dict(result)
        else:
            updated_ticket = db.execute(
                text("""
                    SELECT id, priority, category_id, due_at
                    FROM tickets WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id},
            ).mappings().one()
            updated_ticket = dict(updated_ticket)

        reviewed = db.execute(
            text("""
                UPDATE ai_suggestions
                SET review_status = :decision,
                    reviewed_by_id = :user_id,
                    reviewed_at = NOW()
                WHERE id = :id AND review_status = 'pendente'
                RETURNING id, ticket_id, suggested_category_id,
                          suggested_priority, summary, rationale, model_name,
                          review_status, reviewed_by_id, reviewed_at, created_at
            """),
            {
                "decision": payload.decision,
                "user_id": current_user["id"],
                "id": suggestion_id,
            },
        ).mappings().one()
        record_ticket_history(
            db,
            ticket_id=ticket_id,
            actor_id=current_user["id"],
            action=f"ai_sugestao_{payload.decision}",
            old_value="pendente",
            new_value=str(suggestion_id),
        )
        db.commit()
        return {"suggestion": dict(reviewed), "ticket": updated_ticket}
    except Exception:
        db.rollback()
        raise
