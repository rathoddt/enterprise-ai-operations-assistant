import asyncio
from unittest.mock import AsyncMock

from app.models.schemas import ChatRequest
from app.services.assistant import AssistantService


def test_assistant_service_with_mock_llm():

    mock_provider = AsyncMock()

    mock_provider.generate.return_value = (
        "Payment policy retrieved successfully."
    )

    service = AssistantService(
        llm_provider=mock_provider
    )

    request = ChatRequest(
        question="What is our payment policy?"
    )

    response = asyncio.run(
        service.process_request(request)
    )

    assert response.status == "success"

    assert response.answer == (
        "Payment policy retrieved successfully."
    )

    mock_provider.generate.assert_awaited_once_with(
        "What is our payment policy?"
    )