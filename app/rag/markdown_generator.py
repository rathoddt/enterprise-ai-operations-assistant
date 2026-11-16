import json
from datetime import datetime, timezone

from app.rag.schemas import KnowledgePublicationCandidate


class MarkdownGenerator:
    """Generate structured Markdown documents from approved research."""

    def generate(
        self,
        candidate: KnowledgePublicationCandidate,
        source_references: list[str] | None = None,
    ) -> str:
        """Generate a Markdown document from a publication candidate."""

        research_date = datetime.now(timezone.utc).isoformat()

        def yaml_string(value: str) -> str:
            # JSON double-quoted strings are valid YAML scalars.
            return json.dumps(value, ensure_ascii=False)

        sources = source_references or []

        source_section = (
            "\n".join(f"- {source}" for source in sources)
            if sources
            else "- No external sources provided."
        )

        operation = candidate.operation_name or "Not applicable"

        markdown = f"""---
document_type: research_result
knowledge_category: {candidate.knowledge_category}
producer_type: {candidate.producer_type}
producer_name: {yaml_string(candidate.producer_name)}
research_date: {yaml_string(research_date)}
source_request_id: {yaml_string(candidate.source_request_id)}
provider: {yaml_string(candidate.provider)}
model: {yaml_string(candidate.model)}
status: published
---

# {candidate.original_question}

## Research Answer

{candidate.answer}

## Research Metadata

- **Knowledge Category:** {candidate.knowledge_category}
- **Producer Type:** {candidate.producer_type}
- **Producer Name:** {candidate.producer_name}
- **Operation Name:** {operation}
- **Provider:** {candidate.provider}
- **Model:** {candidate.model}
- **Source Request ID:** {candidate.source_request_id}
- **Research Date:** {research_date}
- **Publication Reason:** {candidate.publication_reason}

## Sources

{source_section}
"""

        return markdown.strip() + "\n"