import pytest
from pydantic import ValidationError

from app.rag.schemas import KnowledgePublicationCandidate


def valid_candidate_data():
    return {
        "original_question": "Which IT companies operate in Navi Mumbai?",
        "answer": "Example research findings.",
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


def test_valid_knowledge_publication_candidate():
    candidate = KnowledgePublicationCandidate(
        **valid_candidate_data()
    )

    assert candidate.knowledge_category == "company_research"
    assert candidate.producer_type == "llm"
    assert candidate.approved_for_publication is True


@pytest.mark.parametrize(
    "category",
    [
        "company_research",
        "job_opportunities",
        "technology_research",
    ],
)
def test_supported_knowledge_categories(category):
    data = valid_candidate_data()
    data["knowledge_category"] = category

    candidate = KnowledgePublicationCandidate(**data)

    assert candidate.knowledge_category == category


def test_invalid_knowledge_category():
    data = valid_candidate_data()
    data["knowledge_category"] = "general_chat"

    with pytest.raises(ValidationError):
        KnowledgePublicationCandidate(**data)


def test_invalid_producer_type():
    data = valid_candidate_data()
    data["producer_type"] = "human"

    with pytest.raises(ValidationError):
        KnowledgePublicationCandidate(**data)


def test_publication_approval_must_be_true():
    data = valid_candidate_data()
    data["approved_for_publication"] = False

    with pytest.raises(ValidationError):
        KnowledgePublicationCandidate(**data)


def test_agent_candidate():
    data = valid_candidate_data()
    data["producer_type"] = "agent"
    data["producer_name"] = "CompanyResearchAgent"
    data["operation_name"] = "company_discovery"

    candidate = KnowledgePublicationCandidate(**data)

    assert candidate.producer_type == "agent"
    assert candidate.operation_name == "company_discovery"


def test_extra_fields_are_rejected():
    data = valid_candidate_data()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        KnowledgePublicationCandidate(**data)