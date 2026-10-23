
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
