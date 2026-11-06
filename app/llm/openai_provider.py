from openai import AsyncOpenAI, APIError
from app.core.exceptions import LLMProviderError


class OpenAIProvider:

    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=(
                    "You are an Enterprise AI Operations Assistant. "
                    "Provide accurate, concise and professional answers."
                ),
                input=prompt,
            )

            return response.output_text

        except APIError as exc:
            raise LLMProviderError(
                message="OpenAI request failed.",
                code="OPENAI_ERROR",
            ) from exc