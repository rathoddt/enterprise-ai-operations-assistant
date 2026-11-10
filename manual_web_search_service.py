import asyncio

from app.api.dependencies import get_web_search_service
from app.core.observability import get_langfuse_client
from app.web_search.schemas import WebSearchRequest


async def main():
    service = get_web_search_service()

    request = WebSearchRequest(
        query="Latest features of Azure AI Foundry",
        max_results=5,
        search_depth="basic",
        topic="general",
        include_answer=True,
    )

    response = await service.search(request)

    print("\nProvider:", response.provider)
    print("Results:", len(response.results))
    print("Response time:", response.response_time)
    print("Answer:", response.answer)

    for index, result in enumerate(response.results, start=1):
        print(f"\n{index}. {result.title}")
        print("URL:", result.url)

    langfuse = get_langfuse_client()
    if langfuse:
        langfuse.flush()
        print("\nLangfuse events flushed.")


if __name__ == "__main__":
    asyncio.run(main())