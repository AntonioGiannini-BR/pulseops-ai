"""Fluxo integrado: login real → chamado → triagem → revisão → automação → auditoria.

Usa banco PostgreSQL de teste com dados temporários, sem acesso a LLM externo.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import engine
from app.main import app


client = TestClient(app)


def test_full_ticket_journey_with_approval(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")
    user_id = ticket_id = None
    email = f"journey-{uuid.uuid4().hex}@pulseops.example"
    password = "SenhaDeTesteSeguro#2026"
    try:
        with engine.begin() as connection:
            user_id = connection.execute(
                text("""
                    INSERT INTO app_users (full_name, email, password_hash, role)
                    VALUES ('Analista de Teste', :email, :password, 'admin')
                    RETURNING id
                """),
                {"email": email, "password": hash_password(password)},
            ).scalar_one()
            category_id = connection.execute(
                text("SELECT id FROM categories WHERE is_active = TRUE ORDER BY id LIMIT 1")
            ).scalar_one()

        login_response = client.post("/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200, login_response.text
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post("/tickets/", headers=headers, json={
            "title": "Sistema de vendas indisponível",
            "description": "Equipe não consegue finalizar pedidos.",
            "requester_id": user_id,
            "category_id": category_id,
            "priority": "baixa",
        })
        assert created.status_code == 201, created.text
        ticket_id = created.json()["id"]
        assert created.json()["priority"] == "baixa"

        triage_url = f"/tickets/{ticket_id}/ai-suggestions"
        suggestion = client.post(triage_url, headers=headers)
        assert suggestion.status_code == 201, suggestion.text
        assert suggestion.json()["model_name"] == "demo-regras-locais"
        assert suggestion.json()["review_status"] == "pendente"

        before_review = client.get(f"/tickets/{ticket_id}", headers=headers)
        assert before_review.json()["priority"] == "baixa"

        approved = client.post(
            f"{triage_url}/{suggestion.json()['id']}/review",
            json={"decision": "aprovada"}, headers=headers,
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["suggestion"]["review_status"] == "aprovada"

        guide = client.post(f"/tickets/{ticket_id}/resolution-guide", headers=headers)
        assert guide.status_code == 200, guide.text
        assert guide.json()["model_name"] == "demo-guia-local"

        catalog_url = f"/tickets/{ticket_id}/resolution-automations"
        catalog = client.get(catalog_url, headers=headers)
        assert catalog.status_code == 200
        assert catalog.json()["expected_status"] == "aberto"

        send = client.post(
            f"{catalog_url}/send_guidance/execute",
            json={"approved": True, "expected_status": "aberto"},
            headers=headers,
        )
        assert send.status_code == 200, send.text
        assert send.json()["comment"]["is_internal"] is False
        assert client.post(
            f"{catalog_url}/send_guidance/execute",
            json={"approved": True, "expected_status": "aberto"},
            headers=headers,
        ).status_code == 409

        advance = client.post(
            f"{catalog_url}/advance_workflow/execute",
            json={"approved": True, "expected_status": "aberto"},
            headers=headers,
        )
        assert advance.status_code == 200, advance.text
        assert advance.json()["ticket_status"] == "em_triagem"

        ticket = client.get(f"/tickets/{ticket_id}", headers=headers)
        assert ticket.status_code == 200
        assert ticket.json()["status"] == "em_triagem"
        assert ticket.json()["resolved_at"] is None

        comments = client.get(f"/tickets/{ticket_id}/comments", headers=headers)
        assert comments.status_code == 200
        assert len(comments.json()) == 1

        history = client.get(f"/tickets/{ticket_id}/history", headers=headers)
        assert history.status_code == 200
        actions = [item["action"] for item in history.json()]
        for action in [
            "criacao", "ai_sugestao_criada", "ai_sugestao_aprovada",
            "automacao_orientacao", "mudanca_status", "automacao_fluxo",
        ]:
            assert action in actions

        overview = client.get("/ai/overview", headers=headers)
        assert overview.status_code == 200
        assert overview.json()["approved"] >= 1
    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(text("DELETE FROM tickets WHERE id=:id"), {"id": ticket_id})
            if user_id is not None:
                connection.execute(text("DELETE FROM app_users WHERE id=:id"), {"id": user_id})
