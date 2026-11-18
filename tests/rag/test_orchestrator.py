
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.llm.schemas import LLMResult
from app.models.schemas import RAGQARequest
from app.rag.orchestrator import RAGOrchestrator
from app.rag.schemas import DocumentChunk


def create_chunk(
    chunk_id="chunk-001",
    document_id="doc-001",
    chunk_index=0,
    text="The candidate has 3 years of MLOps experience.",
    page_number=1,
):
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=chunk_index,
        text=text,
        token_count=10,
        page_number=page_number,
    )


def create_llm_result(
    answer="The candidate has 3 years of MLOps experience. [S1]",
    status="success",
):
    return LLMResult(
        answer=answer,
        provider="openai",
        model="gpt-5",
        input_tokens=100,
        output_tokens=50,
        request_id="request-123",
        response_id="response-123",
        status=status,
        finish_reason="completed",
    )


def create_orchestrator(
    retrieval_results=None,
    llm_result=None,
):
    retrieval_service = Mock()
    retrieval_service.retrieve = AsyncMock(
        return_value=(
            retrieval_results
            if retrieval_results is not None
            else [
                {
                    "chunk": create_chunk(),
                    "score": 0.95,
                }
            ]
        )
    )

    provider = Mock()
    provider.generate = AsyncMock(
        return_value=llm_result or create_llm_result()
    )

    provider_registry = Mock()
    provider_registry.get_provider.return_value = provider

    orchestrator = RAGOrchestrator(
        retrieval_service=retrieval_service,
        provider_registry=provider_registry,
    )

    return (
        orchestrator,
        retrieval_service,
        provider_registry,
        provider,
    )


def test_generates_grounded_answer_with_sources():
    orchestrator, retrieval, registry, provider = (
        create_orchestrator()
    )

    request = RAGQARequest(
        question="How much MLOps experience does the candidate have?",
        provider="openai",
    )

    response = asyncio.run(orchestrator.answer(request))

    assert response.status == "success"
    assert response.rag_metadata.retrieval_status == "success"
    assert response.rag_metadata.retrieved_chunks == 1

    assert response.answer == (
        "The candidate has 3 years of MLOps experience. [S1]"
    )

    assert len(response.sources) == 1
    assert response.sources[0].source_id == "S1"
    assert response.sources[0].document_id == "doc-001"
    assert response.sources[0].chunk_id == "chunk-001"

    assert response.llm_metadata.provider == "openai"
    assert response.llm_metadata.model == "gpt-5"

    retrieval.retrieve.assert_awaited_once()
    registry.get_provider.assert_called_once_with("openai")
    provider.generate.assert_awaited_once()


def test_returns_insufficient_context_without_calling_llm():
    orchestrator, _, registry, provider = create_orchestrator(
        retrieval_results=[]
    )

    request = RAGQARequest(
        question="What is the candidate's salary?",
        provider="openai",
    )

    response = asyncio.run(orchestrator.answer(request))

    assert response.status == "insufficient_context"
    assert response.rag_metadata.retrieval_status == (
        "no_relevant_context"
    )
    assert response.rag_metadata.retrieved_chunks == 0
    assert response.sources == []
    assert response.llm_metadata is None

    registry.get_provider.assert_not_called()
    provider.generate.assert_not_awaited()


def test_passes_document_filter_to_retrieval():
    orchestrator, retrieval, _, _ = create_orchestrator()

    request = RAGQARequest(
        question="Summarize this document",
        document_id="resume-123",
        top_k=3,
        min_score=0.7,
    )

    asyncio.run(orchestrator.answer(request))

    retrieval.retrieve.assert_awaited_once_with(
        question="Summarize this document",
        top_k=3,
        document_id="resume-123",
        min_score=0.7,
    )


def test_selects_anthropic_provider():
    orchestrator, _, registry, _ = create_orchestrator()

    request = RAGQARequest(
        question="Summarize my experience",
        provider="anthropic",
    )

    asyncio.run(orchestrator.answer(request))

    registry.get_provider.assert_called_once_with("anthropic")


def test_does_not_return_success_when_llm_generation_fails():
    failed_result = create_llm_result(status="error")

    orchestrator, _, _, provider = create_orchestrator(
        llm_result=failed_result
    )

    request = RAGQARequest(
        question="Summarize my experience",
        provider="openai",
    )

    with pytest.raises(
        RuntimeError,
        match="LLM generation failed",
    ):
        asyncio.run(orchestrator.answer(request))

    provider.generate.assert_awaited_once()
