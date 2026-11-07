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

    providers = {}

    if settings.foundry_openai_endpoint and settings.foundry_openai_api_key:
        providers["openai"] = OpenAIProvider(
            endpoint=settings.foundry_openai_endpoint,
            api_key=settings.foundry_openai_api_key,
            deployment=settings.foundry_openai_deployment,
        )

    if settings.foundry_anthropic_endpoint and settings.foundry_anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(
            endpoint=settings.foundry_anthropic_endpoint,
            api_key=settings.foundry_anthropic_api_key,
            deployment=settings.foundry_anthropic_deployment,
        )

    if not providers:
        raise RuntimeError(
            "No Foundry providers configured. Check your .env settings."
        )

    registry = LLMProviderRegistry(providers)

    return AssistantService(provider_registry=registry)
# --------------------- v1 ----------------------------
# from functools import lru_cache

# from app.core.config import Settings
# from app.llm.openai_provider import OpenAIProvider
# from app.llm.anthropic_provider import AnthropicProvider
# from app.llm.registry import LLMProviderRegistry
# from app.services.assistant import AssistantService


# @lru_cache
# def get_settings() -> Settings:
#     return Settings()


# @lru_cache
# def get_assistant_service() -> AssistantService:
#     settings = get_settings()

#     # Register available LLM providers
#     providers = {}

#     if settings.openai_api_key:
#         providers["openai"] = OpenAIProvider(
#             settings.openai_api_key,
#             settings.openai_model,
#         )

#     if settings.anthropic_api_key:
#         providers["anthropic"] = AnthropicProvider(
#             settings.anthropic_api_key,
#             settings.anthropic_model,
#         )

#     # Create provider registry
#     registry = LLMProviderRegistry(providers)

#     return AssistantService(provider_registry=registry)

# ------------------------ v0 -------------------
# from app.services.assistant import AssistantService


# def get_assistant_service() -> AssistantService:

#     return AssistantService()