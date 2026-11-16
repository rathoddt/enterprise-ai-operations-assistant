
from fastapi import APIRouter, Depends

from app.api.dependencies import get_semantic_retrieval_service
from app.models.schemas import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
)
from app.rag.retrieval_service import SemanticRetrievalService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/search",
    response_model=RetrievalResponse,
)
async def search_documents(
    request: RetrievalRequest,
    retrieval_service: SemanticRetrievalService = Depends(
        get_semantic_retrieval_service
    ),
):
    """Retrieve relevant document chunks using semantic similarity."""

    results = await retrieval_service.retrieve(
        question=request.question,
        top_k=request.top_k,
        document_id=request.document_id,
        min_score=request.min_score,
    )

    retrieved_chunks = [
        RetrievedChunk(
            chunk_id=result["chunk"].chunk_id,
            document_id=result["chunk"].document_id,
            chunk_index=result["chunk"].chunk_index,
            text=result["chunk"].text,
            token_count=result["chunk"].token_count,
            page_number=result["chunk"].page_number,
            similarity_score=result["score"],
        )
        for result in results
    ]

    return RetrievalResponse(
        question=request.question,
        total_results=len(retrieved_chunks),
        results=retrieved_chunks,
    )
