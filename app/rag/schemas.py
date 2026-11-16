
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Metadata describing an ingested knowledge document."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    file_type: Literal["pdf", "docx", "txt", "md"]
    source_type: Literal["upload", "generated"] = "upload"
    source_name: str | None = None
    content_hash: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    page_count: int | None = Field(default=None, ge=1)
    chunk_count: int = Field(default=0, ge=0)


class DocumentChunk(BaseModel):
    """A searchable text chunk belonging to a document."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    token_count: int = Field(ge=1)
    page_number: int | None = Field(default=None, ge=1)


class IngestionResult(BaseModel):
    """Result returned after document ingestion and embedding generation."""

    model_config = ConfigDict(extra="forbid")

    document: DocumentMetadata
    chunks: list[DocumentChunk]
    embeddings: list[list[float]]


class KnowledgePublicationCandidate(BaseModel):
    """An approved research result eligible for knowledge publication."""

    model_config = ConfigDict(extra="forbid")

    original_question: str = Field(min_length=3)
    answer: str = Field(min_length=1)

    # Knowledge category
    knowledge_category: Literal[
        "company_research",
        "job_opportunities",
        "technology_research",
    ]

    # Producer information
    producer_type: Literal["llm", "agent"]
    producer_name: str = Field(min_length=1)
    operation_name: str | None = None

    source_request_id: str = Field(min_length=1)

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)

    publication_reason: str = Field(min_length=1)
    approved_for_publication: Literal[True]