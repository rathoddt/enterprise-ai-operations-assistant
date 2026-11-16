
from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingService:

    def __init__(self):
        if not settings.foundry_openai_endpoint:
            raise ValueError("Foundry OpenAI endpoint is not configured")

        if not settings.foundry_openai_api_key:
            raise ValueError("Foundry OpenAI API key is not configured")

        self.deployment = settings.foundry_openai_embedding_deployment

        self.client = AsyncOpenAI(
            base_url=settings.foundry_openai_endpoint,
            api_key=settings.foundry_openai_api_key,
            timeout=settings.llm_request_timeout_seconds,
            max_retries=0,
        )

    async def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        response = await self.client.embeddings.create(
            model=self.deployment,
            input=text,
            encoding_format="float",
        )

        return response.data[0].embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if any(not text or not text.strip() for text in texts):
            raise ValueError("Input texts cannot contain empty values")

        response = await self.client.embeddings.create(
            model=self.deployment,
            input=texts,
            encoding_format="float",
        )

        ordered_data = sorted(response.data, key=lambda item: item.index)

        return [item.embedding for item in ordered_data]

    async def close(self) -> None:
        await self.client.close()
