"""Assistente de resolução e automações permitidas com aprovação humana.

Nenhuma saída de LLM é usada como comando. O backend define as ações possíveis
e seus parâmetros; o usuário deve confirmar uma ação específica e o estado atual.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.services.ai_triage import InvalidProviderResponse, ProviderUnavailable
from app.services.resolution_guide import generate_resolution_guide
from app.services.ticket_history import record_ticket_history

router = APIRouter(prefix="/tickets", tags=["Resolution Assistant"])
staff_only = require_roles("admin", "analista")

Status = Literal["aberto", "em_triagem", "em_atendimento", "resolvido", "fechado"]
ActionId = Literal["diagnose_platform", "send_guidance", "advance_workflow"]


class AutomationApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approved: Literal[True]
    expected_status: Status


def _ticket(db: Session, ticket_id: int, *, lock: bool = False) -> dict:
    sql = """
        SELECT t.id, t.title, t.description, t.status, t.category_id,
               c.name AS category_name
        FROM tickets t
        JOIN categories c ON c.id = t.category_id
        WHERE t.id = :ticket_id
    """
    if lock:
        sql += " FOR UPDATE OF t"
    result = db.execute(text(sql), {"ticket_id": ticket_id}).mappings().first()
    if result is None:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return dict(result)


def _guidance_text(category_name: str) -> str:
    category = category_name.casefold().strip()
    if category == "acessos":
        instructions = (
            "1. Confirme se está usando a conta corporativa correta.\n"
            "2. Encerre a sessão e entre novamente pelo endereço oficial.\n"
            "3. Se o erro continuar, informe o horário e a mensagem exibida para verificarmos suas permissões."
        )
    elif category == "infraestrutura":
        instructions = (
            "1. Verifique se outros serviços de rede funcionam normalmente.\n"
            "2. Registre o horário da falha e se outras pessoas foram afetadas.\n"
            "3. Informe ao suporte se a falha persiste; não altere configurações de rede sem orientação."
        )
    elif category == "equipamentos":
        instructions = (
            "1. Confirme as conexões externas e se o equipamento está ligado.\n"
            "2. Anote mensagens de erro ou sinais apresentados.\n"
            "3. Informe o modelo do equipamento e quando a falha começou."
        )
    else:
        instructions = (
            "1. Registre a mensagem de erro e o horário aproximado.\n"
            "2. Verifique se a falha ocorre novamente após iniciar uma nova sessão.\n"
            "3. Informe ao suporte o impacto e quais operações estão indisponíveis."
        )
    return (
        "Olá! Recebemos seu chamado. Para ajudar no diagnóstico, siga estas orientações seguras:\n"
        f"{instructions}\n"
        "Não compartilhe senhas, códigos de autenticação ou dados sensíveis neste chamado. "
        "O atendimento permanece em andamento."
    )


def _catalog(ticket: dict, already_sent: bool) -> list[dict]:
    active = ticket["status"] not in ("resolvido", "fechado")
    next_status = {
        "aberto": "em_triagem",
        "em_triagem": "em_atendimento",
    }.get(ticket["status"])
    return [
        {
            "id": "diagnose_platform",
            "label": "Verificar saúde da plataforma",
            "description": "Consulta a conexão do PulseOps AI com o PostgreSQL. Não verifica o sistema externo citado no chamado.",
            "preview": "Executar SELECT 1 no banco do PulseOps AI e registrar o resultado na auditoria.",
            "available": active,
            "reason": None if active else "Chamado concluído",
        },
        {
            "id": "send_guidance",
            "label": "Enviar orientações ao solicitante",
            "description": "Publica um comentário com instruções padronizadas, sem executar comandos externos.",
            "preview": _guidance_text(ticket["category_name"]),
            "available": active and not already_sent,
            "reason": "Chamado concluído" if not active else (
                "Orientações já enviadas por esta automação" if already_sent else None
            ),
        },
        {
            "id": "advance_workflow",
            "label": "Avançar etapa de atendimento",
            "description": "Atualiza o status dentro do fluxo permitido; nunca marca como resolvido automaticamente.",
            "preview": (
                f"Alterar status de {ticket['status']} para {next_status}."
                if next_status else "Nenhuma transição automática segura disponível."
            ),
            "available": next_status is not None,
            "reason": None if next_status else "Não é possível avançar automaticamente nesta etapa",
        },
    ]


def _already_sent(db: Session, ticket_id: int) -> bool:
    return db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM ticket_history
                WHERE ticket_id = :ticket_id AND action = 'automacao_orientacao'
            )
        """),
        {"ticket_id": ticket_id},
    ).scalar_one()


@router.get("/{ticket_id}/resolution-automations")
def list_resolution_automations(
    ticket_id: int,
    db: Session = Depends(get_db),
    _current_user: dict = Depends(staff_only),
):
    ticket = _ticket(db, ticket_id)
    return {
        "ticket_id": ticket_id,
        "expected_status": ticket["status"],
        "actions": _catalog(ticket, _already_sent(db, ticket_id)),
    }


@router.post("/{ticket_id}/resolution-guide")
def suggest_resolution_guide(
    ticket_id: int,
    db: Session = Depends(get_db),
    _current_user: dict = Depends(staff_only),
):
    ticket = _ticket(db, ticket_id)
    if ticket["status"] in ("resolvido", "fechado"):
        raise HTTPException(status_code=409, detail="Chamado já concluído")

    # A consulta à IA não segura conexão/transação do PostgreSQL.
    db.rollback()
    try:
        result = generate_resolution_guide(
            title=ticket["title"],
            description=ticket["description"],
            category=ticket["category_name"],
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InvalidProviderResponse as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result


@router.post("/{ticket_id}/resolution-automations/{action_id}/execute")
def execute_resolution_automation(
    ticket_id: int,
    action_id: ActionId,
    approval: AutomationApproval,
    db: Session = Depends(get_db),
    current_user: dict = Depends(staff_only),
):
    """Somente ações fechadas e aprovadas, em transação com auditoria."""
    try:
        ticket = _ticket(db, ticket_id, lock=True)
        if ticket["status"] != approval.expected_status:
            raise HTTPException(
                status_code=409,
                detail="O status do chamado mudou. Atualize a prévia antes de aprovar.",
            )
        actions = {item["id"]: item for item in _catalog(ticket, _already_sent(db, ticket_id))}
        action = actions[action_id]
        if not action["available"]:
            raise HTTPException(status_code=409, detail=action["reason"] or "Ação indisponível")

        result = {
            "action_id": action_id,
            "ticket_status": ticket["status"],
            "message": "",
            "comment": None,
            "diagnostic": None,
        }

        if action_id == "diagnose_platform":
            # Apenas diagnóstico do próprio banco; nenhuma rede arbitrária.
            db.execute(text("SELECT 1")).scalar_one()
            record_ticket_history(
                db, ticket_id=ticket_id, actor_id=current_user["id"],
                action="automacao_diagnostico", new_value="postgresql_ok",
            )
            result["diagnostic"] = {"api": "ok", "database": "connected"}
            result["message"] = "Diagnóstico do PulseOps AI concluído; não comprova o estado do sistema externo."

        elif action_id == "send_guidance":
            body = _guidance_text(ticket["category_name"])
            comment = db.execute(
                text("""
                    INSERT INTO ticket_comments (ticket_id, author_id, body, is_internal)
                    VALUES (:ticket_id, :author_id, :body, FALSE)
                    RETURNING id, ticket_id, author_id, body, is_internal, created_at
                """),
                {"ticket_id": ticket_id, "author_id": current_user["id"], "body": body},
            ).mappings().one()
            record_ticket_history(
                db, ticket_id=ticket_id, actor_id=current_user["id"],
                action="automacao_orientacao", new_value=str(comment["id"]),
            )
            result["comment"] = dict(comment)
            result["message"] = "Orientações padronizadas publicadas no chamado."

        elif action_id == "advance_workflow":
            next_status = {"aberto": "em_triagem", "em_triagem": "em_atendimento"}[ticket["status"]]
            db.execute(
                text("""
                    UPDATE tickets SET status = :new_status, updated_at = NOW()
                    WHERE id = :ticket_id
                """),
                {"new_status": next_status, "ticket_id": ticket_id},
            )
            record_ticket_history(
                db, ticket_id=ticket_id, actor_id=current_user["id"],
                action="mudanca_status", old_value=ticket["status"], new_value=next_status,
            )
            record_ticket_history(
                db, ticket_id=ticket_id, actor_id=current_user["id"],
                action="automacao_fluxo", old_value=ticket["status"], new_value=next_status,
            )
            result["ticket_status"] = next_status
            result["message"] = f"Etapa atualizada para {next_status}."

        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
