
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import FAISSVectorStore


class SemanticRetrievalService:
    """Generates query embeddings and retrieves relevant document chunks."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: FAISSVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Retrieve semantically relevant chunks for a question."""

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        # Generate embedding for the user's question.
        query_embedding = await self.embedding_service.embed_text(
            question.strip()
        )

        # Search FAISS using cosine similarity.
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id,
            min_score=min_score,
        )

        return results
