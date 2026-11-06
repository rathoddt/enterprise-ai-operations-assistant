import uuid

from app.models.schemas import (
    ChatRequest,
    ChatResponse
)

from app.llm.provider import LLMProvider


class AssistantService:

    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider

    async def process_request(
        self,
        request: ChatRequest
    ) -> ChatResponse:

        conversation_id = (
            request.conversation_id
            or str(uuid.uuid4())
        )

        answer = (
            "Request received successfully. "
            "LLM integration will be implemented "
            "in the next development phase."
        )

        if self.llm_provider:
            answer = await self.llm_provider.generate(
                request.question
            )

        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            status="success"
        )
assistant_service = AssistantService()

# 
# --------------------------v0--------------------------------
# import uuid

# from app.models.schemas import (
#     ChatRequest,
#     ChatResponse
# )


# class AssistantService:

#     async def process_request(
#         self,
#         request: ChatRequest
#     ) -> ChatResponse:

#         conversation_id = (
#             request.conversation_id
#             or str(uuid.uuid4())
#         )

#         return ChatResponse(
#             answer=(
#                 "Request received successfully. "
#                 "LLM integration will be implemented "
#                 "in the next development phase."
#             ),
#             conversation_id=conversation_id,
#             status="success"
#         )


# assistant_service = AssistantService()