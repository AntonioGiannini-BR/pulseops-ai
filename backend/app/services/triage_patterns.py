"""Padrões GoF usados pela triagem supervisionada do PulseOps AI.

Factory Method: cada fábrica concreta cria uma Strategy.
Strategy: encapsula o algoritmo de consulta a cada provedor.
Facade: expõe uma operação única e valida a saída antes do consumo.

A decisão humana e a transação no banco continuam na API.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from app.services.ai_triage import (
    GeneratedProposal,
    InvalidProviderResponse,
    ProviderUnavailable,
)


class TriageStrategy(Protocol):
    """Contrato de classificação independente da tecnologia do provedor."""

    def propose(
        self, *, title: str, description: str,
        current_category_id: int, categories: list[dict],
    ) -> GeneratedProposal:
        ...


class MockTriageStrategy:
    def propose(self, *, title, description, current_category_id, categories):
        from app.services.ai_triage import _mock_proposal
        return _mock_proposal(title, description, categories, current_category_id)


class OllamaTriageStrategy:
    def propose(self, *, title, description, current_category_id, categories):
        from app.services.ai_triage import _ollama_proposal
        return _ollama_proposal(
            title=title, description=description,
            current_category_id=current_category_id, categories=categories,
        )


class OpenAITriageStrategy:
    def propose(self, *, title, description, current_category_id, categories):
        from app.services.ai_triage import _openai_proposal
        return _openai_proposal(
            title=title, description=description,
            current_category_id=current_category_id, categories=categories,
        )


class TriageFactory(ABC):
    """Creator do Factory Method: a fábrica concreta escolhe a implementação."""

    @abstractmethod
    def create_strategy(self) -> TriageStrategy:
        raise NotImplementedError


class MockTriageFactory(TriageFactory):
    def create_strategy(self) -> TriageStrategy:
        return MockTriageStrategy()


class OllamaTriageFactory(TriageFactory):
    def create_strategy(self) -> TriageStrategy:
        return OllamaTriageStrategy()


class OpenAITriageFactory(TriageFactory):
    def create_strategy(self) -> TriageStrategy:
        return OpenAITriageStrategy()


def factory_for(provider: str) -> TriageFactory:
    """Seleção de fábrica feita na borda do sistema, não na lógica da fachada."""
    factories: dict[str, type[TriageFactory]] = {
        "mock": MockTriageFactory,
        "ollama": OllamaTriageFactory,
        "openai": OpenAITriageFactory,
    }
    try:
        return factories[provider]()
    except KeyError as exc:
        raise ProviderUnavailable("Provedor de IA não suportado") from exc


class TriageFacade:
    """Orquestra o contrato da triagem, sem persistência nem aprovação automática."""

    def __init__(self, factory: TriageFactory) -> None:
        self._factory = factory

    def generate(
        self, *, title: str, description: str,
        current_category_id: int, categories: list[dict],
    ) -> GeneratedProposal:
        if not categories:
            raise InvalidProviderResponse("Nenhuma categoria permitida para triagem")
        generated = self._factory.create_strategy().propose(
            title=title, description=description,
            current_category_id=current_category_id, categories=categories,
        )
        allowed_ids = {category["id"] for category in categories}
        if generated.proposal.suggested_category_id not in allowed_ids:
            raise InvalidProviderResponse("Provedor indicou uma categoria inválida")
        return generated
