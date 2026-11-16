
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_semantic_retrieval_service
from app.rag.schemas import DocumentChunk


class FakeSemanticRetrievalService:

    async def retrieve(
        self,
        question,
        top_k=5,
        document_id=None,
        min_score=0.0,
    ):
        chunk = DocumentChunk(
            chunk_id="chunk-001",
            document_id=document_id or "resume-001",
            chunk_index=0,
            text="Experienced in Python, GCP, MLOps and Vertex AI.",
            token_count=12,
            page_number=1,
        )

        return [
            {
                "chunk": chunk,
                "score": 0.95,
            }
        ]


app.dependency_overrides[
    get_semantic_retrieval_service
] = lambda: FakeSemanticRetrievalService()

client = TestClient(app)


def test_search_documents_success():
    response = client.post(
        "/api/v1/documents/search",
        json={
            "question": "What are my MLOps skills?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_results"] == 1
    assert data["results"][0]["chunk_id"] == "chunk-001"
    assert data["results"][0]["document_id"] == "resume-001"
    assert data["results"][0]["similarity_score"] == 0.95


def test_search_documents_with_document_filter():
    response = client.post(
        "/api/v1/documents/search",
        json={
            "question": "Summarize my resume",
            "top_k": 3,
            "document_id": "resume-123",
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["document_id"] == "resume-123"


def test_search_documents_rejects_invalid_top_k():
    response = client.post(
        "/api/v1/documents/search",
        json={
            "question": "Find my skills",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_search_documents_rejects_short_question():
    response = client.post(
        "/api/v1/documents/search",
        json={
            "question": "Hi",
        },
    )

    assert response.status_code == 422


def test_search_documents_rejects_extra_fields():
    response = client.post(
        "/api/v1/documents/search",
        json={
            "question": "Find my skills",
            "unexpected_field": "invalid",
        },
    )

    assert response.status_code == 422
