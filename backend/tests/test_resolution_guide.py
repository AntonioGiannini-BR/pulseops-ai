"""Testes de geração de planos: sem chamadas reais à rede."""

import json

import httpx
import pytest

from app.core.config import settings
from app.services.ai_triage import InvalidProviderResponse, ProviderUnavailable
from app.services.resolution_guide import generate_resolution_guide


VALID_GUIDE = {
    "probable_cause": "Possível falha de permissão no portal.",
    "steps": ["Confirmar se a conta está ativa.", "Conferir o perfil com o administrador."],
    "verification": "Pedir ao solicitante para testar o acesso.",
    "requester_reply": "Estamos verificando o acesso e retornaremos com uma atualização.",
}


class FakeResponse:
    def __init__(self, content=None):
        self.content = content if content is not None else json.dumps(VALID_GUIDE)

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": self.content}}


def test_ollama_guia_estruturado_e_minimizacao(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "qwen2.5:3b")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr("app.services.resolution_guide.httpx.post", fake_post)
    result = generate_resolution_guide(
        title="Acesso bloqueado de pessoa@empresa.example",
        description="Mensagem de permissão negada.",
        category="Acessos",
    )
    assert result.model_name == "ollama/qwen2.5:3b"
    assert len(result.guide.steps) == 2
    url, kwargs = calls[0]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert kwargs["json"]["stream"] is False
    assert kwargs["json"]["format"] == "json"
    assert "pessoa@empresa.example" not in kwargs["json"]["messages"][1]["content"]


def test_guia_invalido_nao_e_executado(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(
        "app.services.resolution_guide.httpx.post",
        lambda *args, **kwargs: FakeResponse(content='{"steps": []}'),
    )
    with pytest.raises(InvalidProviderResponse):
        generate_resolution_guide(title="Falha", description="Teste", category="Acessos")


def test_ollama_indisponivel_retorna_erro(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def no_connection(*args, **kwargs):
        raise httpx.ConnectError("indisponível")

    monkeypatch.setattr("app.services.resolution_guide.httpx.post", no_connection)
    with pytest.raises(ProviderUnavailable):
        generate_resolution_guide(title="Falha", description="Teste", category="Acessos")


def test_mock_nao_finge_ser_modelo(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")
    result = generate_resolution_guide(title="Falha", description="Teste", category="Acessos")
    assert result.model_name == "demo-guia-local"
    assert len(result.guide.steps) >= 2
