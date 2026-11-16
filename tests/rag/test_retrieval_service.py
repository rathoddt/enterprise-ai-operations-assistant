
import asyncio

import pytest

from app.rag.retrieval_service import SemanticRetrievalService


class FakeEmbeddingService:
    def __init__(self):
        self.received_question = None

    async def embed_text(self, text):
        self.received_question = text
        return [1.0, 0.0, 0.0]


class FakeVectorStore:
    def __init__(self):
        self.search_arguments = None

    def search(
        self,
        query_embedding,
        top_k=5,
        document_id=None,
        min_score=0.0,
    ):
        self.search_arguments = {
            "query_embedding": query_embedding,
            "top_k": top_k,
            "document_id": document_id,
            "min_score": min_score,
        }

        return [
            {
                "chunk": "Retrieved document content",
                "score": 0.95,
            }
        ]


def create_service():
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    service = SemanticRetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    return service, embedding_service, vector_store


def test_retrieves_relevant_chunks():
    service, embedding_service, vector_store = create_service()

    results = asyncio.run(
        service.retrieve("  Explain machine learning  ")
    )

    assert embedding_service.received_question == (
        "Explain machine learning"
    )

    assert vector_store.search_arguments["query_embedding"] == [
        1.0, 0.0, 0.0
    ]

    assert len(results) == 1
    assert results[0]["score"] == 0.95


def test_retrieves_with_document_filter():
    service, _, vector_store = create_service()

    asyncio.run(
        service.retrieve(
            question="Summarize my resume",
            top_k=3,
            document_id="resume-123",
            min_score=0.7,
        )
    )

    assert vector_store.search_arguments["top_k"] == 3
    assert vector_store.search_arguments["document_id"] == "resume-123"
    assert vector_store.search_arguments["min_score"] == 0.7


@pytest.mark.parametrize(
    "question",
    ["", " ", None],
)
def test_rejects_empty_question(question):
    service, _, _ = create_service()

    with pytest.raises(ValueError, match="Question cannot be empty"):
        asyncio.run(service.retrieve(question))


def test_rejects_invalid_top_k():
    service, _, _ = create_service()

    with pytest.raises(ValueError, match="top_k"):
        asyncio.run(
            service.retrieve(
                question="Find relevant content",
                top_k=0,
            )
        )
