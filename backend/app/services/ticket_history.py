"""Serviço de auditoria das movimentações dos chamados."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def record_ticket_history(
    db: Session,
    *,
    ticket_id: int,
    actor_id: int,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None,
) -> None:
    """
    Registra uma movimentação de chamado.

    O commit deve ser realizado pelo endpoint responsável,
    garantindo que a alteração e seu histórico sejam
    confirmados na mesma transação.
    """

    db.execute(
        text("""
            INSERT INTO ticket_history (
                ticket_id,
                actor_id,
                action,
                old_value,
                new_value
            )
            VALUES (
                :ticket_id,
                :actor_id,
                :action,
                :old_value,
                :new_value
            )
        """),
        {
            "ticket_id": ticket_id,
            "actor_id": actor_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
        },
    )
