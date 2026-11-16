from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from os import replace
from uuid import uuid4

from app.rag.ingestion_service import DocumentIngestionService
from app.rag.knowledge_publication_policy import KnowledgePublicationPolicy
from app.rag.markdown_generator import MarkdownGenerator
from app.rag.schemas import (
    IngestionResult,
    KnowledgePublicationCandidate,
)


@dataclass(frozen=True)
class KnowledgePublicationResult:
    """Result of publishing a research document."""

    file_path: Path
    ingestion_result: IngestionResult


class KnowledgePublicationService:
    """Publishes eligible research results as Markdown and ingests them."""

    def __init__(
        self,
        ingestion_service: DocumentIngestionService,
        policy: KnowledgePublicationPolicy | None = None,
        markdown_generator: MarkdownGenerator | None = None,
        output_dir: str | Path = "data/knowledge_base/generated",
    ):
        self.ingestion_service = ingestion_service
        self.policy = policy or KnowledgePublicationPolicy()
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.output_dir = Path(output_dir)

    async def publish(
        self,
        candidate: KnowledgePublicationCandidate,
        source_references: list[str] | None = None,
    ) -> KnowledgePublicationResult:
        """Validate, save and ingest an approved research result."""

        if not self.policy.is_eligible(candidate):
            raise ValueError(
                "Knowledge publication candidate is not eligible"
            )

        markdown_content = self.markdown_generator.generate(
            candidate,
            source_references,
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use a generated identifier rather than user-provided text
        # to prevent path traversal and filename collisions.
        document_id = str(uuid4())
        filename = f"research_{document_id}.md"
        file_path = self.output_dir / filename

        # Write to a temporary file and atomically move it into place.
        temp_path = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                suffix=".tmp",
                prefix=".research_",
                dir=self.output_dir,
                delete=False,
            ) as temp_file:
                temp_file.write(markdown_content)
                temp_path = Path(temp_file.name)

            replace(temp_path, file_path)

        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

        # Keep the Markdown file if ingestion fails.
        ingestion_result = await self.ingestion_service.ingest_file(
            file_path=file_path,
            source_type="generated",
            source_name=candidate.producer_name,
        )

        return KnowledgePublicationResult(
            file_path=file_path,
            ingestion_result=ingestion_result,
        )