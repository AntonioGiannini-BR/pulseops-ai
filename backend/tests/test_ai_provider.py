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


class FakeOllamaResponse:
    def __init__(self, category_id=2, content=None):
        self.category_id = category_id
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        content = self.content or json.dumps({
            "suggested_priority": "alta",
            "suggested_category_id": self.category_id,
            "summary": "Falha de acesso",
            "rationale": "O acesso está bloqueado.",
        })
        return {"message": {"content": content}}


def test_ollama_usa_loopback_json_e_mascara_dados(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "qwen2.5:3b")
    monkeypatch.setattr(settings, "ollama_timeout_seconds", 120)
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeOllamaResponse()

    monkeypatch.setattr("app.services.ai_triage.httpx.post", fake_post)
    result = generate_proposal(
        title="Acesso de alice@empresa.example bloqueado",
        description="Não consigo acessar o portal.",
        current_category_id=1,
        categories=CATEGORIES,
    )
    assert result.model_name == "ollama/qwen2.5:3b"
    assert result.proposal.suggested_category_id == 2
    url, kwargs = calls[0]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert kwargs["json"]["stream"] is False
    assert kwargs["json"]["format"] == "json"
    assert kwargs["json"]["model"] == "qwen2.5:3b"
    assert kwargs["timeout"] == 120
    prompt = kwargs["json"]["messages"][1]["content"]
    assert "alice@empresa.example" not in prompt
    assert "[email]" in prompt


def test_ollama_rejeita_categoria_nao_permitida(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(
        "app.services.ai_triage.httpx.post",
        lambda *args, **kwargs: FakeOllamaResponse(category_id=999),
    )
    with pytest.raises(InvalidProviderResponse):
        generate_proposal(
            title="Teste", description="Descrição",
            current_category_id=1, categories=CATEGORIES,
        )


def test_ollama_rejeita_resposta_invalida(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(
        "app.services.ai_triage.httpx.post",
        lambda *args, **kwargs: FakeOllamaResponse(content='{"foo":"bar"}'),
    )
    with pytest.raises(InvalidProviderResponse):
        generate_proposal(
            title="Teste", description="Descrição",
            current_category_id=1, categories=CATEGORIES,
        )


def test_ollama_indisponivel_nao_faz_fallback_silencioso(monkeypatch):
    import httpx

    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("indisponível")

    monkeypatch.setattr("app.services.ai_triage.httpx.post", unavailable)
    with pytest.raises(ProviderUnavailable, match="Ollama local indisponível"):
        generate_proposal(
            title="Teste", description="Descrição",
            current_category_id=1, categories=CATEGORIES,
        )
