import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_usuario_inexistente():
    response = client.post("/auth/login", json={"email": "inexistente@pulseops.example", "password": "senha123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos"


def test_login_senha_incorreta():
    response = client.post("/auth/login", json={"email": "teste.auth@pulseops.example", "password": "SenhaErrada123!"})
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos"


def test_tickets_sem_token():
    from fastapi.testclient import TestClient
    from app.main import app
    response = TestClient(app).get("/tickets/")
    assert response.status_code == 401


def test_tickets_token_invalido():
    from fastapi.testclient import TestClient
    from app.main import app
    response = TestClient(app).get("/tickets/", headers={"Authorization": "Bearer token.invalido.aqui"})
    assert response.status_code == 401


def test_tickets_token_expirado():
    import jwt
    from datetime import datetime, timedelta, timezone
    from fastapi.testclient import TestClient
    from app.core.config import settings
    from app.main import app

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    response = TestClient(app).get("/tickets/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_solicitante_nao_pode_atualizar_ticket():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": "solicitante@pulseops.example",
        "role": "solicitante",
    }

    try:
        response = TestClient(app).patch(
            "/tickets/1",
            json={"priority": "alta"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Você não tem permissão para realizar esta ação"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_solicitante_nao_pode_criar_ticket_para_outro_usuario():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": "solicitante@pulseops.example",
        "role": "solicitante",
    }

    try:
        response = TestClient(app).post(
            "/tickets/",
            json={
                "title": "Chamado não autorizado",
                "description": "Tentativa de criar para outro usuário",
                "requester_id": 999999,
                "category_id": 1,
                "priority": "media",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Você não pode criar chamados em nome de outro usuário"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_staff_pode_atualizar_ticket(role):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": f"{role}@pulseops.example",
        "role": role,
    }

    try:
        response = TestClient(app).patch(
            "/tickets/999999999",
            json={"priority": "alta"},
        )

        # 404 indica que a autorização foi permitida,
        # mas o ticket informado não existe.
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_perfil_desconhecido_nao_pode_criar_ticket():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": "desconhecido@pulseops.example",
        "role": "desconhecido",
    }

    try:
        response = TestClient(app).post(
            "/tickets/",
            json={
                "title": "Teste de permissão",
                "description": "Perfil não autorizado",
                "requester_id": 1,
                "category_id": 1,
                "priority": "media",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Perfil sem permissão para criar chamados"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_staff_pode_consultar_ticket_de_outro_usuario(role):
    import uuid

    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from app.core.security import create_access_token, hash_password
    from app.db.session import engine
    from app.main import app

    requester_id = None
    staff_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            for user_role in ("solicitante", role):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users
                            (full_name, email, password_hash, role)
                        VALUES
                            (:name, :email, :password_hash, :role)
                        RETURNING id
                    """),
                    {
                        "name": "Usuario Temporario RBAC",
                        "email": f"rbac-{uuid.uuid4().hex}@pulseops.example",
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": user_role,
                    },
                ).scalar_one()

                if user_role == "solicitante":
                    requester_id = user_id
                else:
                    staff_id = user_id

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Ticket temporario RBAC",
                    "description": "Teste de permissao de consulta",
                    "requester_id": requester_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        token = create_access_token(staff_id)
        headers = {"Authorization": f"Bearer {token}"}
        client = TestClient(app)

        response = client.get(
            f"/tickets/{ticket_id}",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == ticket_id

        response = client.get("/tickets/", headers=headers)

        assert response.status_code == 200
        assert ticket_id in [
            ticket["id"] for ticket in response.json()
        ]

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            for user_id in (staff_id, requester_id):
                if user_id is not None:
                    connection.execute(
                        text("DELETE FROM app_users WHERE id = :id"),
                        {"id": user_id},
                    )


@pytest.mark.parametrize("role", ["analista", "solicitante"])
def test_apenas_admin_pode_atribuir_ticket(role):
    from fastapi.testclient import TestClient
    from app.api.deps import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": f"{role}@pulseops.example",
        "role": role,
    }

    try:
        response = TestClient(app).patch(
            "/tickets/999999999/assign",
            json={"assignee_id": 1},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Você não tem permissão para realizar esta ação"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
