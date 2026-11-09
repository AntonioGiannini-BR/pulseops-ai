from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg:///pulseops_ai"
    )

    # Modo mock é uma heurística demonstrativa, não um modelo de IA.
    ai_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: SecretStr | None = None
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = Field(default=10, ge=2, le=30)

    jwt_secret_key: str | None = None
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        extra="ignore",
    )


settings = Settings()
