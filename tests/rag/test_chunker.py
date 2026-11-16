
import pytest
import tiktoken

from app.rag.chunker import DocumentChunker


@pytest.fixture
def chunker():
    return DocumentChunker()


def test_empty_document_raises_error(chunker):
    with pytest.raises(ValueError):
        chunker.chunk("", "doc-001")


def test_document_id_is_required(chunker):
    with pytest.raises(ValueError):
        chunker.chunk("Some content", "")


def test_creates_chunk_metadata(chunker):
    result = chunker.chunk(
        "# Enterprise AI\n\nRAG application architecture.",
        "doc-001",
        page_number=2,
    )

    assert len(result) == 1
    assert result[0]["document_id"] == "doc-001"
    assert result[0]["chunk_index"] == 0
    assert result[0]["page_number"] == 2
    assert result[0]["token_count"] > 0
    assert result[0]["chunk_id"]


def test_respects_chunk_size(chunker):
    text = "\n\n".join(
        f"Paragraph {i}: " + ("enterprise AI architecture " * 30)
        for i in range(100)
    )

    result = chunker.chunk(text, "doc-002")

    assert len(result) > 1
    assert all(
        item["token_count"] <= chunker.chunk_size
        for item in result
    )


def test_preserves_markdown_headings(chunker):
    text = """# RAG Architecture

## Components

FastAPI, PostgreSQL and Azure OpenAI.
"""

    result = chunker.chunk(text, "doc-003")

    combined = "\n".join(item["text"] for item in result)

    assert "# RAG Architecture" in combined
    assert "## Components" in combined


def test_preserves_markdown_table(chunker):
    text = """# Technology

| Component | Technology |
|---|---|
| API | FastAPI |
| Database | PostgreSQL |
"""

    result = chunker.chunk(text, "doc-004")

    combined = "\n".join(item["text"] for item in result)

    assert "| Component | Technology |" in combined
    assert "| Database | PostgreSQL |" in combined


def test_preserves_fenced_code_block(chunker):
    text = """# Python example

```python
def hello():
    print("Hello Enterprise AI")
```
"""

    result = chunker.chunk(text, "doc-005")

    combined = "\n".join(item["text"] for item in result)

    assert "```python" in combined
    assert 'print("Hello Enterprise AI")' in combined
    assert "```" in combined


def test_configured_overlap(chunker):
    text = "\n\n".join(
        f"Section {i}: " + ("machine learning architecture " * 25)
        for i in range(40)
    )

    result = chunker.chunk(text, "doc-006")

    assert len(result) > 1

    first_tokens = chunker.encoding.encode(result[0]["text"])
    second_tokens = chunker.encoding.encode(result[1]["text"])

    overlap = min(
        chunker.chunk_overlap,
        len(first_tokens),
        len(second_tokens),
    )

    if overlap:
        assert first_tokens[-overlap:] == second_tokens[:overlap]


def test_token_count_matches_encoding(chunker):
    result = chunker.chunk(
        "Enterprise AI Operations Assistant",
        "doc-007",
    )

    encoding = tiktoken.get_encoding(
        "cl100k_base"
    )

    actual_count = len(
        encoding.encode(result[0]["text"])
    )

    assert result[0]["token_count"] == actual_count
