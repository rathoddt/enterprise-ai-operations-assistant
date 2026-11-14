from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Enterprise AI Operations Assistant"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    # log_level: str = "DEBUG"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    llm_max_input_tokens: int = 10000
    llm_max_output_tokens: int = 1500
    # LLM request reliability
    llm_request_timeout_seconds: int = 180

    # Database persistence reliability
    stale_event_threshold_seconds: int = 300
    event_heartbeat_interval_seconds: int = 60
    # event_heartbeat_interval_seconds: int = 5
    stale_recovery_interval_seconds: int = 60
    persistence_retry_attempts: int = 3
    persistence_retry_delay_seconds: float = 1.0
    

    foundry_openai_endpoint: str | None = None
    foundry_openai_api_key: str | None = None
    foundry_openai_deployment: str = "gpt-5"

    foundry_anthropic_endpoint: str | None = None
    foundry_anthropic_api_key: str | None = None
    foundry_anthropic_deployment: str = "claude-sonnet-5-5"    

    # Langfuse Observability
    langfuse_secret_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_base_url: str = "http://localhost:3000"

    tavily_api_key: str | None = None

    # PostgreSQL configuration
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433
    postgres_db: str = "eaoa_analytics"
    postgres_user: str = "eaoa_app"
    postgres_password: str
    


settings = Settings()