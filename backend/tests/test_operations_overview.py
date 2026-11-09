"""Testes das visões agregadas e da autorização, com PostgreSQL isolado na CI."""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def auth(role: str):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 999999, "email": "teste@pulseops.example", "role": role,
    }


@pytest.mark.parametrize("path", ["/teams/summary", "/ai/overview"])
def test_views_require_auth(path):
    assert client.get(path).status_code == 401
    auth("solicitante")
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_team_summary_has_consistent_totals(role):
    auth(role)
    response = client.get("/teams/summary")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) >= 1
    assert len({item["id"] for item in data}) == len(data)
    assert all(item["active_users"] >= item["analysts"] >= 0 for item in data)
    assert all(item["tickets_total"] >= item["tickets_open"] >= 0 for item in data)
    assert all("email" not in item for item in data)


@pytest.mark.parametrize("role", ["admin", "analista"])
def test_ai_overview_totals(role):
    auth(role)
    response = client.get("/ai/overview")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["suggestions_total"] == data["pending"] + data["approved"] + data["rejected"]
    assert data["suggestions_total"] >= data["ollama"] + data["demonstration"] + data["external_models"]
