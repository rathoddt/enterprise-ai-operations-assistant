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
    
    foundry_openai_endpoint: str | None = None
    foundry_openai_api_key: str | None = None
    foundry_openai_deployment: str = "gpt-5"

    foundry_anthropic_endpoint: str | None = None
    foundry_anthropic_api_key: str | None = None
    foundry_anthropic_deployment: str = "claude-sonnet-5-5"    
    


settings = Settings()