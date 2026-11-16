
import json
from pathlib import Path

import faiss
import numpy as np

from app.rag.schemas import DocumentChunk


class FAISSVectorStore:
    """Stores and retrieves document chunks using FAISS cosine similarity."""

    def __init__(self, index_dir: str | Path = "data/index"):
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss.index"
        self.metadata_path = self.index_dir / "metadata.json"

        self.index: faiss.IndexFlatIP | None = None
        self.chunks: list[DocumentChunk] = []
        self.embedding_dimension: int | None = None

        self._chunk_ids: set[str] = set()

    def add(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Add document chunks and their corresponding embeddings."""

        if not chunks:
            raise ValueError("Chunks cannot be empty")

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk count must match embedding count"
            )

        vectors = np.asarray(embeddings, dtype=np.float32)

        if vectors.ndim != 2:
            raise ValueError("Embeddings must be a 2D array")

        if not np.isfinite(vectors).all():
            raise ValueError("Embeddings must contain finite values")

        if np.any(np.linalg.norm(vectors, axis=1) == 0):
            raise ValueError("Embeddings cannot contain zero vectors")

        dimension = vectors.shape[1]

        if dimension == 0:
            raise ValueError("Embedding dimension cannot be zero")

        if self.embedding_dimension is not None:
            if dimension != self.embedding_dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected "
                    f"{self.embedding_dimension}, received {dimension}"
                )

        incoming_ids = [chunk.chunk_id for chunk in chunks]

        if len(incoming_ids) != len(set(incoming_ids)):
            raise ValueError("Duplicate chunk IDs in input")

        if self._chunk_ids.intersection(incoming_ids):
            raise ValueError("Chunk ID already exists in vector store")

        if any(
            not chunk.chunk_id.strip()
            or not chunk.document_id.strip()
            for chunk in chunks
        ):
            raise ValueError("Chunk and document IDs cannot be empty")

        # Normalize vectors for cosine similarity.
        faiss.normalize_L2(vectors)

        # Initialize index dynamically from embedding dimension.
        if self.index is None:
            self.embedding_dimension = dimension
            self.index = faiss.IndexFlatIP(dimension)

        # FAISS positions match the order of self.chunks.
        self.index.add(vectors)

        self.chunks.extend(chunks)
        self._chunk_ids.update(incoming_ids)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_id: str | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Search for the most similar chunks."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")

        if self.index is None or not self.chunks:
            return []

        query = np.asarray(
            [query_embedding],
            dtype=np.float32,
        )

        if query.ndim != 2 or query.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Query embedding must have dimension "
                f"{self.embedding_dimension}"
            )

        if not np.isfinite(query).all():
            raise ValueError("Query embedding must contain finite values")

        if np.linalg.norm(query) == 0:
            raise ValueError("Query embedding cannot be a zero vector")

        faiss.normalize_L2(query)

        # Retrieve all candidates when document filtering is requested,
        # because filtering only the global top-k could miss relevant
        # chunks from the selected document.
        candidate_count = (
            self.index.ntotal if document_id is not None
            else min(top_k, self.index.ntotal)
        )

        scores, positions = self.index.search(
            query,
            candidate_count,
        )

        results = []

        for score, position in zip(scores[0], positions[0]):
            if position < 0:
                continue

            chunk = self.chunks[int(position)]

            if document_id is not None:
                if chunk.document_id != document_id:
                    continue

            score = float(score)

            if score < min_score:
                continue

            results.append(
                {
                    "chunk": chunk,
                    "score": score,
                }
            )

            if len(results) >= top_k:
                break

        return results

    def save(self) -> None:
        """Persist FAISS index and chunk metadata to disk."""

        if self.index is None:
            raise ValueError("Cannot save an empty vector store")

        self.index_dir.mkdir(parents=True, exist_ok=True)

        metadata = [
            chunk.model_dump(mode="json")
            for chunk in self.chunks
        ]

        index_temp = self.index_path.with_suffix(".index.tmp")
        metadata_temp = self.metadata_path.with_suffix(".json.tmp")

        try:
            faiss.write_index(self.index, str(index_temp))

            metadata_temp.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            index_temp.replace(self.index_path)
            metadata_temp.replace(self.metadata_path)

        finally:
            index_temp.unlink(missing_ok=True)
            metadata_temp.unlink(missing_ok=True)

    def load(self) -> None:
        """Load a previously persisted FAISS index and metadata."""

        if not self.index_path.is_file():
            raise FileNotFoundError(
                f"FAISS index not found: {self.index_path}"
            )

        if not self.metadata_path.is_file():
            raise FileNotFoundError(
                f"Metadata file not found: {self.metadata_path}"
            )

        index = faiss.read_index(str(self.index_path))

        metadata = json.loads(
            self.metadata_path.read_text(encoding="utf-8")
        )

        chunks = [
            DocumentChunk.model_validate(item)
            for item in metadata
        ]

        if index.ntotal != len(chunks):
            raise ValueError(
                "FAISS index count does not match metadata count"
            )

        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs in stored metadata")

        if index.ntotal > 0 and not isinstance(index, faiss.IndexFlatIP):
            raise ValueError("Unsupported FAISS index type")

        self.index = index
        self.chunks = chunks
        self.embedding_dimension = index.d if index.ntotal > 0 else None
        self._chunk_ids = {chunk.chunk_id for chunk in chunks}

    @property
    def total_chunks(self) -> int:
        """Return the number of stored chunks."""

        return len(self.chunks)
