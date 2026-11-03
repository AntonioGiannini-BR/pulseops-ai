"""Testes automatizados do Dashboard Operacional."""

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import engine
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def limpar_dependencias():
    """Remove substituições de autenticação após cada teste."""
    yield
    app.dependency_overrides.clear()


def autenticar_como(role):
    """Simula um usuário autenticado com determinado perfil."""

    def usuario_teste():
        return {
            "id": 999999,
            "email": "teste@pulseops.example",
            "role": role,
        }

    app.dependency_overrides[get_current_user] = usuario_teste


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_dashboard_summary_permite_equipe(role):
    autenticar_como(role)

    response = client.get("/dashboard/summary")

    assert response.status_code == 200, response.text

    data = response.json()

    assert "total_chamados" in data
    assert "chamados_pendentes" in data
    assert "chamados_concluidos" in data
    assert "chamados_fora_sla" in data
    assert "horas_medias_resolucao" in data

    assert (
        data["chamados_pendentes"]
        + data["chamados_concluidos"]
        == data["total_chamados"]
    )


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_dashboard_distribution_permite_equipe(role):
    autenticar_como(role)

    response = client.get("/dashboard/distribution")

    assert response.status_code == 200, response.text

    data = response.json()

    assert set(data["por_status"]) == {
        "aberto",
        "em_triagem",
        "em_atendimento",
        "resolvido",
        "fechado",
    }

    assert set(data["por_prioridade"]) == {
        "baixa",
        "media",
        "alta",
        "critica",
    }

    total_status = sum(data["por_status"].values())
    total_prioridade = sum(data["por_prioridade"].values())

    assert total_status == total_prioridade

    with engine.connect() as connection:
        total_banco = connection.execute(
            text("SELECT COUNT(*) FROM tickets")
        ).scalar_one()

    assert total_status == total_banco


@pytest.mark.parametrize(
    "endpoint",
    [
        "/dashboard/summary",
        "/dashboard/distribution",
    ],
)
def test_dashboard_bloqueia_solicitante(endpoint):
    autenticar_como("solicitante")

    response = client.get(endpoint)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "endpoint",
    [
        "/dashboard/summary",
        "/dashboard/distribution",
    ],
)
def test_dashboard_exige_autenticacao(endpoint):
    response = client.get(endpoint)

    assert response.status_code == 401