from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider


class LLMProviderRegistry:

    def __init__(self, providers: dict):
        self.providers = providers

    def get_provider(self, name: str):
        provider = self.providers.get(name)

        if provider is None:
            raise ValueError(f"Unsupported LLM provider: {name}")

        return provider