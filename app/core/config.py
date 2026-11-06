from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Enterprise AI Operations Assistant"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    log_level: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5-5"


settings = Settings()