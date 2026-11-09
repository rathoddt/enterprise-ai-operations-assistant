import asyncio

from app.web_search.providers.tavily_provider import TavilySearchProvider
from app.web_search.schemas import WebSearchRequest


async def run_search():
    provider = TavilySearchProvider()

    request = WebSearchRequest(
        query="Latest developments in enterprise AI agents",
        max_results=5,
        search_depth="basic",
        topic="general",
    )

    response = await provider.search(request)

    print("\nProvider:", response.provider)
    print("Query:", response.query)
    print("Response time:", response.response_time)
    print("Number of results:", len(response.results))

    for index, result in enumerate(response.results, start=1):
        print(f"\n{index}. {result.title}")
        print("URL:", result.url)
        print("Score:", result.score)
        print("Content:", result.content[:300])


def test_tavily_search_live():
    asyncio.run(run_search())

if __name__ == "__main__":
    asyncio.run(run_search())