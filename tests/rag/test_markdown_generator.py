from app.rag.schemas import KnowledgePublicationCandidate
from app.rag.markdown_generator import MarkdownGenerator


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


def test_generate_markdown_document():
    generator = MarkdownGenerator()
    candidate = create_candidate()

    result = generator.generate(candidate)

    assert result.startswith("---\n")
    assert "# Which IT companies operate in Navi Mumbai?" in result
    assert "## Research Answer" in result
    assert "Several IT companies operate in Navi Mumbai." in result
    assert "knowledge_category: company_research" in result
    assert "producer_type: llm" in result
    assert "status: published" in result


def test_generate_markdown_with_source_references():
    generator = MarkdownGenerator()
    candidate = create_candidate()

    sources = [
        "https://example.com/companies",
        "https://example.com/locations",
    ]

    result = generator.generate(candidate, sources)

    assert "https://example.com/companies" in result
    assert "https://example.com/locations" in result


def test_generate_markdown_without_sources():
    generator = MarkdownGenerator()
    candidate = create_candidate()

    result = generator.generate(candidate)

    assert "No external sources provided." in result


def test_generate_markdown_for_agent():
    generator = MarkdownGenerator()

    candidate = create_candidate(
        producer_type="agent",
        producer_name="CompanyResearchAgent",
        operation_name="company_discovery",
    )

    result = generator.generate(candidate)

    assert "producer_type: agent" in result
    assert "CompanyResearchAgent" in result
    assert "company_discovery" in result


def test_yaml_metadata_escapes_special_characters():
    generator = MarkdownGenerator()

    candidate = create_candidate(
        producer_name='Research "Assistant": Mumbai',
        source_request_id="request-456",
    )

    result = generator.generate(candidate)

    assert 'producer_name: "Research \\"Assistant\\": Mumbai"' in result
    assert 'source_request_id: "request-456"' in result


def test_generate_markdown_returns_trailing_newline():
    generator = MarkdownGenerator()
    candidate = create_candidate()

    result = generator.generate(candidate)

    assert result.endswith("\n")