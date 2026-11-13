import asyncio
import pytest

import app.main as main

from app.core.metrics import assistant_stale_requests_recovered_total

from fastapi.testclient import TestClient

from unittest.mock import AsyncMock

from app.main import app
from app.api.dependencies import get_assistant_service
from app.llm.registry import LLMProviderRegistry
from app.services.assistant import AssistantService
from app.llm.schemas import LLMResult

from app.main import app

client = TestClient(app)


def test_root_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert (
        response.json()["application"]
        == "Enterprise AI Operations Assistant"
    )


def test_health_endpoint():

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_chat_endpoint():
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
            finish_reason="end_turn",
            is_truncated=False, 
            incomplete_reason=None,
        )
    
    registry = LLMProviderRegistry({
        "openai": mock_provider
    })

    mock_service = AssistantService(
        provider_registry=registry
    )

    app.dependency_overrides[get_assistant_service] = (
        lambda: mock_service
    )

    try:
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "question": "What is our payment policy?",
                "provider": "openai"
            }
        )

        assert response.status_code == 200

        assert response.json()["answer"] == (
            "Mock AI response"
        )

        assert response.json()["status"] == "success"

    finally:
        app.dependency_overrides.clear()

# ---------------- v0 ------------------
    # payload = {
    #     "question": "What is our payment policy?"
    # }

    # response = client.post(
    #     "/api/v1/assistant/chat",
    #     json=payload
    # )

    # assert response.status_code == 200

    # data = response.json()

    # assert data["status"] == "success"
    # assert data["conversation_id"] is not None


def test_chat_validation():

    payload = {
        "question": "Hi"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        json=payload
    )

    assert response.status_code == 422


def test_chat_rejects_extra_fields():

    payload = {
        "question": "What is our payment policy?",
        "unexpected": "value"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        json=payload
    )

    assert response.status_code == 422

def test_stale_recovery_worker_increments_metric(monkeypatch):

    class FakeRepository:

        async def recover_stale_assistant_requests(self):
            return 2

    monkeypatch.setattr(
        main,
        "EventRepository",
        FakeRepository
    )

    async def stop_worker(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(
        main.asyncio,
        "sleep",
        stop_worker
    )

    before = assistant_stale_requests_recovered_total._value.get()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main.stale_request_recovery_worker())

    after = assistant_stale_requests_recovered_total._value.get()

    assert after == before + 2