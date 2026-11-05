from fastapi import APIRouter

from app.models.schemas import (
    ChatRequest,
    ChatResponse
)

from app.services.assistant import assistant_service

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    return await assistant_service.process_request(
        request
    )