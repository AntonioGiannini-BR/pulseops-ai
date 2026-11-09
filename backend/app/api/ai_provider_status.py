"""Expõe somente a configuração do provedor; nunca revela a chave de API."""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_roles
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Triage"])


class AIProviderStatus(BaseModel):
    provider: Literal["mock", "openai"]
    configured: bool
    model: str | None


@router.get("/status", response_model=AIProviderStatus)
def get_ai_provider_status(
    _current_user: dict = Depends(require_roles("admin", "analista")),
):
    """Indica presença de configuração, não validade da chave ou conectividade."""
    configured = settings.ai_provider == "mock" or bool(
        settings.openai_api_key
        and settings.openai_api_key.get_secret_value().strip()
    )
    return AIProviderStatus(
        provider=settings.ai_provider,
        configured=configured,
        model=settings.ai_model if settings.ai_provider == "openai" else None,
    )
