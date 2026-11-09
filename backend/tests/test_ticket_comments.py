"""Testes de integração dos comentários de chamados."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import create_access_token, hash_password
from app.db.session import engine
from app.main import app


client = TestClient(app)


def test_comentarios_e_permissoes():
    user_ids = []
    ticket_id = None

    try:
        # Criar usuários temporários.
        with engine.begin() as connection:
            category_id = connection.execute(
                text("SELECT id FROM categories ORDER BY id LIMIT 1")
            ).scalar_one()

            for role in (
                "admin",
                "analista",
                "solicitante",
                "solicitante",
            ):
                user_id = connection.execute(
                    text("""
                        INSERT INTO app_users (
                            full_name,
                            email,
                            password_hash,
                            role
                        )
                        VALUES (
                            :name,
                            :email,
                            :password_hash,
                            :role
                        )
                        RETURNING id
                    """),
                    {
                        "name": f"Teste Comentarios {role}",
                        "email": (
                            f"comments-{uuid.uuid4().hex}@pulseops.example"
                        ),
                        "password_hash": hash_password("TesteSeguro123!"),
                        "role": role,
                    },
                ).scalar_one()

                user_ids.append(user_id)

        admin_id, analyst_id, requester_id, outsider_id = user_ids

        def headers(user_id):
            return {
                "Authorization": (
                    f"Bearer {create_access_token(user_id)}"
                )
            }

        admin_headers = headers(admin_id)
        analyst_headers = headers(analyst_id)
        requester_headers = headers(requester_id)
        outsider_headers = headers(outsider_id)

        # Criar chamado pertencente ao solicitante.
        response = client.post(
            "/tickets/",
            headers=requester_headers,
            json={
                "title": "Teste de comentarios",
                "description": "Validar comentarios e permissoes",
                "requester_id": requester_id,
                "category_id": category_id,
                "priority": "media",
            },
        )

        assert response.status_code == 201, response.text

        ticket_id = response.json()["id"]
        comments_url = f"/tickets/{ticket_id}/comments"

        # 1. Solicitante cria comentário público.
        response = client.post(
            comments_url,
            headers=requester_headers,
            json={
                "body": "Preciso de ajuda com este chamado.",
            },
        )

        assert response.status_code == 201, response.text

        public_comment = response.json()

        assert public_comment["ticket_id"] == ticket_id
        assert public_comment["author_id"] == requester_id
        assert public_comment["is_internal"] is False
        assert public_comment["created_at"] is not None

        # 2. Administrador cria comentário interno.
        response = client.post(
            comments_url,
            headers=admin_headers,
            json={
                "body": "Observacao interna da equipe.",
                "is_internal": True,
            },
        )

        assert response.status_code == 201, response.text

        internal_comment = response.json()

        assert internal_comment["author_id"] == admin_id
        assert internal_comment["is_internal"] is True

        # 3. Analista cria comentário interno.
        response = client.post(
            comments_url,
            headers=analyst_headers,
            json={
                "body": "Analise tecnica em andamento.",
                "is_internal": True,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["author_id"] == analyst_id

        # 4. Administrador visualiza todos os comentários.
        response = client.get(
            comments_url,
            headers=admin_headers,
        )

        assert response.status_code == 200, response.text
        assert len(response.json()) == 3

        # 5. Analista visualiza todos os comentários.
        response = client.get(
            comments_url,
            headers=analyst_headers,
        )

        assert response.status_code == 200, response.text
        assert len(response.json()) == 3

        # 6. Solicitante visualiza somente comentários públicos.
        response = client.get(
            comments_url,
            headers=requester_headers,
        )

        assert response.status_code == 200, response.text

        comments = response.json()

        assert len(comments) == 1
        assert comments[0]["id"] == public_comment["id"]
        assert all(not comment["is_internal"] for comment in comments)

        # 7. Solicitante não pode criar comentário interno.
        response = client.post(
            comments_url,
            headers=requester_headers,
            json={
                "body": "Tentativa de comentario interno.",
                "is_internal": True,
            },
        )

        assert response.status_code == 403

        # 8. Outro solicitante não pode visualizar comentários.
        response = client.get(
            comments_url,
            headers=outsider_headers,
        )

        assert response.status_code == 404

        # 9. Outro solicitante não pode comentar.
        response = client.post(
            comments_url,
            headers=outsider_headers,
            json={"body": "Acesso indevido."},
        )

        assert response.status_code == 404

        # 10. Comentários vazios são rejeitados.
        for body in ("", "   "):
            response = client.post(
                comments_url,
                headers=admin_headers,
                json={"body": body},
            )

            assert response.status_code == 422

        # 11. O cliente não pode escolher o autor.
        response = client.post(
            comments_url,
            headers=admin_headers,
            json={
                "body": "Tentativa de alterar autor.",
                "author_id": outsider_id,
            },
        )

        assert response.status_code == 422

        # 12. Acesso sem autenticação.
        assert client.get(comments_url).status_code == 401

        assert client.post(
            comments_url,
            json={"body": "Sem autenticacao"},
        ).status_code == 401

        # 13. Chamado inexistente.
        nonexistent_url = "/tickets/999999999999/comments"

        assert client.get(
            nonexistent_url,
            headers=admin_headers,
        ).status_code == 404

        assert client.post(
            nonexistent_url,
            headers=admin_headers,
            json={"body": "Teste"},
        ).status_code == 404

        # 14. Tentativas rejeitadas não criaram comentários.
        response = client.get(
            comments_url,
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert len(response.json()) == 3

    finally:
        # Remover chamado e comentários associados.
        with engine.begin() as connection:
            if ticket_id is not None:
                connection.execute(
                    text("""
                        DELETE FROM tickets
                        WHERE id = :ticket_id
                    """),
                    {"ticket_id": ticket_id},
                )

            # Remover usuários temporários.
            for user_id in user_ids:
                connection.execute(
                    text("""
                        DELETE FROM app_users
                        WHERE id = :user_id
                    """),
                    {"user_id": user_id},
                )
