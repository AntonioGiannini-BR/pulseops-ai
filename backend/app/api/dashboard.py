from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("admin", "analista")
    ),
):
    """
    Retorna os indicadores gerais do PulseOps AI.

    Acesso permitido:
    - Administradores
    - Analistas
    """

    result = db.execute(
        text("""
            SELECT
                total_chamados,
                chamados_pendentes,
                chamados_concluidos,
                chamados_fora_sla,
                horas_medias_resolucao
            FROM v_dashboard_kpis
        """)
    )

    summary = result.mappings().one()

    return {
        "total_chamados": summary["total_chamados"],
        "chamados_pendentes": summary["chamados_pendentes"],
        "chamados_concluidos": summary["chamados_concluidos"],
        "chamados_fora_sla": summary["chamados_fora_sla"],
        "horas_medias_resolucao": (
            float(summary["horas_medias_resolucao"])
            if summary["horas_medias_resolucao"] is not None
            else None
        ),
    }
@router.get("/distribution")
def get_dashboard_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("admin", "analista")
    ),
):
    """
    Retorna a distribuição dos chamados
    por status e prioridade.
    """

    status_result = db.execute(
        text("""
            SELECT status, COUNT(*) AS total
            FROM tickets
            GROUP BY status
        """)
    ).mappings().all()

    priority_result = db.execute(
        text("""
            SELECT priority, COUNT(*) AS total
            FROM tickets
            GROUP BY priority
        """)
    ).mappings().all()

    por_status = {
        "aberto": 0,
        "em_triagem": 0,
        "em_atendimento": 0,
        "resolvido": 0,
        "fechado": 0,
    }

    por_prioridade = {
        "baixa": 0,
        "media": 0,
        "alta": 0,
        "critica": 0,
    }

    for row in status_result:
        por_status[row["status"]] = row["total"]

    for row in priority_result:
        por_prioridade[row["priority"]] = row["total"]

    return {
        "por_status": por_status,
        "por_prioridade": por_prioridade,
    }