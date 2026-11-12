import uuid
import pytest
import asyncio
from unittest.mock import AsyncMock
# from urllib import response

from app.llm.registry import LLMProviderRegistry
from app.models.schemas import ChatRequest
from app.services.assistant import AssistantService
from app.llm.schemas import LLMResult
from app.core.config import settings
from app.web_search.routing import SearchDecision
from app.web_search.schemas import WebSearchResponse, WebSearchResult

def test_assistant_service_with_mock_llm():

    mock_provider = AsyncMock()

    mock_provider.generate.return_value = LLMResult(
            answer="Mock AI response",
            provider="openai",
            model="gpt-5",
            input_tokens=10,
            output_tokens=20,
            request_id="mock-request-123",
            response_id="mock-response-456",
            status="success",
            finish_reason="end_turn",
            is_truncated=False, 
            incomplete_reason=None,
        )

    registry = LLMProviderRegistry({
        "openai": mock_provider
    })

    service = AssistantService(
        provider_registry=registry
    )

    request = ChatRequest(
        question="What is our payment policy?",
        provider="openai"
    )

    response = asyncio.run(
        service.process_request(request)
    )

    assert response.answer == (
        "Mock AI response"
    )


    assert response.status == "success"

    # Verify both prompts were passed to the LLM provider.
    mock_provider.generate.assert_awaited_once_with(
        system_prompt=(
            "Provide a concise, well-structured answer. "
            "Use approximately 400–600 words unless the question "
            "requires more detail. Avoid unnecessary repetition."
        ),
        user_prompt="What is our payment policy?",
        max_output_tokens=settings.llm_max_output_tokens,
    )

    # Verify response metadata.
    assert response.metadata.request_id == "mock-request-123"
    assert response.metadata.response_id == "mock-response-456"
    assert response.metadata.finish_reason == "end_turn"
    assert response.metadata.is_truncated is False
    assert response.metadata.incomplete_reason is None



def test_assistant_service_with_search_and_event_persistence():

    async def run_test():

        # Mock LLM provider
        mock_provider = AsyncMock()
        mock_provider.generate.return_value = LLMResult(
            answer="Mock answer based on web search.",
            provider="openai",
            model="gpt-5",
            input_tokens=100,
            output_tokens=50,
            request_id="mock-request-789",
            response_id="mock-response-789",
            status="success",
            finish_reason="end_turn",
            is_truncated=False,
            incomplete_reason=None,
        )

        registry = LLMProviderRegistry({
            "openai": mock_provider
        })

        # Mock search router
        mock_search_router = AsyncMock()
        mock_search_router.route.return_value = SearchDecision(
            requires_search=True,
            reason="The query requires recent information.",
            search_query="Latest Azure AI Foundry developments",
            search_type="general",
            freshness="live",
            confidence=0.95,
            decision_source="rules",
        )

        # Mock web search service
        mock_web_search_service = AsyncMock()
        mock_web_search_service.search.return_value = WebSearchResponse(
            query="Latest Azure AI Foundry developments",
            provider="tavily",
            answer="Recent Azure AI Foundry updates.",
            results=[
                WebSearchResult(
                    title="Azure AI Foundry Updates",
                    url="https://example.com/azure-ai",
                    content="Latest platform developments.",
                    score=0.95,
                )
            ],
            response_time=1.2,
        )

        # Mock event repository
        mock_event_repository = AsyncMock()

        service = AssistantService(
            provider_registry=registry,
            search_router=mock_search_router,
            web_search_service=mock_web_search_service,
            event_repository=mock_event_repository,
        )

        request = ChatRequest(
            question="What are the latest Azure AI Foundry developments?",
            provider="openai",
        )

        response = await service.process_request(request)

        # Verify assistant response
        assert response.status == "success"
        assert response.answer == "Mock answer based on web search."

        # Verify search routing
        mock_search_router.route.assert_awaited_once()

        # Verify web search execution was requested
        mock_web_search_service.search.assert_awaited_once()

        # Extract the parent request UUID
        create_call = (
            mock_event_repository.create_assistant_request.await_args
        )
        request_event_id = create_call.kwargs["event_id"]

        # Verify search decision uses the same UUID
        decision_call = (
            mock_event_repository.record_search_decision.await_args
        )
        assert decision_call.kwargs["event_id"] == request_event_id

        # Verify the same UUID is passed to WebSearchService
        web_search_call = (
            mock_web_search_service.search.await_args
        )
        assert web_search_call.kwargs["request_event_id"] == request_event_id

        # Verify final assistant request update
        update_call = (
            mock_event_repository.update_assistant_request.await_args
        )
        assert update_call.kwargs["event_id"] == request_event_id
        assert update_call.kwargs["status"] == "success"

        # Verify search context reaches the LLM
        llm_call = mock_provider.generate.await_args
        assert "Recent Azure AI Foundry updates." in llm_call.kwargs["user_prompt"]

    asyncio.run(run_test())


@pytest.mark.parametrize("should_fail", [False, True])
def test_heartbeat_is_cancelled_after_request_completion(should_fail):

    async def run_test():

        heartbeat_started = asyncio.Event()
        heartbeat_stopped = asyncio.Event()

        # Simulate an LLM request that waits until heartbeat starts.
        async def generate_response(**kwargs):
            await heartbeat_started.wait()

            if should_fail:
                raise RuntimeError("Simulated LLM failure")

            return LLMResult(
                answer="Mock heartbeat test response",
                provider="openai",
                model="gpt-5",
                input_tokens=10,
                output_tokens=20,
                request_id="heartbeat-test-request",
                response_id="heartbeat-test-response",
                status="success",
                finish_reason="end_turn",
                is_truncated=False,
                incomplete_reason=None,
            )

        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = generate_response

        registry = LLMProviderRegistry({
            "openai": mock_provider
        })

        mock_event_repository = AsyncMock()

        service = AssistantService(
            provider_registry=registry,
            event_repository=mock_event_repository,
        )

        # Replace the real heartbeat loop with a controlled test coroutine.
        async def heartbeat_probe(event_id):
            heartbeat_started.set()

            try:
                await asyncio.Event().wait()
            finally:
                heartbeat_stopped.set()

        service._run_request_heartbeat = heartbeat_probe

        request = ChatRequest(
            question="Test heartbeat lifecycle",
            provider="openai",
        )

        response = await service.process_request(request)

        # Verify heartbeat started and was stopped.
        assert heartbeat_started.is_set()
        assert heartbeat_stopped.is_set()

        if should_fail:
            assert response.status == "error"
            mock_event_repository.update_assistant_request.assert_awaited_with(
                event_id=mock_event_repository.create_assistant_request.await_args.kwargs["event_id"],
                model="unknown",
                status="error",
                latency_ms=pytest.approx(
                    response.metadata.latency_ms
                ),
            )
        else:
            assert response.status == "success"
            assert response.answer == "Mock heartbeat test response"

    asyncio.run(run_test())


def test_persistence_retry_succeeds_after_transient_failure(monkeypatch):

    async def run_test():

        mock_repository = AsyncMock()
        mock_repository.update_assistant_request.side_effect = [
            RuntimeError("Temporary database failure"),
            None,
        ]

        service = AssistantService(
            provider_registry=LLMProviderRegistry({}),
            event_repository=mock_repository,
        )

        sleep_mock = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep_mock)

        result = await service._persist_request_with_retry(
            event_id=uuid.uuid4(),
            status="success",
        )

        assert result is True
        assert mock_repository.update_assistant_request.await_count == 2
        sleep_mock.assert_awaited_once()

    asyncio.run(run_test())


def test_persistence_retry_stops_after_max_attempts(monkeypatch):

    async def run_test():

        mock_repository = AsyncMock()
        mock_repository.update_assistant_request.side_effect = (
            RuntimeError("Database unavailable")
        )

        service = AssistantService(
            provider_registry=LLMProviderRegistry({}),
            event_repository=mock_repository,
        )

        sleep_mock = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep_mock)

        result = await service._persist_request_with_retry(
            event_id=uuid.uuid4(),
            status="success",
        )

        assert result is False
        assert (
            mock_repository.update_assistant_request.await_count
            == settings.persistence_retry_attempts
        )
        assert (
            sleep_mock.await_count
            == settings.persistence_retry_attempts - 1
        )

    asyncio.run(run_test())


def test_successful_llm_response_survives_persistence_failure(monkeypatch):

    async def run_test():

        mock_provider = AsyncMock()
        mock_provider.generate.return_value = LLMResult(
            answer="Successful LLM response",
            provider="openai",
            model="gpt-5",
            input_tokens=10,
            output_tokens=20,
            request_id="retry-test-request",
            response_id="retry-test-response",
            status="success",
            finish_reason="end_turn",
            is_truncated=False,
            incomplete_reason=None,
        )

        mock_repository = AsyncMock()
        mock_repository.update_assistant_request.side_effect = (
            RuntimeError("Database unavailable")
        )

        registry = LLMProviderRegistry({
            "openai": mock_provider
        })

        service = AssistantService(
            provider_registry=registry,
            event_repository=mock_repository,
        )

        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        monkeypatch.setattr(
            settings,
            "persistence_retry_attempts",
            2,
        )

        request = ChatRequest(
            question="Test persistence failure",
            provider="openai",
        )

        response = await service.process_request(request)

        assert response.status == "success"
        assert response.answer == "Successful LLM response"

        assert (
            mock_repository.update_assistant_request.await_count == 2
        )

    asyncio.run(run_test())
