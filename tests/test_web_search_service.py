import asyncio

from app.services.web_search import WebSearchService
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)

from unittest.mock import AsyncMock
from uuid import uuid4

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

def test_web_search_service_persists_success_event():

    async def run_test():

        mock_repository = AsyncMock()
        request_event_id = uuid4()

        service = WebSearchService(
            provider=MockWebSearchProvider(),
            event_repository=mock_repository,
        )

        request = WebSearchRequest(
            query="Azure AI Foundry",
            max_results=5,
        )

        response = await service.search(
            request,
            request_event_id=request_event_id,
        )

        # Verify search response
        assert response.provider == "mock"
        assert len(response.results) == 1

        # Verify execution event persistence
        mock_repository.record_web_search_execution.assert_awaited_once()

        call = mock_repository.record_web_search_execution.await_args
        assert call.kwargs["event_id"] == request_event_id
        assert call.kwargs["provider"] == "mock"
        assert call.kwargs["status"] == "success"
        assert call.kwargs["result_count"] == 1
        assert call.kwargs["answer_available"] is False
        assert call.kwargs["response_time"] >= 0

    asyncio.run(run_test())

def test_web_search_service_persists_failure_event():

    class FailingWebSearchProvider:

        async def search(self, request: WebSearchRequest):
            raise RuntimeError("Mock Tavily API failure")

    async def run_test():

        mock_repository = AsyncMock()
        request_event_id = uuid4()

        service = WebSearchService(
            provider=FailingWebSearchProvider(),
            event_repository=mock_repository,
        )

        request = WebSearchRequest(
            query="Azure AI Foundry",
            max_results=5,
        )

        try:
            await service.search(
                request,
                request_event_id=request_event_id,
            )
            assert False, "Expected RuntimeError was not raised"

        except RuntimeError as exc:
            assert str(exc) == "Mock Tavily API failure"

        mock_repository.record_web_search_execution.assert_awaited_once()

        call = mock_repository.record_web_search_execution.await_args

        assert call.kwargs["event_id"] == request_event_id
        assert call.kwargs["status"] == "error"
        assert call.kwargs["error_type"] == "RuntimeError"
        assert call.kwargs["response_time"] >= 0

    asyncio.run(run_test())