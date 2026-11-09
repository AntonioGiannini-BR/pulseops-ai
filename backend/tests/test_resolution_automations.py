"""Integração: aprovação, autorização, auditoria e ações idempotentes."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app

client = TestClient(app)


@pytest.fixture
def context():
    users = []
    ticket_id = None
    try:
        with engine.begin() as conn:
            category_id = conn.execute(
                text("SELECT id FROM categories WHERE LOWER(name) = 'acessos' LIMIT 1")
            ).scalar_one_or_none()
            if category_id is None:
                category_id = conn.execute(text("SELECT id FROM categories ORDER BY id LIMIT 1")).scalar_one()
            for role in ("admin", "analista", "solicitante"):
                user_id = conn.execute(
                    text("""
                        INSERT INTO app_users (full_name, email, password_hash, role)
                        VALUES ('Teste Automação', :email, :password, :role)
                        RETURNING id
                    """),
                    {
                        "email": f"automation-{uuid.uuid4().hex}@pulseops.example",
                        "password": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()
                users.append(user_id)
            ticket_id = conn.execute(
                text("""
                    INSERT INTO tickets (title, description, requester_id, category_id)
                    VALUES ('Portal com erro', 'Permissão negada', :requester, :category)
                    RETURNING id
                """),
                {"requester": users[2], "category": category_id},
            ).scalar_one()
        yield {
            "id": ticket_id,
            "admin": {"Authorization": f"Bearer {create_access_token(users[0])}"},
            "analyst": {"Authorization": f"Bearer {create_access_token(users[1])}"},
            "requester": {"Authorization": f"Bearer {create_access_token(users[2])}"},
        }
    finally:
        with engine.begin() as conn:
            if ticket_id is not None:
                conn.execute(text("DELETE FROM tickets WHERE id = :id"), {"id": ticket_id})
            for user_id in reversed(users):
                conn.execute(text("DELETE FROM app_users WHERE id = :id"), {"id": user_id})


def url(ctx):
    return f"/tickets/{ctx['id']}/resolution-automations"


def execute(ctx, action, headers, status="aberto", approved=True):
    return client.post(
        f"{url(ctx)}/{action}/execute",
        headers=headers,
        json={"approved": approved, "expected_status": status},
    )


def test_catalogo_exige_permissao_e_mostra_previa(context):
    assert client.get(url(context)).status_code == 401
    assert client.get(url(context), headers=context["requester"]).status_code == 403
    response = client.get(url(context), headers=context["analyst"])
    assert response.status_code == 200
    data = response.json()
    assert data["expected_status"] == "aberto"
    assert {action["id"] for action in data["actions"]} == {
        "diagnose_platform", "send_guidance", "advance_workflow"
    }
    assert "Não compartilhe senhas" in next(
        item["preview"] for item in data["actions"] if item["id"] == "send_guidance"
    )


def test_acao_sem_aprovacao_nao_altera_dados(context):
    assert execute(context, "send_guidance", context["admin"], approved=False).status_code == 422
    assert execute(context, "send_guidance", context["requester"]).status_code == 403
    assert execute(context, "nao_permitida", context["admin"]).status_code == 422
    with engine.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM ticket_comments WHERE ticket_id=:id"),
            {"id": context["id"]},
        ).scalar_one() == 0


def test_envio_de_orientacoes_uma_vez_com_auditoria(context):
    response = execute(context, "send_guidance", context["analyst"])
    assert response.status_code == 200, response.text
    comment = response.json()["comment"]
    assert comment["is_internal"] is False
    assert "senha" in comment["body"].lower()
    assert execute(context, "send_guidance", context["analyst"]).status_code == 409
    public = client.get(
        f"/tickets/{context['id']}/comments", headers=context["requester"]
    )
    assert public.status_code == 200
    assert len(public.json()) == 1
    history = client.get(
        f"/tickets/{context['id']}/history", headers=context["admin"]
    ).json()
    assert [item["action"] for item in history] == ["automacao_orientacao"]
    assert history[0]["new_value"] == str(comment["id"])


def test_avanco_de_fluxo_nao_resolve_chamado(context):
    first = execute(context, "advance_workflow", context["admin"])
    assert first.status_code == 200, first.text
    assert first.json()["ticket_status"] == "em_triagem"
    assert execute(context, "advance_workflow", context["admin"]).status_code == 409
    second = execute(context, "advance_workflow", context["analyst"], status="em_triagem")
    assert second.status_code == 200, second.text
    assert second.json()["ticket_status"] == "em_atendimento"
    assert execute(context, "advance_workflow", context["admin"], status="em_atendimento").status_code == 409
    history = client.get(
        f"/tickets/{context['id']}/history", headers=context["admin"]
    ).json()
    assert [item["action"] for item in history] == [
        "mudanca_status", "automacao_fluxo", "mudanca_status", "automacao_fluxo"
    ]
    with engine.connect() as conn:
        ticket = conn.execute(
            text("SELECT status, resolved_at FROM tickets WHERE id=:id"),
            {"id": context["id"]},
        ).mappings().one()
    assert ticket["status"] == "em_atendimento"
    assert ticket["resolved_at"] is None


def test_diagnostico_apenas_do_banco_e_auditoria(context):
    response = execute(context, "diagnose_platform", context["admin"])
    assert response.status_code == 200, response.text
    assert response.json()["diagnostic"] == {"api": "ok", "database": "connected"}
    assert "não comprova" in response.json()["message"]
    history = client.get(
        f"/tickets/{context['id']}/history", headers=context["admin"]
    ).json()
    assert history[0]["action"] == "automacao_diagnostico"


def test_guia_exige_permissao_e_nao_modifica_chamado(context, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")
    endpoint = f"/tickets/{context['id']}/resolution-guide"
    assert client.post(endpoint).status_code == 401
    assert client.post(endpoint, headers=context["requester"]).status_code == 403
    result = client.post(endpoint, headers=context["analyst"])
    assert result.status_code == 200, result.text
    assert result.json()["model_name"] == "demo-guia-local"
    assert len(result.json()["guide"]["steps"]) >= 2
    with engine.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM ticket_history WHERE ticket_id=:id"),
            {"id": context["id"]},
        ).scalar_one() == 0

def test_chamado_concluido_nao_recebe_automacoes(context):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE tickets
                SET status='resolvido', resolved_at=NOW()
                WHERE id=:id
            """),
            {"id": context["id"]},
        )
    catalog = client.get(url(context), headers=context["admin"])
    assert catalog.status_code == 200
    assert all(not item["available"] for item in catalog.json()["actions"])
    for action in ("diagnose_platform", "send_guidance", "advance_workflow"):
        response = execute(context, action, context["admin"], status="resolvido")
        assert response.status_code == 409, response.text
    with engine.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM ticket_history WHERE ticket_id=:id"),
            {"id": context["id"]},
        ).scalar_one() == 0


def test_erro_na_auditoria_desfaz_publicacao(context, monkeypatch):
    def audit_unavailable(*args, **kwargs):
        raise RuntimeError("Falha na auditoria")

    monkeypatch.setattr(
        "app.api.resolution_assistant.record_ticket_history", audit_unavailable
    )
    with pytest.raises(RuntimeError, match="Falha na auditoria"):
        execute(context, "send_guidance", context["admin"])
    with engine.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM ticket_comments WHERE ticket_id=:id"),
            {"id": context["id"]},
        ).scalar_one() == 0
