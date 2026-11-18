from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    RAGQARequest,
    RAGQAResponse,
)

from app.api.dependencies import (
    get_assistant_service,
    get_rag_orchestrator,
)

from app.models.schemas import ChatRequest, ChatResponse
from app.services.assistant import AssistantService
from app.rag.orchestrator import RAGOrchestrator

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"]
)

@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    assistant: AssistantService = Depends(get_assistant_service)
):
    return await assistant.process_request(request)


@router.post(
    "/qa",
    response_model=RAGQAResponse,
)
async def rag_qa(
    request: RAGQARequest,
    orchestrator: RAGOrchestrator = Depends(
        get_rag_orchestrator
    ),
):
    try:
        return await orchestrator.answer(request)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM generation failed while processing the RAG request.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the RAG request.",
        ) from exc