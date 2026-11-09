"""Testes de integração do histórico de chamados."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app


client = TestClient(app)


def test_historico_completo_e_permissoes():
    user_ids = []
    ticket_id = None

    try:
        # Preparar usuários temporários.
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            for role in ("admin", "analista", "solicitante"):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users (
                            full_name, email, password_hash, role
                        )
                        VALUES (
                            :name, :email, :password_hash, :role
                        )
                        RETURNING id
                    """),
                    {
                        "name": f"Teste Historico {role}",
                        "email": (
                            f"history-{uuid.uuid4().hex}@pulseops.example"
                        ),
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()

                user_ids.append(user_id)

        admin_id, analyst_id, outsider_id = user_ids

        admin_headers = {
            "Authorization": (
                f"Bearer {create_access_token(admin_id)}"
            )
        }

        outsider_headers = {
            "Authorization": (
                f"Bearer {create_access_token(outsider_id)}"
            )
        }

        # 1. Criar chamado pela API.
        response = client.post(
            "/tickets/",
            headers=admin_headers,
            json={
                "title": "Teste de auditoria",
                "description": "Validar histórico completo",
                "requester_id": admin_id,
                "category_id": category_id,
                "priority": "media",
            },
        )

        assert response.status_code == 201, response.text

        ticket_id = response.json()["id"]

        # 2. Alterar prioridade.
        response = client.patch(
            f"/tickets/{ticket_id}",
            headers=admin_headers,
            json={"priority": "alta"},
        )

        assert response.status_code == 200, response.text

        # 3. Atribuir analista.
        response = client.patch(
            f"/tickets/{ticket_id}/assign",
            headers=admin_headers,
            json={"assignee_id": analyst_id},
        )

        assert response.status_code == 200, response.text

        # 4. Alterar status.
        response = client.patch(
            f"/tickets/{ticket_id}/status",
            headers=admin_headers,
            json={"status": "em_triagem"},
        )

        assert response.status_code == 200, response.text

        # 5. Consultar histórico.
        history_url = f"/tickets/{ticket_id}/history"

        response = client.get(
            history_url,
            headers=admin_headers,
        )

        assert response.status_code == 200, response.text

        history = response.json()

        assert len(history) == 4

        assert [event["action"] for event in history] == [
            "criacao",
            "mudanca_prioridade",
            "atribuicao",
            "mudanca_status",
        ]

        assert all(
            event["actor_id"] == admin_id
            for event in history
        )

        assert all(
            event["ticket_id"] == ticket_id
            for event in history
        )

        assert history[0]["old_value"] is None
        assert history[0]["new_value"] == "aberto"

        assert history[1]["old_value"] == "media"
        assert history[1]["new_value"] == "alta"

        assert history[2]["old_value"] is None
        assert history[2]["new_value"] == str(analyst_id)

        assert history[3]["old_value"] == "aberto"
        assert history[3]["new_value"] == "em_triagem"

        # 6. Operações repetidas não devem duplicar eventos.
        response = client.patch(
            f"/tickets/{ticket_id}",
            headers=admin_headers,
            json={"priority": "alta"},
        )
        assert response.status_code == 200, response.text

        response = client.patch(
            f"/tickets/{ticket_id}/assign",
            headers=admin_headers,
            json={"assignee_id": analyst_id},
        )
        assert response.status_code == 200, response.text

        # 7. Transição inválida não deve gerar histórico.
        response = client.patch(
            f"/tickets/{ticket_id}/status",
            headers=admin_headers,
            json={"status": "fechado"},
        )

        assert response.status_code == 409, response.text

        response = client.get(
            history_url,
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert len(response.json()) == 4

        # 8. Solicitante não pode consultar chamado de outro.
        response = client.get(
            history_url,
            headers=outsider_headers,
        )

        assert response.status_code == 404

        # 9. Solicitante pode consultar o próprio histórico.
        with engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE tickets
                    SET requester_id = :requester_id
                    WHERE id = :ticket_id
                """),
                {
                    "requester_id": outsider_id,
                    "ticket_id": ticket_id,
                },
            )

        response = client.get(
            history_url,
            headers=outsider_headers,
        )

        assert response.status_code == 200, response.text
        assert len(response.json()) == 4

        # 10. Acesso sem autenticação.
        response = client.get(history_url)

        assert response.status_code == 401

        # 10. Chamado inexistente.
        response = client.get(
            "/tickets/999999999999/history",
            headers=admin_headers,
        )

        assert response.status_code == 404

    finally:
        # Limpar dados temporários.
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            for user_id in reversed(user_ids):
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": user_id},
                )


def test_rollback_quando_auditoria_falha(monkeypatch):
    """Falha na auditoria não pode persistir alteração do chamado."""

    admin_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            admin_id = connection.execute(
                text("""
                    INSERT INTO app_users (
                        full_name, email, password_hash, role
                    )
                    VALUES (
                        :name, :email, :password_hash, 'admin'
                    )
                    RETURNING id
                """),
                {
                    "name": "Admin Rollback",
                    "email": f"rollback-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets (
                        title, description, requester_id,
                        category_id, priority
                    )
                    VALUES (
                        :title, :description, :requester_id,
                        :category_id, 'media'
                    )
                    RETURNING id
                """),
                {
                    "title": "Teste de rollback",
                    "description": "Validar atomicidade da auditoria",
                    "requester_id": admin_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        def simular_falha(*args, **kwargs):
            raise RuntimeError("Falha simulada na auditoria")

        monkeypatch.setattr(
            "app.api.tickets.record_ticket_history",
            simular_falha,
        )

        headers = {
            "Authorization": f"Bearer {create_access_token(admin_id)}"
        }

        # A falha é esperada neste teste.
        try:
            client.patch(
                f"/tickets/{ticket_id}",
                headers=headers,
                json={"priority": "alta"},
            )
        except RuntimeError as exc:
            assert str(exc) == "Falha simulada na auditoria"
        else:
            raise AssertionError(
                "A operação deveria falhar durante a auditoria"
            )

        # A prioridade original deve permanecer no PostgreSQL.
        with engine.connect() as connection:
            priority = connection.execute(
                text("""
                    SELECT priority
                    FROM tickets
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id},
            ).scalar_one()

            history_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM ticket_history
                    WHERE ticket_id = :ticket_id
                """),
                {"ticket_id": ticket_id},
            ).scalar_one()

        assert priority == "media"
        assert history_count == 0

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            if admin_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": admin_id},
                )
