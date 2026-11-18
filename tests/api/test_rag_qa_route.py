
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_rag_orchestrator


class FakeRAGOrchestrator:

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.received_request = None

    async def answer(self, request):
        self.received_request = request

        if self.error:
            raise self.error

        return self.response


client = TestClient(app)


def test_rag_qa_success():
    fake_orchestrator = FakeRAGOrchestrator(
        response={
            "question": "What are my MLOps skills?",
            "answer": "Experienced in MLOps and Vertex AI. [S1]",
            "status": "success",
            "sources": [
                {
                    "source_id": "S1",
                    "document_id": "resume-001",
                    "chunk_id": "chunk-001",
                    "chunk_index": 0,
                    "page_number": 1,
                    "similarity_score": 0.95,
                    "excerpt": "Experienced in Python, GCP and MLOps.",
                }
            ],
            "rag_metadata": {
                "retrieval_status": "success",
                "retrieved_chunks": 1,
                "top_k": 5,
                "min_score": 0.2,
            },
            "llm_metadata": {
                "provider": "openai",
                "model": "gpt-5",
                "latency_ms": 1200,
                "input_tokens": 100,
                "output_tokens": 50,
                "request_id": "request-123",
                "response_id": "response-123",
                "status": "success",
                "finish_reason": "completed",
                "is_truncated": False,
                "incomplete_reason": None,
            },
        }
    )

    app.dependency_overrides[get_rag_orchestrator] = (
        lambda: fake_orchestrator
    )

    try:
        response = client.post(
            "/api/v1/assistant/qa",
            json={
                "question": "What are my MLOps skills?",
                "provider": "openai",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"
        assert data["answer"] == (
            "Experienced in MLOps and Vertex AI. [S1]"
        )
        assert data["sources"][0]["source_id"] == "S1"
        assert data["sources"][0]["document_id"] == "resume-001"
        assert data["llm_metadata"]["provider"] == "openai"

        assert fake_orchestrator.received_request.question == (
            "What are my MLOps skills?"
        )

    finally:
        app.dependency_overrides.pop(
            get_rag_orchestrator,
            None,
        )


def test_rag_qa_insufficient_context():
    fake_orchestrator = FakeRAGOrchestrator(
        response={
            "question": "What is my salary?",
            "answer": "No relevant information was found.",
            "status": "insufficient_context",
            "sources": [],
            "rag_metadata": {
                "retrieval_status": "no_relevant_context",
                "retrieved_chunks": 0,
                "top_k": 5,
                "min_score": 0.2,
            },
            "llm_metadata": None,
        }
    )

    app.dependency_overrides[get_rag_orchestrator] = (
        lambda: fake_orchestrator
    )

    try:
        response = client.post(
            "/api/v1/assistant/qa",
            json={
                "question": "What is my salary?",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "insufficient_context"
        assert data["sources"] == []
        assert data["llm_metadata"] is None

    finally:
        app.dependency_overrides.pop(
            get_rag_orchestrator,
            None,
        )


def test_rag_qa_llm_failure_returns_502():
    fake_orchestrator = FakeRAGOrchestrator(
        error=RuntimeError("LLM generation failed")
    )

    app.dependency_overrides[get_rag_orchestrator] = (
        lambda: fake_orchestrator
    )

    try:
        response = client.post(
            "/api/v1/assistant/qa",
            json={
                "question": "Summarize my experience",
            },
        )

        assert response.status_code == 502
        assert response.json()["detail"] == (
            "LLM generation failed while processing the RAG request."
        )

    finally:
        app.dependency_overrides.pop(
            get_rag_orchestrator,
            None,
        )


def test_rag_qa_rejects_invalid_request():
    response = client.post(
        "/api/v1/assistant/qa",
        json={
            "question": "Hi",
            "provider": "openai",
        },
    )

    assert response.status_code == 422


def test_rag_qa_rejects_invalid_provider():
    response = client.post(
        "/api/v1/assistant/qa",
        json={
            "question": "Summarize my experience",
            "provider": "unsupported",
        },
    )

    assert response.status_code == 422
