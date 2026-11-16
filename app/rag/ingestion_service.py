
import hashlib
import uuid
from pathlib import Path
from typing import Literal

from app.rag.chunker import DocumentChunker
from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import EmbeddingService
from app.rag.schemas import (
    DocumentChunk,
    DocumentMetadata,
    IngestionResult,
)
from app.rag.text_processor import TextProcessor
from app.rag.vector_store import FAISSVectorStore

class DocumentIngestionService:
    """Coordinates document extraction, cleaning, chunking and embedding."""

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        text_processor: TextProcessor | None = None,
        chunker: DocumentChunker | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: FAISSVectorStore | None = None,
    ):
        self.document_loader = document_loader or DocumentLoader()
        self.text_processor = text_processor or TextProcessor()
        self.chunker = chunker or DocumentChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store

    async def ingest_bytes(
        self,
        filename: str,
        content: bytes,
        source_type: Literal["upload", "generated"] = "upload",
        source_name: str | None = None,
    ) -> IngestionResult:

        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        if not content:
            raise ValueError("Document content cannot be empty")

        document_id = str(uuid.uuid4())
        extension = Path(filename).suffix.lower()

        # Extract document content.
        extracted_pages = self.document_loader.load_bytes(
            filename,
            content,
        )

        all_chunks = []
        next_chunk_index = 0
        page_numbers = set()

        # Clean and chunk each extracted page.
        for page in extracted_pages:
            cleaned_text = self.text_processor.clean(page["text"])
            page_number = page["page_number"]

            if page_number is not None:
                page_numbers.add(page_number)

            page_chunks = self.chunker.chunk(
                text=cleaned_text,
                document_id=document_id,
                page_number=page_number,
            )

            # Maintain unique chunk indexes across pages.
            for chunk in page_chunks:
                chunk["chunk_index"] = next_chunk_index
                next_chunk_index += 1

                all_chunks.append(
                    DocumentChunk.model_validate(chunk)
                )

        if not all_chunks:
            raise ValueError("Document produced no usable chunks")

        # Generate embeddings in the same order as the chunks.
        embeddings = await self.embedding_service.embed_texts(
            [chunk.text for chunk in all_chunks]
        )

        if len(embeddings) != len(all_chunks):
            raise ValueError(
                "Embedding count does not match document chunk count"
            )
        # Store document chunks and embeddings in FAISS.
        if self.vector_store is not None:
            self.vector_store.add(
                chunks=all_chunks,
                embeddings=embeddings,
            )
            self.vector_store.save()        

        # Build document-level metadata.
        metadata = DocumentMetadata(
            document_id=document_id,
            filename=Path(filename).name,
            file_type=extension.lstrip("."),
            source_type=source_type,
            source_name=source_name,
            content_hash=hashlib.sha256(content).hexdigest(),
            page_count=len(page_numbers) if page_numbers else None,
            chunk_count=len(all_chunks),
        )

        return IngestionResult(
            document=metadata,
            chunks=all_chunks,
            embeddings=embeddings,
        )

    async def ingest_file(
        self,
        file_path: str | Path,
        source_type: Literal["upload", "generated"] = "generated",
        source_name: str | None = None,
    ) -> IngestionResult:

        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        content = path.read_bytes()

        return await self.ingest_bytes(
            filename=path.name,
            content=content,
            source_type=source_type,
            source_name=source_name,
        )

    async def close(self) -> None:
        await self.embedding_service.close()
