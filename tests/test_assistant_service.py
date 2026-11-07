
import asyncio
from unittest.mock import AsyncMock
from urllib import response

from app.llm.registry import LLMProviderRegistry
from app.models.schemas import ChatRequest
from app.services.assistant import AssistantService
from app.llm.schemas import LLMResult

def test_assistant_service_with_mock_llm():

    mock_provider = AsyncMock()

    # mock_provider.generate.return_value = (
    #     "Payment policy retrieved successfully."
    # )

    mock_provider.generate.return_value = LLMResult(
            answer="Mock AI response",
            provider="openai",
            model="gpt-5",
            input_tokens=10,
            output_tokens=20,
            request_id="mock-request-123",
            response_id="mock-response-456",
            status="success",
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

    mock_provider.generate.assert_awaited_once_with(
        "What is our payment policy?"
    )
    
    assert response.metadata.request_id == "mock-request-123"
    assert response.metadata.response_id == "mock-response-456"