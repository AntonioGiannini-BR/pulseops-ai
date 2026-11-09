"""Visões agregadas para Equipes e Central de IA, sem expor dados privados."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db

router = APIRouter(tags=["Operations"], dependencies=[Depends(require_roles("admin", "analista"))])


@router.get("/teams/summary")
def teams_summary(db: Session = Depends(get_db)):
    """Contagens agregadas por departamento. Sem nomes/e-mails de colaboradores."""
    rows = db.execute(text("""
        SELECT d.id, d.name,
               COALESCE(u.active_users, 0) AS active_users,
               COALESCE(u.analysts, 0) AS analysts,
               COALESCE(t.tickets_total, 0) AS tickets_total,
               COALESCE(t.tickets_open, 0) AS tickets_open
        FROM departments d
        LEFT JOIN (
            SELECT department_id,
                   COUNT(*) FILTER (WHERE is_active = TRUE) AS active_users,
                   COUNT(*) FILTER (WHERE is_active = TRUE AND role = 'analista') AS analysts
            FROM app_users
            GROUP BY department_id
        ) u ON u.department_id = d.id
        LEFT JOIN (
            SELECT department_id, COUNT(*) AS tickets_total,
                   COUNT(*) FILTER (WHERE status NOT IN ('resolvido','fechado')) AS tickets_open
            FROM tickets
            GROUP BY department_id
        ) t ON t.department_id = d.id
        ORDER BY d.name
    """)).mappings().all()
    return [dict(row) for row in rows]


@router.get("/ai/overview")
def ai_overview(db: Session = Depends(get_db)):
    """Métricas globais dos resultados de triagem, sem conteúdo dos chamados."""
    row = db.execute(text("""
        SELECT COUNT(*) AS suggestions_total,
               COUNT(*) FILTER (WHERE review_status = 'pendente') AS pending,
               COUNT(*) FILTER (WHERE review_status = 'aprovada') AS approved,
               COUNT(*) FILTER (WHERE review_status = 'rejeitada') AS rejected,
               COUNT(*) FILTER (WHERE model_name LIKE 'ollama/%') AS ollama,
               COUNT(*) FILTER (WHERE model_name LIKE 'demo-%') AS demonstration,
               COUNT(*) FILTER (
                   WHERE model_name NOT LIKE 'ollama/%'
                     AND model_name NOT LIKE 'demo-%'
                     AND model_name IS NOT NULL
               ) AS external_models
        FROM ai_suggestions
    """)).mappings().one()
    return dict(row)
