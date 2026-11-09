"""Criação intencional de administrador, sem senha por argumento ou seed pública.

Uso (na pasta backend): python -m scripts.create_admin --email admin@empresa.local --name "Admin"
"""

import argparse
import getpass
import re

from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import engine


def create_admin(*, email: str, full_name: str, password: str) -> int:
    normalized_email = email.strip().lower()
    normalized_name = full_name.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
        raise ValueError("Informe um e-mail válido")
    if not 2 <= len(normalized_name) <= 150:
        raise ValueError("O nome deve conter entre 2 e 150 caracteres")
    if len(password) < 12:
        raise ValueError("A senha deve ter pelo menos 12 caracteres")
    with engine.begin() as connection:
        existing = connection.execute(
            text("SELECT id FROM app_users WHERE LOWER(email) = :email"),
            {"email": normalized_email},
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("Já existe uma conta com esse e-mail")
        created_id = connection.execute(
            text("""
                INSERT INTO app_users (full_name, email, password_hash, role, is_active)
                VALUES (:name, :email, :password_hash, 'admin', TRUE)
                RETURNING id
            """),
            {
                "name": normalized_name,
                "email": normalized_email,
                "password_hash": hash_password(password),
            },
        ).scalar_one()
    return created_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria uma conta administrativa local com senha privada.")
    parser.add_argument("--email", required=True, help="E-mail da conta administrativa")
    parser.add_argument("--name", required=True, help="Nome da conta administrativa")
    args = parser.parse_args()
    first = getpass.getpass("Senha forte (mínimo 12 caracteres): ")
    second = getpass.getpass("Confirme a senha: ")
    if first != second:
        parser.error("As senhas não correspondem")
    try:
        user_id = create_admin(email=args.email, full_name=args.name, password=first)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Administrador criado com ID {user_id}. A senha não foi exibida.")


if __name__ == "__main__":
    main()
