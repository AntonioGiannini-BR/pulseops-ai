import pytest
from app.api.deps import get_current_user
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@pulseops.example", "role": "analista"}
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)


def test_list_tickets():

    response = client.get("/tickets/")

    assert response.status_code == 200

    assert isinstance(response.json(), list)


def test_get_ticket_not_found():

    response = client.get("/tickets/999999")

    assert response.status_code == 404

    assert response.json() == {

        "detail": "Chamado não encontrado"

    }


def test_get_ticket_existing():

    response = client.get("/tickets/")

    assert response.status_code == 200

    tickets = response.json()

    assert len(tickets) > 0

    ticket_id = tickets[0]["id"]

    response = client.get(f"/tickets/{ticket_id}")

    assert response.status_code == 200

    assert response.json()["id"] == ticket_id

def test_create_ticket_invalid_priority():
    response = client.post(
        "/tickets/",
        json={
            "title": "Teste de prioridade",
            "description": "Verificar validação",
            "requester_id": 22,
            "category_id": 19,
            "priority": "urgente"
        }
    )

    assert response.status_code == 422

def test_create_ticket_empty_title():
    response = client.post(
        "/tickets/",
        json={
            "title": "",
            "description": "Verificar título obrigatório",
            "requester_id": 22,
            "category_id": 19,
            "priority": "alta"
        }
    )

    assert response.status_code == 422


def test_update_ticket_success():
    tickets = client.get("/tickets/").json()
    assert len(tickets) > 0

    ticket_id = tickets[0]["id"]
    original_status = tickets[0]["status"]
    original_priority = tickets[0]["priority"]

    try:
        response = client.patch(
            f"/tickets/{ticket_id}",
            json={
                "status": "em_atendimento",
                "priority": "alta",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "em_atendimento"
        assert response.json()["priority"] == "alta"

        check = client.get(f"/tickets/{ticket_id}")
        assert check.status_code == 200
        assert check.json()["status"] == "em_atendimento"
        assert check.json()["priority"] == "alta"

    finally:
        client.patch(
            f"/tickets/{ticket_id}",
            json={
                "status": original_status,
                "priority": original_priority,
            },
        )


def test_update_ticket_not_found():
    response = client.patch(
        "/tickets/999999",
        json={"status": "resolvido"},
    )
    assert response.status_code == 404


def test_update_ticket_invalid_status():
    response = client.patch(
        "/tickets/999999",
        json={"status": "cancelado"},
    )
    assert response.status_code == 422


def test_update_ticket_empty_body():
    response = client.patch(
        "/tickets/999999",
        json={},
    )
    assert response.status_code == 422
