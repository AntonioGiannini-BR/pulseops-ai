"""Validações de inicialização de ambiente e proteção de endpoints em produção."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_missing_or_short_jwt():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            _env_file=None,
            app_environment="production",
            jwt_secret_key="short",
            database_url="postgresql+psycopg://user:pass@localhost:5432/database",
        )


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            _env_file=None,
            app_environment="production",
            jwt_secret_key="ALTERE_ISTO_GERE_UM_SEGREDO_ALEATORIO_COM_32_CARACTERES",
            database_url="postgresql+psycopg://user:pass@localhost:5432/database",
        )


def test_production_needs_explicit_database():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(
            _env_file=None,
            app_environment="production",
            jwt_secret_key="a" * 40,
            database_url="postgresql+psycopg:///pulseops_ai",
        )


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(
            _env_file=None,
            app_environment="production",
            jwt_secret_key="a" * 40,
            database_url="postgresql+psycopg://user:pass@localhost:5432/database",
            cors_origins="*",
        )


def test_ollama_base_url_limited_to_local_or_internal_hosts():
    with pytest.raises(ValidationError, match="ollama_base_url"):
        Settings(_env_file=None, ollama_base_url="https://example.com/llm")
    valid = Settings(_env_file=None, ollama_base_url="http://ollama:11434")
    assert valid.ollama_base_url == "http://ollama:11434"
