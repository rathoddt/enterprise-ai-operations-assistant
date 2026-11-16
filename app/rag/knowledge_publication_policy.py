from app.rag.schemas import KnowledgePublicationCandidate


class KnowledgePublicationPolicy:
    """Controls which research results are eligible for RAG publication."""

    ALLOWED_CATEGORIES = {
        "company_research",
        "job_opportunities",
        "technology_research",
    }

    def __init__(
        self,
        allowed_agent_operations: set[tuple[str, str]] | None = None,
    ):
        self.allowed_agent_operations = allowed_agent_operations or set()

    def is_eligible(
        self,
        candidate: KnowledgePublicationCandidate,
    ) -> bool:
        """Return whether a candidate is eligible for publication."""

        if not candidate.approved_for_publication:
            return False

        if candidate.knowledge_category not in self.ALLOWED_CATEGORIES:
            return False

        if candidate.producer_type == "llm":
            return True

        if candidate.producer_type == "agent":
            if not candidate.operation_name:
                return False

            return (
                candidate.producer_name,
                candidate.operation_name,
            ) in self.allowed_agent_operations

        return False