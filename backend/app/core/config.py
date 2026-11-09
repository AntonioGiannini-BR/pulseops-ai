from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    jwt_secret_key: str | None = None
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        extra="ignore",
    )


settings = Settings()
