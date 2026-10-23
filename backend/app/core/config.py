from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg:///pulseops_ai"
    )

    jwt_secret_key: str | None = None
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
