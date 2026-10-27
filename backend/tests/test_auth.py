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
