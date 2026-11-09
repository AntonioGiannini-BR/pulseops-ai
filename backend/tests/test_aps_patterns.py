"""APS: contrato de triagem com padrões e teste primeiro (TDD)."""

import pytest

from app.services.ai_triage import GeneratedProposal, InvalidProviderResponse, ProviderUnavailable, TriageProposal
from app.services.triage_patterns import (
    TriageFacade, MockTriageFactory, OllamaTriageFactory, OpenAITriageFactory,
    factory_for,
)


CATEGORIES = [{"id": 1, "name": "Sistemas"}, {"id": 2, "name": "Equipamentos"}]


def test_factory_method_seleciona_estrategias():
    assert isinstance(factory_for("mock"), MockTriageFactory)
    assert isinstance(factory_for("ollama"), OllamaTriageFactory)
    assert isinstance(factory_for("openai"), OpenAITriageFactory)
    assert type(factory_for("mock").create_strategy()).__name__ == "MockTriageStrategy"
    assert type(factory_for("ollama").create_strategy()).__name__ == "OllamaTriageStrategy"
    assert type(factory_for("openai").create_strategy()).__name__ == "OpenAITriageStrategy"


def test_facade_rejeita_categorias_vazias_antes_de_chamar_provedor(monkeypatch):
    calls = []
    monkeypatch.setattr("app.services.ai_triage._ollama_proposal", lambda **kw: calls.append(kw))
    with pytest.raises(InvalidProviderResponse, match="categoria"):
        TriageFacade(OllamaTriageFactory()).generate(
            title="Erro", description="Sem acesso", current_category_id=1, categories=[]
        )
    assert calls == []


def test_facade_rejeita_categoria_inventada_pelo_provedor(monkeypatch):
    monkeypatch.setattr("app.services.ai_triage._ollama_proposal", lambda **kw: GeneratedProposal(
        proposal=TriageProposal(
            suggested_priority="alta", suggested_category_id=999,
            summary="Erro de acesso", rationale="Possível indisponibilidade",
        ),
        model_name="ollama/teste",
    ))
    with pytest.raises(InvalidProviderResponse, match="categoria"):
        TriageFacade(OllamaTriageFactory()).generate(
            title="Erro", description="Sem acesso", current_category_id=1, categories=CATEGORIES
        )


def test_facade_integra_estrategia_mock_sem_alterar_dados():
    original = [dict(category) for category in CATEGORIES]
    generated = TriageFacade(MockTriageFactory()).generate(
        title="Impressora parou", description="O setor inteiro está parado",
        current_category_id=1, categories=CATEGORIES,
    )
    assert generated.proposal.suggested_category_id == 2
    assert generated.proposal.suggested_priority == "critica"
    assert generated.model_name == "demo-regras-locais"
    assert CATEGORIES == original


def test_factory_rejeita_provedor_nao_suportado():
    with pytest.raises(ProviderUnavailable):
        factory_for("desconhecido")
