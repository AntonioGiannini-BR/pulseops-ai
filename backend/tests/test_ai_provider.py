"""Testes isolados do adaptador externo: nenhuma chamada real à rede."""

import json

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.services.ai_triage import (
    InvalidProviderResponse,
    ProviderUnavailable,
    generate_proposal,
)


CATEGORIES = [
    {"id": 1, "name": "Infraestrutura"},
    {"id": 2, "name": "Acessos"},
]


class FakeResponse:
    def __init__(self, category_id=2):
        self.category_id = category_id

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "suggested_priority": "alta",
                        "suggested_category_id": self.category_id,
                        "summary": "Solicitação de acesso",
                        "rationale": "Usuário sem acesso ao sistema",
                    }),
                },
            }],
        }


def test_openai_valida_resposta_e_minimiza_dados(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("chave-apenas-teste"))
    monkeypatch.setattr(settings, "ai_model", "modelo-teste")

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr("app.services.ai_triage.httpx.post", fake_post)
    result = generate_proposal(
        title="Falha no acesso de alice@empresa.example",
        description="Não consigo acessar o sistema.",
        current_category_id=1,
        categories=CATEGORIES,
    )
    assert result.model_name == "modelo-teste"
    assert result.proposal.suggested_priority == "alta"
    assert result.proposal.suggested_category_id == 2

    url, kwargs = calls[0]
    assert url == "https://api.openai.com/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer chave-apenas-teste"
    user_payload = kwargs["json"]["messages"][1]["content"]
    assert "alice@empresa.example" not in user_payload
    assert "[email]" in user_payload
    assert "chave-apenas-teste" not in user_payload


def test_openai_rejeita_categoria_inventada(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("chave-apenas-teste"))
    monkeypatch.setattr(
        "app.services.ai_triage.httpx.post",
        lambda *args, **kwargs: FakeResponse(category_id=999),
    )
    with pytest.raises(InvalidProviderResponse):
        generate_proposal(
            title="Teste",
            description="Descrição",
            current_category_id=1,
            categories=CATEGORIES,
        )


def test_openai_sem_chave_nao_usa_rede(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    def no_network(*args, **kwargs):
        raise AssertionError("Rede não deveria ser acessada")

    monkeypatch.setattr("app.services.ai_triage.httpx.post", no_network)
    with pytest.raises(ProviderUnavailable):
        generate_proposal(
            title="Teste",
            description="Descrição",
            current_category_id=1,
            categories=CATEGORIES,
        )
