import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app


client = TestClient(app)


def test_ciclo_de_vida_completo():
    admin_id = None
    ticket_id = None

    try:
        # Criar dados temporários
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            admin_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES
                        (:name, :email, :password_hash, 'admin')
                    RETURNING id
                """),
                {
                    "name": "Admin Lifecycle",
                    "email": f"lifecycle-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Teste do ciclo de vida",
                    "description": "Chamado temporário para teste",
                    "requester_id": admin_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        token = create_access_token(admin_id)

        headers = {
            "Authorization": f"Bearer {token}"
        }

        # Verificar estado inicial
        with engine.connect() as connection:
            initial = connection.execute(
                text("""
                    SELECT status, resolved_at, closed_at
                    FROM tickets
                    WHERE id = :id
                """),
                {"id": ticket_id},
            ).mappings().one()

            assert initial["status"] == "aberto"
            assert initial["resolved_at"] is None
            assert initial["closed_at"] is None

        # Executar todas as transições
        statuses = [
            "em_triagem",
            "em_atendimento",
            "resolvido",
            "fechado",
        ]

        for status in statuses:
            response = client.patch(
                f"/tickets/{ticket_id}/status",
                headers=headers,
                json={"status": status},
            )

            assert response.status_code == 200, response.text
            assert response.json()["status"] == status

            if status == "resolvido":
                assert response.json()["resolved_at"] is not None
                assert response.json()["closed_at"] is None

            if status == "fechado":
                assert response.json()["resolved_at"] is not None
                assert response.json()["closed_at"] is not None

        # Verificar persistência no PostgreSQL
        with engine.connect() as connection:
            saved = connection.execute(
                text("""
                    SELECT status, opened_at, resolved_at, closed_at
                    FROM tickets
                    WHERE id = :id
                """),
                {"id": ticket_id},
            ).mappings().one()

            assert saved["status"] == "fechado"
            assert saved["resolved_at"] is not None
            assert saved["closed_at"] is not None

            assert saved["resolved_at"] >= saved["opened_at"]
            assert saved["closed_at"] >= saved["resolved_at"]

    finally:
        # Remover registros temporários
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


def test_rejeita_transicoes_invalidas():
    admin_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            admin_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES
                        (:name, :email, :password_hash, 'admin')
                    RETURNING id
                """),
                {
                    "name": "Admin Transicoes",
                    "email": f"transicoes-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Teste de transicoes invalidas",
                    "description": "Chamado temporario",
                    "requester_id": admin_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        headers = {
            "Authorization": f"Bearer {create_access_token(admin_id)}"
        }

        # Não pode pular diretamente para resolvido ou fechado.
        for invalid_status in ["resolvido", "fechado"]:
            response = client.patch(
                f"/tickets/{ticket_id}/status",
                headers=headers,
                json={"status": invalid_status},
            )

            assert response.status_code == 409, response.text

        # O chamado deve continuar aberto.
        with engine.connect() as connection:
            status = connection.execute(
                text("SELECT status FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            ).scalar_one()

            assert status == "aberto"

        # Avançar corretamente até o fechamento.
        for status in [
            "em_triagem",
            "em_atendimento",
            "resolvido",
            "fechado",
        ]:
            response = client.patch(
                f"/tickets/{ticket_id}/status",
                headers=headers,
                json={"status": status},
            )

            assert response.status_code == 200, response.text

        # Um chamado fechado não pode ser reaberto.
        for invalid_status in ["aberto", "em_atendimento"]:
            response = client.patch(
                f"/tickets/{ticket_id}/status",
                headers=headers,
                json={"status": invalid_status},
            )

            assert response.status_code == 409, response.text

        # Confirmar que continua fechado no PostgreSQL.
        with engine.connect() as connection:
            status = connection.execute(
                text("SELECT status FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            ).scalar_one()

            assert status == "fechado"

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


def test_solicitante_nao_pode_alterar_status():
    requester_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            requester_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES
                        (:name, :email, :password_hash, 'solicitante')
                    RETURNING id
                """),
                {
                    "name": "Solicitante Lifecycle",
                    "email": f"solicitante-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Teste de permissao",
                    "description": "Validar acesso ao ciclo de vida",
                    "requester_id": requester_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        headers = {
            "Authorization": f"Bearer {create_access_token(requester_id)}"
        }

        # Solicitante autenticado não pode alterar o status.
        response = client.patch(
            f"/tickets/{ticket_id}/status",
            headers=headers,
            json={"status": "em_triagem"},
        )

        assert response.status_code == 403, response.text

        # Usuário sem autenticação também não pode alterar.
        response = client.patch(
            f"/tickets/{ticket_id}/status",
            json={"status": "em_triagem"},
        )

        assert response.status_code == 401, response.text

        # Confirmar que o banco não foi alterado.
        with engine.connect() as connection:
            saved_status = connection.execute(
                text("""
                    SELECT status
                    FROM tickets
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id},
            ).scalar_one()

            assert saved_status == "aberto"

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            if requester_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": requester_id},
                )


def test_analista_pode_alterar_status():
    analyst_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            analyst_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES
                        (:name, :email, :password_hash, 'analista')
                    RETURNING id
                """),
                {
                    "name": "Analista Lifecycle",
                    "email": f"analista-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Teste de permissao analista",
                    "description": "Validar atualizacao por analista",
                    "requester_id": analyst_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        headers = {
            "Authorization": f"Bearer {create_access_token(analyst_id)}"
        }

        response = client.patch(
            f"/tickets/{ticket_id}/status",
            headers=headers,
            json={"status": "em_triagem"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "em_triagem"

        with engine.connect() as connection:
            saved_status = connection.execute(
                text("SELECT status FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            ).scalar_one()

            assert saved_status == "em_triagem"

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            if analyst_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": analyst_id},
                )


def test_alterar_status_ticket_inexistente():
    admin_id = None

    try:
        with engine.begin() as connection:
            admin_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES
                        (:name, :email, :password_hash, 'admin')
                    RETURNING id
                """),
                {
                    "name": "Admin Ticket Inexistente",
                    "email": f"notfound-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            # Escolher um ID que não existe no banco.
            missing_id = connection.execute(
                text("SELECT COALESCE(MAX(id), 0) + 100000 FROM tickets")
            ).scalar_one()

        headers = {
            "Authorization": f"Bearer {create_access_token(admin_id)}"
        }

        response = client.patch(
            f"/tickets/{missing_id}/status",
            headers=headers,
            json={"status": "em_triagem"},
        )

        assert response.status_code == 404, response.text
        assert response.json()["detail"] == "Chamado não encontrado"

        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM tickets WHERE id = :id"),
                {"id": missing_id},
            ).scalar_one()

            assert count == 0

    finally:
        with engine.begin() as connection:
            if admin_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": admin_id},
                )
