import asyncio

from app.services.web_search import WebSearchService
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)


class MockWebSearchProvider:

    async def search(self, request: WebSearchRequest) -> WebSearchResponse:
        return WebSearchResponse(
            query=request.query,
            provider="mock",
            results=[
                WebSearchResult(
                    title="Azure AI Foundry Documentation",
                    url="https://example.com/azure-ai",
                    content="Azure AI Foundry documentation.",
                    score=0.95,
                )
            ],
            response_time=0.5,
        )


def test_web_search_service_returns_results():

    async def run_test():
        service = WebSearchService(
            provider=MockWebSearchProvider()
        )

        request = WebSearchRequest(
            query="Azure AI Foundry",
            max_results=5,
        )

        response = await service.search(request)

        assert response.provider == "mock"
        assert response.query == "Azure AI Foundry"
        assert len(response.results) == 1
        assert response.results[0].title == "Azure AI Foundry Documentation"

    asyncio.run(run_test())