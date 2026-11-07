from typing import Protocol
from app.llm.schemas import LLMResult

async def generate(
    self,
    system_prompt: str,
    user_prompt: str,
) -> LLMResult:
    ...

# ------------------------- v0 -------------------
# class LLMProvider(Protocol):

#     async def generate(self, prompt: str) -> LLMResult:
#         ...