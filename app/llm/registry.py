
from typing import Protocol

class LLMProvider(Protocol):

    async def generate(self, prompt: str) -> str:
        ...

class LLMProviderRegistry:

    def __init__(self, providers: dict[str, LLMProvider]):
        self.providers = providers

    def get_provider(self, name: str) -> LLMProvider:
        provider = self.providers.get(name)

        if provider is None:
            raise ValueError(
                f"Unsupported or unavailable LLM provider: {name}"
            )

        return provider
