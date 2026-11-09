
import asyncio

from app.api.dependencies import get_assistant_service
from app.core.observability import get_langfuse_client
from app.web_search.router import SearchRouter


async def main():

    assistant = get_assistant_service()

    # Use the actual configured OpenAI provider.
    provider = assistant.provider_registry.get_provider("openai")

    router = SearchRouter()

    query = "Can I use Gemini 3 with Vertex AI?"

    decision = await router.route(
        query=query,
        provider=provider,
    )

    print("\nSearch routing decision:")
    print(decision.model_dump())


if __name__ == "__main__":

    try:
        asyncio.run(main())

    finally:
        langfuse = get_langfuse_client()

        if langfuse:
            langfuse.flush()
