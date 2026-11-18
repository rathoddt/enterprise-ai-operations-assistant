
import pytest

from app.rag.context_builder import ContextBuilder
from app.rag.schemas import DocumentChunk


def create_chunk(
    chunk_id="chunk-001",
    document_id="doc-001",
    chunk_index=0,
    text="This is sample document content.",
    page_number=1,
):
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=chunk_index,
        text=text,
        token_count=10,
        page_number=page_number,
    )


def test_build_empty_results():
    context, sources = ContextBuilder.build([])

    assert context == ""
    assert sources == []


def test_build_single_chunk():
    chunk = create_chunk()

    context, sources = ContextBuilder.build([
        {
            "chunk": chunk,
            "score": 0.85,
        }
    ])

    assert "[S1]" in context
    assert "doc-001" in context
    assert "chunk-001" in context
    assert "Page Number: 1" in context
    assert "Similarity Score: 0.8500" in context
    assert chunk.text in context

    assert len(sources) == 1
    assert sources[0]["document_id"] == "doc-001"
    assert sources[0]["chunk_id"] == "chunk-001"
    assert sources[0]["page_number"] == 1
    assert sources[0]["similarity_score"] == 0.85


def test_build_multiple_chunks():
    first_chunk = create_chunk(
        chunk_id="chunk-001",
        chunk_index=0,
        text="First document section.",
    )

    second_chunk = create_chunk(
        chunk_id="chunk-002",
        chunk_index=1,
        text="Second document section.",
        page_number=2,
    )

    context, sources = ContextBuilder.build([
        {"chunk": first_chunk, "score": 0.91},
        {"chunk": second_chunk, "score": 0.82},
    ])

    assert "[S1]" in context
    assert "[S2]" in context

    assert "First document section." in context
    assert "Second document section." in context

    assert len(sources) == 2
    assert sources[0]["chunk_index"] == 0
    assert sources[1]["chunk_index"] == 1
    assert sources[1]["page_number"] == 2


def test_build_chunk_without_page_number():
    chunk = create_chunk(page_number=None)

    context, sources = ContextBuilder.build([
        {"chunk": chunk, "score": 0.75}
    ])

    assert "Page Number: Not available" in context
    assert sources[0]["page_number"] is None


def test_excerpt_is_limited_to_500_characters():
    long_text = "A" * 1000
    chunk = create_chunk(text=long_text)

    context, sources = ContextBuilder.build([
        {"chunk": chunk, "score": 0.90}
    ])

    assert len(sources[0]["excerpt"]) == 500
    assert len(context) > 500


def test_invalid_chunk_text_is_rejected():
    with pytest.raises(Exception):
        create_chunk(text="")

def test_source_ids_map_to_retrieved_chunks():
    results = [
        {
            "chunk": DocumentChunk(
                chunk_id="chunk-001",
                document_id="doc-001",
                chunk_index=0,
                text="First document content",
                token_count=5,
                page_number=1,
            ),
            "score": 0.95,
        },
        {
            "chunk": DocumentChunk(
                chunk_id="chunk-002",
                document_id="doc-002",
                chunk_index=1,
                text="Second document content",
                token_count=5,
                page_number=2,
            ),
            "score": 0.85,
        },
    ]

    _, sources = ContextBuilder.build(results)

    assert sources[0]["source_id"] == "S1"
    assert sources[0]["document_id"] == "doc-001"
    assert sources[1]["source_id"] == "S2"
    assert sources[1]["document_id"] == "doc-002"