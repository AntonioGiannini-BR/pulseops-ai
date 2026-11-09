"""API de administração de contas: autorização, segurança e auditoria."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import engine
from app.main import app

PASSWORD = "SenhaSeguraDeTeste#2026"
client = TestClient(app)


@pytest.fixture
def staff_and_requester():
    marker = uuid.uuid4().hex
    ids = []
    with engine.begin() as db:
        for role in ("admin", "solicitante"):
            user_id = db.execute(
                text("""
                    INSERT INTO app_users (full_name, email, password_hash, role)
                    VALUES (:name, :email, :hash, :role) RETURNING id
                """),
                {
                    "name": "Conta de Teste",
                    "email": role + "-" + marker + "@pulseops.example",
                    "hash": hash_password(PASSWORD),
                    "role": role,
                },
            ).scalar_one()
            ids.append(user_id)
    try:
        yield {
            "admin_id": ids[0],
            "requester_id": ids[1],
            "admin_headers": {"Authorization": "Bearer " + create_access_token(ids[0])},
            "requester_headers": {"Authorization": "Bearer " + create_access_token(ids[1])},
            "ids": ids,
        }
    finally:
        with engine.begin() as db:
            for user_id in ids:
                db.execute(
                    text("""
                        DELETE FROM user_audit_events
                        WHERE actor_id = :id OR target_user_id = :id
                    """), {"id": user_id},
                )
            for user_id in reversed(ids):
                db.execute(text("DELETE FROM app_users WHERE id = :id"), {"id": user_id})


def _new_user_payload():
    return {
        "full_name": "Novo Analista",
        "email": "analista-" + uuid.uuid4().hex + "@pulseops.example",
        "role": "analista",
        "password": PASSWORD,
        "department_id": None,
    }


def test_only_admin_can_list_or_create_accounts(staff_and_requester):
    info = staff_and_requester
    assert client.get("/users/").status_code == 401
    assert client.get("/users/", headers=info["requester_headers"]).status_code == 403
    assert client.post("/users/", json=_new_user_payload(), headers=info["requester_headers"]).status_code == 403
    response = client.get("/users/?limit=5", headers=info["admin_headers"])
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all("password_hash" not in item and "password" not in item for item in response.json())


def test_create_duplicate_invalid_role_and_audit(staff_and_requester):
    info = staff_and_requester
    payload = _new_user_payload()
    invalid = {**payload, "role": "admin"}
    assert client.post("/users/", headers=info["admin_headers"], json=invalid).status_code == 422
    assert client.post("/users/", headers=info["admin_headers"], json={**payload, "password": "curta"}).status_code == 422
    assert client.post("/users/", headers=info["admin_headers"], json={**payload, "department_id": 99999999}).status_code == 422

    created = client.post("/users/", headers=info["admin_headers"], json=payload)
    assert created.status_code == 201, created.text
    user = created.json()
    info["ids"].append(user["id"])
    assert user["email"] == payload["email"]
    assert user["role"] == "analista"
    assert user["is_active"] is True
    assert "password" not in user and "password_hash" not in user

    with engine.connect() as db:
        row = db.execute(
            text("SELECT password_hash FROM app_users WHERE id=:id"),
            {"id": user["id"]},
        ).scalar_one()
        assert row != PASSWORD and verify_password(PASSWORD, row)
        event = db.execute(
            text("SELECT action, actor_id FROM user_audit_events WHERE target_user_id=:id"),
            {"id": user["id"]},
        ).mappings().one()
    assert event["action"] == "conta_criada"
    assert event["actor_id"] == info["admin_id"]

    duplicate = client.post(
        "/users/",
        headers=info["admin_headers"],
        json={**payload, "email": payload["email"].upper()},
    )
    assert duplicate.status_code == 409


def test_disable_reenable_revokes_access_and_protects_admin(staff_and_requester):
    info = staff_and_requester
    target_id = info["requester_id"]
    assert client.patch(
        "/users/" + str(target_id) + "/status",
        headers=info["requester_headers"],
        json={"is_active": False},
    ).status_code == 403
    assert client.patch(
        "/users/" + str(info["admin_id"]) + "/status",
        headers=info["admin_headers"],
        json={"is_active": False},
    ).status_code == 403

    disabled = client.patch(
        "/users/" + str(target_id) + "/status",
        headers=info["admin_headers"],
        json={"is_active": False},
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["is_active"] is False
    assert client.get("/auth/me", headers=info["requester_headers"]).status_code == 401
    assert client.post("/auth/login", json={
        "email": "solicitante-" + "wrong" + "@pulseops.example",
        "password": PASSWORD,
    }).status_code == 401

    enabled = client.patch(
        "/users/" + str(target_id) + "/status",
        headers=info["admin_headers"],
        json={"is_active": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True
    assert client.get("/auth/me", headers=info["requester_headers"]).status_code == 200
    with engine.connect() as db:
        actions = db.execute(
            text("""
                SELECT action FROM user_audit_events
                WHERE target_user_id=:id ORDER BY id
            """), {"id": target_id},
        ).scalars().all()
    assert actions == ["conta_desativada", "conta_reativada"]


def test_password_change_requires_old_secret_and_creates_audit(staff_and_requester):
    info = staff_and_requester
    headers = info["requester_headers"]
    assert client.post("/auth/change-password", headers=headers, json={
        "current_password": "errada",
        "new_password": "OutraSenhaDeTeste#2026",
    }).status_code == 401
    assert client.post("/auth/change-password", headers=headers, json={
        "current_password": PASSWORD, "new_password": PASSWORD,
    }).status_code == 422

    changed = client.post("/auth/change-password", headers=headers, json={
        "current_password": PASSWORD, "new_password": "OutraSenhaDeTeste#2026",
    })
    assert changed.status_code == 200, changed.text
    with engine.connect() as db:
        email = db.execute(
            text("SELECT email FROM app_users WHERE id=:id"),
            {"id": info["requester_id"]},
        ).scalar_one()
        audit = db.execute(
            text("SELECT action FROM user_audit_events WHERE target_user_id=:id ORDER BY id DESC LIMIT 1"),
            {"id": info["requester_id"]},
        ).scalar_one()
    assert audit == "senha_alterada"
    assert client.post("/auth/login", json={"email": email, "password": PASSWORD}).status_code == 401
    assert client.post("/auth/login", json={
        "email": email, "password": "OutraSenhaDeTeste#2026",
    }).status_code == 200
