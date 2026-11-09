
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import engine
from app.main import app


@pytest.fixture
def test_user():
    email = f"auth-{uuid.uuid4().hex}@pulseops.example"

    with engine.begin() as connection:
        user_id = connection.execute(
            text("""
                INSERT INTO app_users
                    (full_name, email, password_hash, role)
                VALUES
                    (:name, :email, :password_hash, :role)
                RETURNING id
            """),
            {
                "name": "Usuario Temporario",
                "email": email,
                "password_hash": hash_password("TesteSeguro123!"),
                "role": "solicitante",
            },
        ).scalar_one()

    try:
        yield {"id": user_id, "email": email}
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM app_users WHERE id = :id"),
                {"id": user_id},
            )


def test_login_valido(test_user):
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": "TesteSeguro123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_senha_errada(test_user):
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": "SenhaErrada!",
        },
    )

    assert response.status_code == 401


def test_login_conta_desativada(test_user):
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE app_users SET is_active = FALSE WHERE id = :id"),
            {"id": test_user["id"]},
        )

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": "TesteSeguro123!",
        },
    )

    assert response.status_code == 401


def test_tickets_com_jwt_valido(test_user):
    from app.core.security import create_access_token
    token = create_access_token(test_user["id"])
    response = TestClient(app).get("/tickets/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_solicitante_consulta_proprio_ticket(test_user):
    from app.core.security import create_access_token

    with engine.begin() as connection:
        category_id = connection.execute(
            text("SELECT id FROM categories ORDER BY id LIMIT 1")
        ).scalar_one_or_none()

        assert category_id is not None, "Nenhuma categoria cadastrada"

        ticket_id = connection.execute(
            text("""
                INSERT INTO tickets
                    (title, description, requester_id, category_id)
                VALUES
                    (:title, :description, :requester_id, :category_id)
                RETURNING id
            """),
            {
                "title": "Teste de RBAC",
                "description": "Chamado temporário para testar permissões",
                "requester_id": test_user["id"],
                "category_id": category_id,
            },
        ).scalar_one()

    try:
        token = create_access_token(test_user["id"])

        response = TestClient(app).get(
            f"/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == ticket_id
        assert response.json()["requester_id"] == test_user["id"]

    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            )



def test_solicitante_nao_consulta_ticket_de_outro_usuario(test_user):
    from app.core.security import create_access_token

    other_email = f"rbac-{uuid.uuid4().hex}@pulseops.example"
    other_user_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            other_user_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role)
                    VALUES (:name, :email, :password_hash, 'solicitante')
                    RETURNING id
                """),
                {
                    "name": "Outro Solicitante",
                    "email": other_email,
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Ticket privado RBAC",
                    "description": "Teste de isolamento",
                    "requester_id": other_user_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        token = create_access_token(test_user["id"])
        headers = {"Authorization": f"Bearer {token}"}
        client = TestClient(app)

        response = client.get(f"/tickets/{ticket_id}", headers=headers)
        assert response.status_code == 404

        response = client.get("/tickets/", headers=headers)
        assert response.status_code == 200
        assert ticket_id not in [t["id"] for t in response.json()]

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )
            if other_user_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": other_user_id},
                )


def test_solicitante_pode_criar_proprio_ticket(test_user):
    from app.core.security import create_access_token

    with engine.begin() as connection:
        category_id = connection.execute(
            text("SELECT id FROM categories ORDER BY id LIMIT 1")
        ).scalar_one_or_none()

    assert category_id is not None, "Nenhuma categoria cadastrada"

    token = create_access_token(test_user["id"])
    ticket_id = None

    try:
        response = TestClient(app).post(
            "/tickets/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Chamado autorizado RBAC",
                "description": "Teste de criação pelo próprio solicitante",
                "requester_id": test_user["id"],
                "category_id": category_id,
                "priority": "media",
            },
        )

        assert response.status_code == 201, response.text
        ticket_id = response.json()["id"]
        assert response.json()["requester_id"] == test_user["id"]

    finally:
        if ticket_id is not None:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )
