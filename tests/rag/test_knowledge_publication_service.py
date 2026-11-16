import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.rag.knowledge_publication_service import (
    KnowledgePublicationService,
)
from app.rag.knowledge_publication_policy import (
    KnowledgePublicationPolicy,
)
from app.rag.schemas import KnowledgePublicationCandidate


def create_candidate(**overrides):
    data = {
        "original_question": "Which IT companies operate in Navi Mumbai?",
        "answer": "Several IT companies operate in Navi Mumbai.",
        "knowledge_category": "company_research",
        "producer_type": "llm",
        "producer_name": "GPT-5",
        "operation_name": None,
        "source_request_id": "request-123",
        "provider": "openai",
        "model": "gpt-5",
        "publication_reason": "Relevant company research",
        "approved_for_publication": True,
    }

    data.update(overrides)
    return KnowledgePublicationCandidate(**data)


@pytest.fixture
def ingestion_service():
    service = Mock()
    service.ingest_file = AsyncMock(return_value=Mock(name="ingestion_result"))
    return service


@pytest.fixture
def publication_service(ingestion_service, tmp_path):
    return KnowledgePublicationService(
        ingestion_service=ingestion_service,
        output_dir=tmp_path / "generated",
    )


def test_successful_publication(
    publication_service,
    ingestion_service,
    tmp_path,
):
    candidate = create_candidate()

    result = asyncio.run(publication_service.publish(candidate))

    assert result.file_path.exists()
    assert result.file_path.suffix == ".md"
    assert result.file_path.parent == tmp_path / "generated"

    content = result.file_path.read_text(encoding="utf-8")

    assert "# Which IT companies operate in Navi Mumbai?" in content
    assert "Several IT companies operate in Navi Mumbai." in content

    ingestion_service.ingest_file.assert_awaited_once_with(
        file_path=result.file_path,
        source_type="generated",
        source_name="GPT-5",
    )


def test_rejected_candidate_is_not_saved(
    ingestion_service,
    tmp_path,
):
    output_dir = tmp_path / "generated"

    service = KnowledgePublicationService(
        ingestion_service=ingestion_service,
        policy=KnowledgePublicationPolicy(),
        output_dir=output_dir,
    )

    candidate = create_candidate(
        knowledge_category="company_research",
        producer_type="agent",
        producer_name="CompanyResearchAgent",
        operation_name="company_discovery",
    )

    with pytest.raises(ValueError, match="not eligible"):
        asyncio.run(service.publish(candidate))

    assert not output_dir.exists()
    ingestion_service.ingest_file.assert_not_awaited()


def test_ingestion_failure_preserves_markdown_file(
    publication_service,
    ingestion_service,
):
    ingestion_service.ingest_file.side_effect = RuntimeError(
        "Embedding service unavailable"
    )

    candidate = create_candidate()

    with pytest.raises(
        RuntimeError,
        match="Embedding service unavailable",
    ):
        asyncio.run(publication_service.publish(candidate))

    generated_files = list(
        publication_service.output_dir.glob("*.md")
    )

    assert len(generated_files) == 1
    assert generated_files[0].exists()


def test_generated_filename_is_not_based_on_user_input(
    publication_service,
):
    candidate = create_candidate(
        original_question="../../outside/unsafe-question"
    )

    result = asyncio.run(publication_service.publish(candidate))

    assert result.file_path.parent == publication_service.output_dir
    assert result.file_path.name.startswith("research_")
    assert result.file_path.suffix == ".md"


def test_source_references_are_included(publication_service):
    candidate = create_candidate()

    sources = [
        "https://example.com/company-a",
        "https://example.com/company-b",
    ]

    result = asyncio.run(
        publication_service.publish(
            candidate,
            source_references=sources,
        )
    )

    content = result.file_path.read_text(encoding="utf-8")

    assert "https://example.com/company-a" in content
    assert "https://example.com/company-b" in content