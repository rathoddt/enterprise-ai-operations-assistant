
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_document_ingestion_service
from app.core.config import settings
from app.rag.ingestion_service import DocumentIngestionService
from app.rag.document_loader import SUPPORTED_EXTENSIONS


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def validate_file_content(filename: str, content: bytes) -> None:
    """Validate basic file signatures and text encoding."""

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file signature")

    elif extension == ".docx":
        if not content.startswith(b"PK\x03\x04"):
            raise ValueError("Invalid DOCX file signature")

    elif extension in {".txt", ".md"}:
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "Text documents must use UTF-8 encoding"
            ) from exc


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    ingestion_service: DocumentIngestionService = Depends(
        get_document_ingestion_service
    ),
):
    """Upload and ingest a PDF, DOCX, TXT or Markdown document."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Supported formats: PDF, DOCX, TXT, MD",
        )

    max_bytes = settings.rag_max_upload_size_mb * 1024 * 1024

    # Read at most one byte beyond the configured limit.
    content = await file.read(max_bytes + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.rag_max_upload_size_mb} MB limit",
        )

    try:
        validate_file_content(file.filename, content)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc    

    try:
        result = await ingestion_service.ingest_bytes(
            filename=file.filename,
            content=content,
            source_type="upload",
        )

    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()

    embedding_dimensions = (
        len(result.embeddings[0]) if result.embeddings else 0
    )

    return {
        "status": "success",
        "message": "Document ingested and embedded successfully",
        "document": result.document.model_dump(mode="json"),
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "page_number": chunk.page_number,
            }
            for chunk in result.chunks
        ],
        "embedding_count": len(result.embeddings),
        "embedding_dimensions": embedding_dimensions,
    }
