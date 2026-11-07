import logging
import time
import uuid

from app.llm.registry import LLMProviderRegistry
from app.llm.schemas import LLMMetadata
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class AssistantService:

    def __init__(self, provider_registry: LLMProviderRegistry):
        self.provider_registry = provider_registry

    async def process_request(self, request: ChatRequest) -> ChatResponse:

        conversation_id = (
            request.conversation_id or str(uuid.uuid4())
        )

        provider = self.provider_registry.get_provider(
            request.provider
        )

        start_time = time.perf_counter()

        try:
            result = await provider.generate(request.question)

            latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            metadata = LLMMetadata(
                provider=result.provider,
                model=result.model,
                latency_ms=latency_ms,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                request_id=result.request_id,
                response_id=result.response_id,
                status="success",
            )

            logger.info(
                "LLM request completed | provider=%s model=%s "
                "latency_ms=%.2f input_tokens=%s output_tokens=%s "
                "request_id=%s response_id=%s",
                metadata.provider,
                metadata.model,
                metadata.latency_ms,
                metadata.input_tokens,
                metadata.output_tokens,
                metadata.request_id,
                metadata.response_id,
            )

            # logger.info(
            #     "LLM request completed | provider=%s model=%s "
            #     "latency_ms=%.2f input_tokens=%s output_tokens=%s "
            #     "request_id=%s",
            #     metadata.provider,
            #     metadata.model,
            #     metadata.latency_ms,
            #     metadata.input_tokens,
            #     metadata.output_tokens,
            #     metadata.request_id,
            #     metadata.response_id,
            # )


            return ChatResponse(
                answer=result.answer,
                conversation_id=conversation_id,
                status="success",
                metadata=metadata,
            )

        except Exception:
            latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.exception(
                "LLM request failed | provider=%s",
                request.provider,
            )

            deployment = getattr(provider, "deployment", None)

            if not isinstance(deployment, str):
                deployment = "unknown"

            metadata = LLMMetadata(
                provider=request.provider,
                model=deployment,
                latency_ms=latency_ms,
                status="error",
            )

            # metadata = LLMMetadata(
            #     provider=request.provider,
            #     model=getattr(provider, "deployment", "unknown"),
            #     latency_ms=latency_ms,
            #     status="error",
            # )

            return ChatResponse(
                answer="The assistant could not process your request.",
                conversation_id=conversation_id,
                status="error",
                metadata=metadata,
            )

# import uuid

# from app.llm.registry import LLMProviderRegistry
# from app.models.schemas import ChatRequest, ChatResponse


# class AssistantService:

#     def __init__(self, provider_registry: LLMProviderRegistry):
#         self.provider_registry = provider_registry

#     async def process_request(
#         self,
#         request: ChatRequest,
#     ) -> ChatResponse:

#         conversation_id = (
#             request.conversation_id or str(uuid.uuid4())
#         )

#         provider = self.provider_registry.get_provider(
#             request.provider
#         )

#         answer = await provider.generate(request.question)

#         return ChatResponse(
#             answer=answer,
#             conversation_id=conversation_id,
#             status="success",
#         )


# --------------------------v1--------------------------------
# import uuid

# from app.models.schemas import (
#     ChatRequest,
#     ChatResponse
# )

# from app.llm.provider import LLMProvider


# class AssistantService:

#     def __init__(self, llm_provider: LLMProvider | None = None):
#         self.llm_provider = llm_provider

#     async def process_request(
#         self,
#         request: ChatRequest
#     ) -> ChatResponse:

#         conversation_id = (
#             request.conversation_id
#             or str(uuid.uuid4())
#         )

#         answer = (
#             "Request received successfully. "
#             "LLM integration will be implemented "
#             "in the next development phase."
#         )

#         if self.llm_provider:
#             answer = await self.llm_provider.generate(
#                 request.question
#             )

#         return ChatResponse(
#             answer=answer,
#             conversation_id=conversation_id,
#             status="success"
#         )
# assistant_service = AssistantService()


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