from functools import lru_cache

from app.core.config import Settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.registry import LLMProviderRegistry
from app.services.assistant import AssistantService

from app.services.web_search import WebSearchService
from app.web_search.providers.tavily_provider import TavilySearchProvider

from app.web_search.router import SearchRouter
from app.db.repositories import EventRepository

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

    # registry = LLMProviderRegistry(providers)

    # return AssistantService(provider_registry=registry)

    registry = LLMProviderRegistry(providers)

    search_router = SearchRouter()
    web_search_service = get_web_search_service()

    # return AssistantService(
    #     provider_registry=registry,
    #     search_router=search_router,
    #     web_search_service=web_search_service,
    # )
    return AssistantService(
        provider_registry=registry,
        search_router=search_router,
        web_search_service=web_search_service,
        event_repository=EventRepository(),
    )

@lru_cache
def get_web_search_service() -> WebSearchService:
    settings = get_settings()

    if not settings.tavily_api_key:
        raise RuntimeError(
            "Tavily API key is not configured. Check your .env settings."
        )

    provider = TavilySearchProvider()

    return WebSearchService(provider=provider)
