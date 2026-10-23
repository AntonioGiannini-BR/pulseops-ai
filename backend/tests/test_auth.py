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
