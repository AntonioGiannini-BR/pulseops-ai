from pathlib import Path
from typing import Literal

from pydantic import model_validator

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_environment: Literal["development", "production"] = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = (
        "postgresql+psycopg:///pulseops_ai"
    )

    # mock: regras locais; openai: API externa; ollama: modelo local.
    ai_provider: Literal["mock", "openai", "ollama"] = "mock"
    openai_api_key: SecretStr | None = None
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = Field(default=10, ge=2, le=30)
    ollama_model: str = Field(default="qwen2.5:3b", min_length=1, max_length=100)
    ollama_timeout_seconds: float = Field(default=120, ge=10, le=300)
    ollama_base_url: Literal[
        "http://127.0.0.1:11434",
        "http://localhost:11434",
        "http://host.docker.internal:11434",
        "http://ollama:11434",
    ] = "http://127.0.0.1:11434"

    jwt_secret_key: str | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_minutes: int = 30

    @model_validator(mode="after")
    def check_production_secrets(self):
        if self.app_environment == "production":
            if not self.jwt_secret_key or len(self.jwt_secret_key) < 32 or "ALTERE_" in self.jwt_secret_key:
                raise ValueError("JWT_SECRET_KEY deve ser aleatória e ter pelo menos 32 caracteres em produção")
            if self.database_url == "postgresql+psycopg:///pulseops_ai":
                raise ValueError("DATABASE_URL deve ser definido explicitamente em produção")
            if any(origin.strip() == "*" for origin in self.cors_origins.split(",")):
                raise ValueError("CORS_ORIGINS não pode conter '*' em produção")
        return self

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        extra="ignore",
    )


settings = Settings()
