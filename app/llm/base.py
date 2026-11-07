from typing import Protocol

from app.llm.schemas import LLMResult


class LLMProvider(Protocol):

    async def generate(self, prompt: str) -> LLMResult:
        ...