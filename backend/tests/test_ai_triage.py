"""Integração da triagem supervisionada (PostgreSQL de teste)."""

import uuid

import pytest
from pydantic import SecretStr
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.services.ai_triage import (
    GeneratedProposal,
    ProviderUnavailable,
    TriageProposal,
)

client = TestClient(app)


@pytest.fixture
def context():
    user_ids = []
    ticket_id = None
    try:
        with engine.begin() as conn:
            category_ids = conn.execute(
                text("SELECT id FROM categories WHERE is_active = TRUE ORDER BY id LIMIT 2")
            ).scalars().all()
            assert len(category_ids) >= 2
            users = {}
            for role in ("admin", "analista", "solicitante", "solicitante"):
                user_id = conn.execute(
                    text("""
                        INSERT INTO app_users (full_name, email, password_hash, role)
                        VALUES (:name, :email, :password, :role)
                        RETURNING id
                    """),
                    {
                        "name": "Teste IA",
                        "email": f"ai-{uuid.uuid4().hex}@pulseops.example",
                        "password": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()
                user_ids.append(user_id)
                users[f"{role}-{len(user_ids)}"] = user_id
            ticket_id = conn.execute(
                text("""
                    INSERT INTO tickets (
                        title, description, requester_id, category_id,
                        priority, due_at
                    ) VALUES (
                        'Impressora indisponível',
                        'Impressora do escritório parou de funcionar',
                        :requester, :category, 'baixa',
                        NOW() + INTERVAL '72 hours'
                    )
                    RETURNING id
                """),
                {"requester": user_ids[2], "category": category_ids[0]},
            ).scalar_one()

        yield {
            "ticket_id": ticket_id,
            "categories": category_ids,
            "admin_id": user_ids[0],
            "analyst_id": user_ids[1],
            "requester_id": user_ids[2],
            "outsider_id": user_ids[3],
            "admin": {"Authorization": f"Bearer {create_access_token(user_ids[0])}"},
            "analyst": {"Authorization": f"Bearer {create_access_token(user_ids[1])}"},
            "requester": {"Authorization": f"Bearer {create_access_token(user_ids[2])}"},
            "outsider": {"Authorization": f"Bearer {create_access_token(user_ids[3])}"},
        }
    finally:
        with engine.begin() as conn:
            if ticket_id is not None:
                conn.execute(text("DELETE FROM tickets WHERE id = :id"), {"id": ticket_id})
            for user_id in reversed(user_ids):
                conn.execute(text("DELETE FROM app_users WHERE id = :id"), {"id": user_id})


def url(ctx):
    return f"/tickets/{ctx['ticket_id']}/ai-suggestions"


def read_ticket(ctx):
    with engine.connect() as conn:
        return dict(conn.execute(
            text("SELECT priority, category_id, due_at FROM tickets WHERE id = :id"),
            {"id": ctx["ticket_id"]},
        ).mappings().one())


def propose_critical(ctx, monkeypatch):
    def fake(**kwargs):
        return GeneratedProposal(
            proposal=TriageProposal(
                suggested_priority="critica",
                suggested_category_id=ctx["categories"][1],
                summary="Atendimento requer avaliação.",
                rationale="Falha bloqueia operação.",
            ),
            model_name="teste-modelo",
        )
    monkeypatch.setattr("app.api.ai_suggestions.generate_proposal", fake)


def test_criacao_pendente_sem_alterar_chamado(context):
    before = read_ticket(context)
    response = client.post(url(context), headers=context["admin"])
    assert response.status_code == 201, response.text
    suggestion = response.json()
    assert suggestion["review_status"] == "pendente"
    assert suggestion["reviewed_by_id"] is None
    assert suggestion["model_name"] == "demo-regras-locais"
    assert read_ticket(context) == before

    result = client.get(url(context), headers=context["analyst"])
    assert result.status_code == 200
    assert [item["id"] for item in result.json()] == [suggestion["id"]]

    history = client.get(
        f"/tickets/{context['ticket_id']}/history",
        headers=context["admin"],
    ).json()
    assert history[-1]["action"] == "ai_sugestao_criada"

    duplicate = client.post(url(context), headers=context["admin"])
    assert duplicate.status_code == 409


def test_aprovacao_altera_categoria_prioridade_sla_e_historico(context, monkeypatch):
    propose_critical(context, monkeypatch)
    response = client.post(url(context), headers=context["analyst"])
    assert response.status_code == 201, response.text
    suggestion_id = response.json()["id"]

    review = client.post(
        f"{url(context)}/{suggestion_id}/review",
        headers=context["admin"],
        json={"decision": "aprovada"},
    )
    assert review.status_code == 200, review.text
    body = review.json()
    assert body["suggestion"]["review_status"] == "aprovada"
    assert body["suggestion"]["reviewed_by_id"] == context["admin_id"]
    assert body["ticket"]["priority"] == "critica"
    assert body["ticket"]["category_id"] == context["categories"][1]

    with engine.connect() as conn:
        sla = conn.execute(
            text("""
                SELECT EXTRACT(EPOCH FROM (t.due_at - t.opened_at))/60 AS minutes,
                       p.resolution_minutes AS expected
                FROM tickets t JOIN sla_policies p ON p.priority = t.priority
                WHERE t.id = :id
            """),
            {"id": context["ticket_id"]},
        ).mappings().one()
    assert float(sla["minutes"]) == pytest.approx(sla["expected"])

    history = client.get(
        f"/tickets/{context['ticket_id']}/history",
        headers=context["analyst"],
    ).json()
    assert [item["action"] for item in history] == [
        "ai_sugestao_criada",
        "mudanca_prioridade",
        "mudanca_categoria",
        "ai_sugestao_aprovada",
    ]
    again = client.post(
        f"{url(context)}/{suggestion_id}/review",
        headers=context["admin"],
        json={"decision": "aprovada"},
    )
    assert again.status_code == 409


def test_rejeicao_nao_aplica_e_permite_nova_sugestao(context, monkeypatch):
    propose_critical(context, monkeypatch)
    before = read_ticket(context)
    created = client.post(url(context), headers=context["admin"])
    suggestion_id = created.json()["id"]

    response = client.post(
        f"{url(context)}/{suggestion_id}/review",
        headers=context["analyst"],
        json={"decision": "rejeitada"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["suggestion"]["reviewed_by_id"] == context["analyst_id"]
    assert read_ticket(context) == before
    assert client.post(url(context), headers=context["admin"]).status_code == 201


def test_permissoes_e_chamado_concluido(context):
    assert client.post(url(context)).status_code == 401
    assert client.post(url(context), headers=context["requester"]).status_code == 403
    assert client.get(url(context), headers=context["requester"]).status_code == 403
    assert client.get(url(context), headers=context["outsider"]).status_code == 403
    assert client.post(
        f"{url(context)}/999999999/review",
        headers=context["admin"],
        json={"decision": "aprovada"},
    ).status_code == 404
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE tickets
                SET status = 'resolvido', resolved_at = NOW()
                WHERE id = :id
            """),
            {"id": context["ticket_id"]},
        )
    assert client.post(url(context), headers=context["admin"]).status_code == 409


def test_erro_provedor_nao_persiste_sugestao(context, monkeypatch):
    def broken(**kwargs):
        raise ProviderUnavailable("Provedor temporariamente indisponível")
    monkeypatch.setattr("app.api.ai_suggestions.generate_proposal", broken)
    response = client.post(url(context), headers=context["admin"])
    assert response.status_code == 503
    assert client.get(url(context), headers=context["admin"]).json() == []


def test_rollback_se_auditoria_falhar(context, monkeypatch):
    propose_critical(context, monkeypatch)
    created = client.post(url(context), headers=context["admin"])
    suggestion_id = created.json()["id"]
    before = read_ticket(context)

    def broken_history(*args, **kwargs):
        raise RuntimeError("Auditoria indisponível")

    monkeypatch.setattr("app.api.ai_suggestions.record_ticket_history", broken_history)
    with pytest.raises(RuntimeError, match="Auditoria indisponível"):
        client.post(
            f"{url(context)}/{suggestion_id}/review",
            headers=context["admin"],
            json={"decision": "aprovada"},
        )

    assert read_ticket(context) == before
    suggestions = client.get(url(context), headers=context["admin"]).json()
    assert suggestions[0]["review_status"] == "pendente"


def test_status_provedor_requer_permissao_e_nao_revela_chave(context, monkeypatch):
    assert client.get("/ai/status").status_code == 401
    assert client.get("/ai/status", headers=context["requester"]).status_code == 403

    monkeypatch.setattr(settings, "ai_provider", "mock")
    monkeypatch.setattr(settings, "openai_api_key", None)
    demo = client.get("/ai/status", headers=context["admin"])
    assert demo.status_code == 200
    assert demo.json() == {"provider": "mock", "configured": True, "model": None}

    monkeypatch.setattr(settings, "ai_provider", "openai")
    missing_key = client.get("/ai/status", headers=context["analyst"])
    assert missing_key.status_code == 200
    assert missing_key.json() == {
        "provider": "openai", "configured": False, "model": settings.ai_model
    }

    monkeypatch.setattr(settings, "openai_api_key", SecretStr("segredo-somente-teste"))
    configured = client.get("/ai/status", headers=context["admin"])
    assert configured.status_code == 200
    assert configured.json()["configured"] is True
    assert "segredo-somente-teste" not in configured.text

    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "qwen2.5:3b")
    local = client.get("/ai/status", headers=context["analyst"])
    assert local.status_code == 200
    assert local.json() == {
        "provider": "ollama", "configured": True, "model": "qwen2.5:3b"
    }
    assert "segredo-somente-teste" not in local.text
