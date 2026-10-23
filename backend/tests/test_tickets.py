from fastapi.testclient import TestClient

from app.main import app

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
