from anthropic import AsyncAnthropic, APIError
from app.core.exceptions import LLMProviderError


class AnthropicProvider:

    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=(
                    "You are an Enterprise AI Operations Assistant. "
                    "Provide accurate, concise and professional answers."
                ),
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            return "".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

        except APIError as exc:
            raise LLMProviderError(
                message="Anthropic request failed.",
                code="ANTHROPIC_ERROR",
            ) from exc