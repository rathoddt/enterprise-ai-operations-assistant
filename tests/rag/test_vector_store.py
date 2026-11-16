
import pytest

from app.rag.schemas import DocumentChunk
from app.rag.vector_store import FAISSVectorStore


def create_chunk(
    chunk_id: str,
    document_id: str = "doc-1",
    text: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        text=text or f"Content for {chunk_id}",
        token_count=5,
        page_number=1,
    )


def test_add_chunks_and_embeddings(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        create_chunk("chunk-1"),
        create_chunk("chunk-2"),
    ]

    embeddings = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]

    store.add(chunks, embeddings)

    assert store.total_chunks == 2
    assert store.embedding_dimension == 2
    assert store.index.ntotal == 2


def test_search_returns_most_similar_chunks(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        create_chunk("chunk-1", text="Python programming"),
        create_chunk("chunk-2", text="Cloud architecture"),
        create_chunk("chunk-3", text="Machine learning"),
    ]

    embeddings = [
        [1.0, 0.0],
        [0.0, 1.0],
        [0.9, 0.1],
    ]

    store.add(chunks, embeddings)

    results = store.search(
        query_embedding=[1.0, 0.0],
        top_k=2,
    )

    assert len(results) == 2
    assert results[0]["chunk"].chunk_id == "chunk-1"
    assert results[1]["chunk"].chunk_id == "chunk-3"
    assert results[0]["score"] > results[1]["score"]


def test_search_filters_by_document_id(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        create_chunk("chunk-1", document_id="resume-1"),
        create_chunk("chunk-2", document_id="resume-2"),
        create_chunk("chunk-3", document_id="resume-1"),
    ]

    embeddings = [
        [1.0, 0.0],
        [0.99, 0.01],
        [0.0, 1.0],
    ]

    store.add(chunks, embeddings)

    results = store.search(
        query_embedding=[1.0, 0.0],
        top_k=5,
        document_id="resume-1",
    )

    assert len(results) == 2
    assert all(
        result["chunk"].document_id == "resume-1"
        for result in results
    )


def test_search_returns_empty_for_unknown_document(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    store.add(
        [create_chunk("chunk-1")],
        [[1.0, 0.0]],
    )

    results = store.search(
        query_embedding=[1.0, 0.0],
        document_id="unknown-document",
    )

    assert results == []


def test_search_returns_empty_for_empty_store(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    results = store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []


def test_search_respects_minimum_score(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    store.add(
        [
            create_chunk("chunk-1"),
            create_chunk("chunk-2"),
        ],
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ],
    )

    results = store.search(
        query_embedding=[1.0, 0.0],
        min_score=0.9,
    )

    assert len(results) == 1
    assert results[0]["chunk"].chunk_id == "chunk-1"


def test_save_and_load_vector_store(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        create_chunk("chunk-1", text="Python"),
        create_chunk("chunk-2", text="Machine learning"),
    ]

    store.add(
        chunks,
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ],
    )

    store.save()

    loaded_store = FAISSVectorStore(index_dir=tmp_path)
    loaded_store.load()

    assert loaded_store.total_chunks == 2
    assert loaded_store.embedding_dimension == 2

    results = loaded_store.search(
        query_embedding=[1.0, 0.0],
        top_k=1,
    )

    assert results[0]["chunk"].text == "Python"


def test_rejects_mismatched_chunk_and_embedding_counts(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    with pytest.raises(ValueError, match="Chunk count"):
        store.add(
            [create_chunk("chunk-1")],
            [],
        )


def test_rejects_duplicate_chunk_ids(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    with pytest.raises(ValueError, match="Duplicate chunk IDs"):
        store.add(
            [
                create_chunk("chunk-1"),
                create_chunk("chunk-1"),
            ],
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
        )


def test_rejects_duplicate_chunk_across_additions(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    store.add(
        [create_chunk("chunk-1")],
        [[1.0, 0.0]],
    )

    with pytest.raises(ValueError, match="already exists"):
        store.add(
            [create_chunk("chunk-1")],
            [[0.0, 1.0]],
        )


def test_rejects_embedding_dimension_mismatch(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    store.add(
        [create_chunk("chunk-1")],
        [[1.0, 0.0]],
    )

    with pytest.raises(ValueError, match="dimension mismatch"):
        store.add(
            [create_chunk("chunk-2")],
            [[1.0, 0.0, 0.0]],
        )


def test_rejects_zero_embedding(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    with pytest.raises(ValueError, match="zero vectors"):
        store.add(
            [create_chunk("chunk-1")],
            [[0.0, 0.0]],
        )


def test_rejects_invalid_top_k(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    with pytest.raises(ValueError, match="top_k"):
        store.search(
            query_embedding=[1.0, 0.0],
            top_k=0,
        )


def test_rejects_invalid_query_dimension(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    store.add(
        [create_chunk("chunk-1")],
        [[1.0, 0.0]],
    )

    with pytest.raises(ValueError, match="dimension"):
        store.search(
            query_embedding=[1.0, 0.0, 0.0],
        )


def test_rejects_saving_empty_store(tmp_path):
    store = FAISSVectorStore(index_dir=tmp_path)

    with pytest.raises(ValueError, match="empty vector store"):
        store.save()
