"""Testes de integração para prazos e indicadores de SLA.

Requer PostgreSQL de desenvolvimento com categorias e políticas de SLA.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app


client = TestClient(app)


@pytest.fixture
def admin_de_teste():
    """Cria um administrador temporário, sem tocar em contas existentes."""
    with engine.begin() as connection:
        category_id = connection.execute(
            text("SELECT id FROM categories ORDER BY id LIMIT 1")
        ).scalar_one()
        admin_id = connection.execute(
            text("""
                INSERT INTO app_users (full_name, email, password_hash, role)
                VALUES (:name, :email, :password_hash, 'admin')
                RETURNING id
            """),
            {
                "name": "Admin Teste SLA",
                "email": f"sla-{uuid.uuid4().hex}@pulseops.example",
                "password_hash": hash_password("SenhaTemporariaTeste123!"),
            },
        ).scalar_one()

    try:
        yield {
            "admin_id": admin_id,
            "category_id": category_id,
            "headers": {
                "Authorization": f"Bearer {create_access_token(admin_id)}"
            },
        }
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM tickets WHERE requester_id = :id"),
                {"id": admin_id},
            )
            connection.execute(
                text("DELETE FROM app_users WHERE id = :id"),
                {"id": admin_id},
            )


def criar_chamado(contexto, prioridade):
    return client.post(
        "/tickets/",
        headers=contexto["headers"],
        json={
            "title": "Teste automático de SLA",
            "description": "Validação de cálculo de vencimento.",
            "requester_id": contexto["admin_id"],
            "category_id": contexto["category_id"],
            "priority": prioridade,
        },
    )


@pytest.mark.parametrize("prioridade", ["baixa", "media", "alta", "critica"])
def test_criacao_calcula_prazo_da_politica(admin_de_teste, prioridade):
    response = criar_chamado(admin_de_teste, prioridade)
    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["due_at"] is not None

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    EXTRACT(EPOCH FROM (t.due_at - t.opened_at)) / 60 AS minutos,
                    p.resolution_minutes AS esperado
                FROM tickets t
                JOIN sla_policies p ON p.priority = t.priority
                WHERE t.id = :id
            """),
            {"id": ticket["id"]},
        ).mappings().one()

    assert float(result["minutos"]) == pytest.approx(result["esperado"])

    detail = client.get(
        f"/tickets/{ticket['id']}",
        headers=admin_de_teste["headers"],
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["due_at"] == ticket["due_at"]
    assert detail.json()["sla_status"] == "em_dia"


def test_troca_prioridade_recalcula_prazo(admin_de_teste):
    created = criar_chamado(admin_de_teste, "baixa")
    assert created.status_code == 201, created.text
    ticket = created.json()

    updated = client.patch(
        f"/tickets/{ticket['id']}",
        headers=admin_de_teste["headers"],
        json={"priority": "critica"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["due_at"] != ticket["due_at"]

    with engine.connect() as connection:
        saved = connection.execute(
            text("""
                SELECT
                    t.priority,
                    EXTRACT(EPOCH FROM (t.due_at - t.opened_at)) / 60 AS minutos,
                    p.resolution_minutes AS esperado
                FROM tickets t
                JOIN sla_policies p ON p.priority = t.priority
                WHERE t.id = :id
            """),
            {"id": ticket["id"]},
        ).mappings().one()

    assert saved["priority"] == "critica"
    assert float(saved["minutos"]) == pytest.approx(saved["esperado"])

    detail = client.get(
        f"/tickets/{ticket['id']}",
        headers=admin_de_teste["headers"],
    )
    assert detail.status_code == 200
    assert detail.json()["due_at"] == updated.json()["due_at"]


def test_dashboard_retorna_percentual_sla(admin_de_teste):
    response = client.get(
        "/dashboard/summary",
        headers=admin_de_teste["headers"],
    )
    assert response.status_code == 200, response.text
    percentual = response.json()["cumprimento_sla_pct"]
    assert percentual is None or 0 <= percentual <= 100
