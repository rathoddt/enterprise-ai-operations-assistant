from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from app.llm.schemas import LLMMetadata

DEFAULT_SYSTEM_PROMPT = (
    "Provide a concise, well-structured answer. "
    "Use approximately 400–600 words unless the question "
    "requires more detail. Avoid unnecessary repetition."
)

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["openai", "anthropic"] = "openai"

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="User question"
    )

    system_prompt: str = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        max_length=8000,
    )

    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    status: Literal["success", "pending", "error"]
    metadata: LLMMetadata | None = None

class HealthResponse(BaseModel):
    status: str
    application: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str | None = None



class RetrievalRequest(BaseModel):
    """Request model for semantic document search."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Question used to retrieve relevant document chunks",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of chunks to retrieve",
    )

    document_id: str | None = Field(
        default=None,
        description="Optional document ID to restrict retrieval",
    )

    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score",
    )


class RetrievedChunk(BaseModel):
    """A retrieved document chunk with its similarity score."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    token_count: int
    page_number: int | None = None
    similarity_score: float


class RetrievalResponse(BaseModel):
    """Response containing semantically retrieved chunks."""

    question: str
    total_results: int
    results: list[RetrievedChunk]


# ==================================================
# RAG QUESTION AND ANSWER SCHEMAS
# ==================================================

class RAGQARequest(BaseModel):
    """Request model for document-grounded question answering."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Question to answer using indexed documents",
    )

    provider: Literal["openai", "anthropic"] = "openai"

    document_id: str | None = Field(
        default=None,
        description=(
            "Optional document ID. If omitted, "
            "search all indexed documents."
        ),
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    min_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
    )

    system_prompt: str = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        max_length=8000,
    )


class RAGSource(BaseModel):
    """Source reference for a retrieved document chunk."""

    source_id: str
    document_id: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    similarity_score: float
    excerpt: str


class RAGMetadata(BaseModel):
    """Metadata describing the retrieval operation."""

    retrieval_status: Literal[
        "success",
        "no_relevant_context",
    ]

    retrieved_chunks: int
    top_k: int
    min_score: float


class RAGQAResponse(BaseModel):
    """Response from the RAG question-answering pipeline."""

    question: str

    answer: str

    status: Literal[
        "success",
        "insufficient_context",
    ]

    sources: list[RAGSource] = Field(default_factory=list)

    rag_metadata: RAGMetadata

    llm_metadata: LLMMetadata | None = None
