import pytest

from app.rag.schemas import KnowledgePublicationCandidate
from app.rag.knowledge_publication_policy import KnowledgePublicationPolicy


def create_candidate(**overrides):
    data = {
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

    data.update(overrides)
    return KnowledgePublicationCandidate(**data)


def test_approved_llm_candidate_is_eligible():
    policy = KnowledgePublicationPolicy()
    candidate = create_candidate()

    assert policy.is_eligible(candidate) is True


@pytest.mark.parametrize(
    "category",
    [
        "company_research",
        "job_opportunities",
        "technology_research",
    ],
)
def test_all_supported_categories_are_eligible(category):
    policy = KnowledgePublicationPolicy()
    candidate = create_candidate(knowledge_category=category)

    assert policy.is_eligible(candidate) is True


def test_agent_operation_is_rejected_when_not_allowlisted():
    policy = KnowledgePublicationPolicy()

    candidate = create_candidate(
        producer_type="agent",
        producer_name="CompanyResearchAgent",
        operation_name="company_discovery",
    )

    assert policy.is_eligible(candidate) is False


def test_allowlisted_agent_operation_is_eligible():
    policy = KnowledgePublicationPolicy(
        allowed_agent_operations={
            ("CompanyResearchAgent", "company_discovery")
        }
    )

    candidate = create_candidate(
        producer_type="agent",
        producer_name="CompanyResearchAgent",
        operation_name="company_discovery",
    )

    assert policy.is_eligible(candidate) is True


def test_agent_without_operation_name_is_rejected():
    policy = KnowledgePublicationPolicy()

    candidate = create_candidate(
        producer_type="agent",
        producer_name="CompanyResearchAgent",
        operation_name=None,
    )

    assert policy.is_eligible(candidate) is False