"""Criação segura de administrador sem credenciais publicadas."""

import uuid

import pytest
from sqlalchemy import text

from app.core.security import verify_password
from app.db.session import engine
from scripts.create_admin import create_admin


def test_creates_active_admin_with_hashed_password():
    email = f"bootstrap-{uuid.uuid4().hex}@pulseops.example"
    password = "SenhaSeguraDeTeste!2026"
    user_id = None
    try:
        user_id = create_admin(email=email.upper(), full_name="Admin Temporário", password=password)
        with engine.connect() as connection:
            user = connection.execute(
                text("SELECT email, password_hash, role, is_active FROM app_users WHERE id=:id"),
                {"id": user_id},
            ).mappings().one()
        assert user["email"] == email
        assert user["role"] == "admin"
        assert user["is_active"] is True
        assert password not in user["password_hash"]
        assert verify_password(password, user["password_hash"])
        with pytest.raises(ValueError, match="Já existe"):
            create_admin(email=email, full_name="Outra conta", password=password)
    finally:
        if user_id is not None:
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM app_users WHERE id=:id"), {"id": user_id})


@pytest.mark.parametrize("email,name,password", [
    ("invalid", "Admin", "SenhaSeguraDeTeste!"),
    ("valid@empresa.example", "A", "SenhaSeguraDeTeste!"),
    ("valid@empresa.example", "Admin", "curta"),
])
def test_rejects_invalid_account_data(email, name, password):
    with pytest.raises(ValueError):
        create_admin(email=email, full_name=name, password=password)
