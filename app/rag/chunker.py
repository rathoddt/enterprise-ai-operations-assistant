
import uuid

import tiktoken

from app.core.config import settings


class DocumentChunker:

    def __init__(self):
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap

        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be greater than zero")

        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size"
            )

        self.encoding = tiktoken.get_encoding(
            settings.rag_tokenizer_encoding
        )

        self.newline_token = self.encoding.encode("\n")

    def chunk(
        self,
        text: str,
        document_id: str,
        page_number: int | None = None,
    ) -> list[dict]:

        if not isinstance(text, str):
            raise TypeError("Input must be a string")

        if not text.strip():
            raise ValueError("Document content cannot be empty")

        if not document_id:
            raise ValueError("Document ID is required")

        tokens = self.encoding.encode(text)

        if not tokens:
            raise ValueError("Document contains no tokens")

        results = []

        start = 0
        chunk_index = 0

        while start < len(tokens):

            end = min(start + self.chunk_size, len(tokens))

            # Prefer a newline boundary near the target limit.
            if end < len(tokens):
                adjusted_end = self._find_newline_boundary(
                    tokens,
                    start,
                    end,
                )

                if adjusted_end is not None:
                    end = adjusted_end

            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)

            if chunk_text.strip():
                results.append({
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "token_count": len(chunk_tokens),
                    "page_number": page_number,
                    "text": chunk_text,
                })

                chunk_index += 1

            if end >= len(tokens):
                break

            # Advance using the same original token sequence.
            # This guarantees exact token overlap.
            start = end - self.chunk_overlap

        return results

    def _find_newline_boundary(
        self,
        tokens: list[int],
        start: int,
        end: int,
    ) -> int | None:

        search_start = max(
            start + 1,
            end - 50,
        )

        newline_length = len(self.newline_token)

        for position in range(end - 1, search_start - 1, -1):

            candidate = tokens[
                position:position + newline_length
            ]

            if candidate == self.newline_token:
                return position + newline_length

        return None
