from typing import Protocol
from app.llm.schemas import LLMResult

class LLMProvider(Protocol):

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
    ) -> LLMResult:
        ...

