import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app


def test_admin_atribui_ticket_a_analista_ativo():
    admin_id = None
    analyst_id = None
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            for role in ("admin", "analista"):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users
                            (full_name, email, password_hash, role)
                        VALUES
                            (:name, :email, :password_hash, :role)
                        RETURNING id
                    """),
                    {
                        "name": f"Usuario {role}",
                        "email": f"assignment-{uuid.uuid4().hex}@pulseops.example",
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()

                if role == "admin":
                    admin_id = user_id
                else:
                    analyst_id = user_id

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (title, description, requester_id, category_id)
                    VALUES
                        (:title, :description, :requester_id, :category_id)
                    RETURNING id
                """),
                {
                    "title": "Teste de atribuicao",
                    "description": "Ticket temporario",
                    "requester_id": admin_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        token = create_access_token(admin_id)

        response = TestClient(app).patch(
            f"/tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {token}"},
            json={"assignee_id": analyst_id},
        )

        assert response.status_code == 200, response.text
        assert response.json()["id"] == ticket_id
        assert response.json()["assignee_id"] == analyst_id

        with engine.connect() as connection:
            saved_assignee = connection.execute(
                text("SELECT assignee_id FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            ).scalar_one()

        assert saved_assignee == analyst_id

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            for user_id in (analyst_id, admin_id):
                if user_id is not None:
                    connection.execute(
                        text("DELETE FROM app_users WHERE id = :id"),
                        {"id": user_id},
                    )


import pytest


@pytest.mark.parametrize(
    "role, is_active",
    [
        ("analista", False),
        ("solicitante", True),
    ],
)
def test_admin_nao_atribui_ticket_a_usuario_invalido(role, is_active):
    admin_id = None
    target_id = None
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
                    "name": "Admin Teste",
                    "email": f"admin-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                },
            ).scalar_one()

            target_id = connection.execute(
                text("""
                    INSERT INTO app_users
                        (full_name, email, password_hash, role, is_active)
                    VALUES
                        (:name, :email, :password_hash, :role, :is_active)
                    RETURNING id
                """),
                {
                    "name": "Usuario Destino",
                    "email": f"target-{uuid.uuid4().hex}@pulseops.example",
                    "password_hash": hash_password("TesteSeguro123!"),
                    "role": role,
                    "is_active": is_active,
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
                    "title": "Teste de atribuicao invalida",
                    "description": "Verificacao de regras de atribuicao",
                    "requester_id": admin_id,
                    "category_id": category_id,
                },
            ).scalar_one()

        token = create_access_token(admin_id)

        response = TestClient(app).patch(
            f"/tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {token}"},
            json={"assignee_id": target_id},
        )

        assert response.status_code == 422, response.text

        with engine.connect() as connection:
            saved_assignee = connection.execute(
                text("SELECT assignee_id FROM tickets WHERE id = :id"),
                {"id": ticket_id},
            ).scalar_one()

        assert saved_assignee is None

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            for user_id in (target_id, admin_id):
                if user_id is not None:
                    connection.execute(
                        text("DELETE FROM app_users WHERE id = :id"),
                        {"id": user_id},
                    )


def test_admin_pode_reatribuir_ticket():
    admin_id = None
    analyst_ids = []
    ticket_id = None

    try:
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            for role in ("admin", "analista", "analista"):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users
                            (full_name, email, password_hash, role)
                        VALUES
                            (:name, :email, :password_hash, :role)
                        RETURNING id
                    """),
                    {
                        "name": f"Usuario {role}",
                        "email": f"reassign-{uuid.uuid4().hex}@pulseops.example",
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()

                if role == "admin":
                    admin_id = user_id
                else:
                    analyst_ids.append(user_id)

            ticket_id = connection.execute(
                text("""
                    INSERT INTO tickets
                        (
                            title,
                            description,
                            requester_id,
                            category_id,
                            assignee_id
                        )
                    VALUES
                        (
                            :title,
                            :description,
                            :requester_id,
                            :category_id,
                            :assignee_id
                        )
                    RETURNING id
                """),
                {
                    "title": "Teste de reatribuicao",
                    "description": "Transferencia entre analistas",
                    "requester_id": admin_id,
                    "category_id": category_id,
                    "assignee_id": analyst_ids[0],
                },
            ).scalar_one()

        token = create_access_token(admin_id)

        response = TestClient(app).patch(
            f"/tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {token}"},
            json={"assignee_id": analyst_ids[1]},
        )

        assert response.status_code == 200, response.text
        assert response.json()["assignee_id"] == analyst_ids[1]

        with engine.connect() as connection:
            saved_assignee = connection.execute(
                text("""
                    SELECT assignee_id
                    FROM tickets
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id},
            ).scalar_one()

        assert saved_assignee == analyst_ids[1]

    finally:
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("DELETE FROM tickets WHERE id = :id"),
                    {"id": ticket_id},
                )

            for user_id in reversed(analyst_ids):
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": user_id},
                )

            if admin_id is not None:
                connection.execute(
                    text("DELETE FROM app_users WHERE id = :id"),
                    {"id": admin_id},
                )


def test_admin_nao_pode_atribuir_ticket_inexistente():
    admin_id = None
    analyst_id = None

    try:
        with engine.begin() as connection:
            for role in ("admin", "analista"):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users
                            (full_name, email, password_hash, role)
                        VALUES
                            (:name, :email, :password_hash, :role)
                        RETURNING id
                    """),
                    {
                        "name": f"Usuario {role}",
                        "email": f"notfound-{uuid.uuid4().hex}@pulseops.example",
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()

                if role == "admin":
                    admin_id = user_id
                else:
                    analyst_id = user_id

        token = create_access_token(admin_id)

        response = TestClient(app).patch(
            "/tickets/999999999999/assign",
            headers={"Authorization": f"Bearer {token}"},
            json={"assignee_id": analyst_id},
        )

        assert response.status_code == 404, response.text
        assert response.json()["detail"] == "Chamado não encontrado"

    finally:
        with engine.begin() as connection:
            for user_id in (analyst_id, admin_id):
                if user_id is not None:
                    connection.execute(
                        text("DELETE FROM app_users WHERE id = :id"),
                        {"id": user_id},
                    )
