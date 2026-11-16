
import pytest
from datetime import timezone

from pydantic import ValidationError

from app.rag.schemas import DocumentMetadata, DocumentChunk


def test_document_metadata_defaults():
    metadata = DocumentMetadata(
        document_id="doc-001",
        filename="architecture.pdf",
        file_type="pdf",
        content_hash="abc123",
    )

    assert metadata.source_type == "upload"
    assert metadata.chunk_count == 0
    assert metadata.page_count is None
    assert metadata.created_at.tzinfo is not None
    assert metadata.created_at.utcoffset() is not None


def test_document_metadata_supports_generated_source():
    metadata = DocumentMetadata(
        document_id="doc-002",
        filename="agent_response_001.md",
        file_type="md",
        source_type="generated",
        source_name="enterprise_ai_assistant",
        content_hash="def456",
    )

    assert metadata.source_type == "generated"
    assert metadata.source_name == "enterprise_ai_assistant"


def test_document_metadata_rejects_unsupported_file_type():
    with pytest.raises(ValidationError):
        DocumentMetadata(
            document_id="doc-003",
            filename="notes.xlsx",
            file_type="xlsx",
            content_hash="ghi789",
        )


def test_document_metadata_rejects_negative_chunk_count():
    with pytest.raises(ValidationError):
        DocumentMetadata(
            document_id="doc-004",
            filename="notes.txt",
            file_type="txt",
            content_hash="jkl012",
            chunk_count=-1,
        )


def test_document_chunk_creation():
    chunk = DocumentChunk(
        chunk_id="chunk-001",
        document_id="doc-001",
        chunk_index=0,
        text="Enterprise AI Operations Assistant",
        token_count=5,
        page_number=1,
    )

    assert chunk.document_id == "doc-001"
    assert chunk.chunk_index == 0
    assert chunk.token_count == 5
    assert chunk.page_number == 1


def test_document_chunk_rejects_empty_text():
    with pytest.raises(ValidationError):
        DocumentChunk(
            chunk_id="chunk-002",
            document_id="doc-001",
            chunk_index=0,
            text="",
            token_count=1,
        )


def test_document_chunk_rejects_negative_index():
    with pytest.raises(ValidationError):
        DocumentChunk(
            chunk_id="chunk-003",
            document_id="doc-001",
            chunk_index=-1,
            text="Sample content",
            token_count=2,
        )
