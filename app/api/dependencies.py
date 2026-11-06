from functools import lru_cache

from app.core.config import Settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.registry import LLMProviderRegistry
from app.services.assistant import AssistantService


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_assistant_service() -> AssistantService:
    settings = get_settings()

    # Register available LLM providers
    providers = {}

    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(
            settings.openai_api_key,
            settings.openai_model,
        )

    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(
            settings.anthropic_api_key,
            settings.anthropic_model,
        )

    # Create provider registry
    registry = LLMProviderRegistry(providers)

    return AssistantService(provider_registry=registry)

# from app.services.assistant import AssistantService


# def get_assistant_service() -> AssistantService:

#     return AssistantService()