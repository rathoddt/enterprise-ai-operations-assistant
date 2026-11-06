
from fastapi import APIRouter, Depends

from app.models.schemas import (
    ChatRequest,
    ChatResponse
)

from app.api.dependencies import get_assistant_service
from app.models.schemas import ChatRequest, ChatResponse
from app.services.assistant import AssistantService

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
