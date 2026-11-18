
from app.rag.schemas import DocumentChunk


class ContextBuilder:
    """Builds source-labelled context from retrieved document chunks."""

    @staticmethod
    def build(results: list[dict]) -> tuple[str, list[dict]]:
        """
        Build LLM context and structured source references.

        Returns:
            context_text: Formatted document context.
            sources: Structured source metadata.
        """

        if not results:
            return "", []

        context_sections = []
        sources = []

        for index, result in enumerate(results, start=1):
            chunk: DocumentChunk = result["chunk"]
            score = float(result["score"])

            source_id = f"S{index}"

            context_sections.append(
                f"[{source_id}]\n"
                f"Document ID: {chunk.document_id}\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"Chunk Index: {chunk.chunk_index}\n"
                f"Page Number: {chunk.page_number or 'Not available'}\n"
                f"Similarity Score: {score:.4f}\n"
                f"Content:\n{chunk.text}"
            )

            sources.append({
                "source_id": source_id,"document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "similarity_score": score,
                "excerpt": chunk.text[:500],
            })

        context_text = (
            "Retrieved document context follows.\n"
            "Use these sources as evidence when answering.\n"
            "Do not invent facts or citations.\n\n"
            + "\n\n---\n\n".join(context_sections)
        )

        return context_text, sources
