
import asyncio
import hashlib

from app.rag.ingestion_service import DocumentIngestionService


class FakeDocumentLoader:
    def load_bytes(self, filename, content):
        return [
            {"text": "First page content", "page_number": 1},
            {"text": "Second page content", "page_number": 2},
        ]


class FakeTextProcessor:
    def clean(self, text):
        return text.strip()


class FakeChunker:
    def chunk(self, text, document_id, page_number=None):
        return [
            {
                "chunk_id": f"chunk-{page_number}",
                "document_id": document_id,
                "chunk_index": 0,
                "text": text,
                "token_count": 3,
                "page_number": page_number,
            }
        ]


class FakeEmbeddingService:
    async def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def close(self):
        pass

class FakeVectorStore:
    def __init__(self):
        self.added_chunks = []
        self.added_embeddings = []
        self.save_called = False

    def add(self, chunks, embeddings):
        self.added_chunks = chunks
        self.added_embeddings = embeddings

    def save(self):
        self.save_called = True

def create_service(embedding_service=None):
    return DocumentIngestionService(
        document_loader=FakeDocumentLoader(),
        text_processor=FakeTextProcessor(),
        chunker=FakeChunker(),
        embedding_service=embedding_service or FakeEmbeddingService(),
    )


def test_ingests_document_and_generates_embeddings():
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=b"sample PDF content",
        )
    )

    assert result.document.filename == "architecture.pdf"
    assert result.document.file_type == "pdf"
    assert result.document.source_type == "upload"
    assert result.document.chunk_count == 2
    assert result.document.page_count == 2

    assert len(result.chunks) == 2
    assert len(result.embeddings) == 2


def test_chunk_indexes_are_unique_across_pages():
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=b"sample content",
        )
    )

    indexes = [chunk.chunk_index for chunk in result.chunks]

    assert indexes == [0, 1]


def test_embeddings_match_chunk_order():
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=b"sample content",
        )
    )

    assert result.embeddings == [
        [0.1, 0.2, 0.3],
        [0.1, 0.2, 0.3],
    ]

    assert result.chunks[0].text == "First page content"
    assert result.chunks[1].text == "Second page content"


def test_generated_document_metadata():
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="agent_response_001.md",
            content=b"Generated knowledge",
            source_type="generated",
            source_name="enterprise_ai_assistant",
        )
    )

    assert result.document.source_type == "generated"
    assert result.document.source_name == "enterprise_ai_assistant"
    assert result.document.file_type == "md"


def test_document_content_hash():
    content = b"sample PDF content"
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=content,
        )
    )

    expected_hash = hashlib.sha256(content).hexdigest()

    assert result.document.content_hash == expected_hash


def test_rejects_empty_filename():
    service = create_service()

    try:
        asyncio.run(
            service.ingest_bytes(
                filename=" ",
                content=b"sample content",
            )
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Filename cannot be empty" in str(exc)


def test_rejects_empty_content():
    service = create_service()

    try:
        asyncio.run(
            service.ingest_bytes(
                filename="document.txt",
                content=b"",
            )
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Document content cannot be empty" in str(exc)

def test_ingestion_adds_chunks_to_vector_store():
    vector_store = FakeVectorStore()

    service = DocumentIngestionService(
        document_loader=FakeDocumentLoader(),
        text_processor=FakeTextProcessor(),
        chunker=FakeChunker(),
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
    )

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=b"sample PDF content",
        )
    )

    assert len(vector_store.added_chunks) == 2
    assert len(vector_store.added_embeddings) == 2

    assert vector_store.added_chunks == result.chunks
    assert vector_store.added_embeddings == result.embeddings

    assert vector_store.save_called is True


def test_ingestion_without_vector_store_still_works():
    service = create_service()

    result = asyncio.run(
        service.ingest_bytes(
            filename="architecture.pdf",
            content=b"sample PDF content",
        )
    )

    assert len(result.chunks) == 2
    assert len(result.embeddings) == 2