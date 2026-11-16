
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_document_ingestion_service
from app.rag.schemas import (
    DocumentMetadata,
    DocumentChunk,
    IngestionResult,
)


class MockDocumentIngestionService:

    async def ingest_bytes(
        self,
        filename,
        content,
        source_type="upload",
        source_name=None,
    ):
        if not content:
            raise ValueError("Document content cannot be empty")

        document = DocumentMetadata(
            document_id="doc-test-001",
            filename=filename,
            file_type=filename.rsplit(".", 1)[-1].lower(),
            source_type=source_type,
            source_name=source_name,
            content_hash="mock-hash",
            page_count=1,
            chunk_count=1,
        )

        chunk = DocumentChunk(
            chunk_id="chunk-test-001",
            document_id="doc-test-001",
            chunk_index=0,
            text="Mock document content",
            token_count=3,
            page_number=1,
        )

        return IngestionResult(
            document=document,
            chunks=[chunk],
            embeddings=[[0.1, 0.2, 0.3]],
        )


client = TestClient(app)


@pytest.fixture
def mock_ingestion_service():
    app.dependency_overrides[
        get_document_ingestion_service
    ] = lambda: MockDocumentIngestionService()

    yield

    app.dependency_overrides.pop(
        get_document_ingestion_service,
        None,
    )


def test_upload_txt_success(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "policy.txt",
                io.BytesIO(b"Sample policy document"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["document"]["filename"] == "policy.txt"
    assert data["document"]["file_type"] == "txt"
    assert data["embedding_count"] == 1
    assert data["embedding_dimensions"] == 3


def test_upload_markdown_success(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "knowledge.md",
                io.BytesIO(b"# Knowledge\nSample content"),
                "text/markdown",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["document"]["file_type"] == "md"


def test_upload_rejects_unsupported_extension(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "report.xlsx",
                io.BytesIO(b"sample"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 415


def test_upload_rejects_empty_file(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "empty.txt",
                io.BytesIO(b""),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_upload_rejects_file_exceeding_size_limit(
    mock_ingestion_service,
    monkeypatch,
):

    monkeypatch.setattr(
        "app.api.routes.documents.settings.rag_max_upload_size_mb",
        1,
    )

    oversized_content = b"x" * (1024 * 1024 + 1)

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "large.txt",
                io.BytesIO(oversized_content),
                "text/plain",
            )
        },
    )

    assert response.status_code == 413


def test_upload_handles_ingestion_validation_error(monkeypatch):

    class FailingIngestionService:

        async def ingest_bytes(self, **kwargs):
            raise ValueError("No extractable text found in PDF")

    app.dependency_overrides[
        get_document_ingestion_service
    ] = lambda: FailingIngestionService()

    try:
        response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "scanned.pdf",
                    io.BytesIO(b"%PDF-1.7\nmock PDF content"),
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "No extractable text found in PDF"
        )

    finally:
        app.dependency_overrides.pop(
            get_document_ingestion_service,
            None,
        )


def test_upload_rejects_invalid_pdf_signature(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "invalid.pdf",
                io.BytesIO(b"This is not a PDF"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file signature"


def test_upload_rejects_invalid_docx_signature(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "invalid.docx",
                io.BytesIO(b"This is not a DOCX"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file signature"


def test_upload_rejects_invalid_text_encoding(mock_ingestion_service):

    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "invalid.txt",
                io.BytesIO(b"\xff\xfe\xff"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Text documents must use UTF-8 encoding"
    )
