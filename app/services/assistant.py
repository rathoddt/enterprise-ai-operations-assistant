import uuid

from app.models.schemas import (
    ChatRequest,
    ChatResponse
)


class AssistantService:

    async def process_request(
        self,
        request: ChatRequest
    ) -> ChatResponse:

        conversation_id = (
            request.conversation_id
            or str(uuid.uuid4())
        )

        return ChatResponse(
            answer=(
                "Request received successfully. "
                "LLM integration will be implemented "
                "in the next development phase."
            ),
            conversation_id=conversation_id,
            status="success"
        )


assistant_service = AssistantService()