import logging
import time
import uuid

from app.llm.registry import LLMProviderRegistry
from app.llm.schemas import LLMMetadata
from app.models.schemas import ChatRequest, ChatResponse
from app.core.config import settings

from contextlib import nullcontext
from app.core.observability import get_langfuse_client

logger = logging.getLogger(__name__)


class AssistantService:

    def __init__(self, provider_registry: LLMProviderRegistry):
        self.provider_registry = provider_registry
        self.langfuse = get_langfuse_client()
    async def process_request(self, request: ChatRequest) -> ChatResponse:

        conversation_id = (
            request.conversation_id or str(uuid.uuid4())
        )

        observation_context = (
            self.langfuse.start_as_current_observation(
                as_type="span",
                name="assistant-request",
                metadata={
                    "provider": request.provider,
                    "conversation_id": conversation_id,
                },
            )
            if self.langfuse
            else nullcontext(None)
        )

        with observation_context as root_span:

            provider = self.provider_registry.get_provider(
                request.provider
            )

            start_time = time.perf_counter()

            try:
                # result = await provider.generate(
                #     system_prompt=request.system_prompt,
                #     user_prompt=request.question,
                #     max_output_tokens=settings.llm_max_output_tokens,
                # )

                generation_context = (
                    self.langfuse.start_as_current_observation(
                        as_type="generation",
                        name="llm-generation",
                        model=getattr(provider, "deployment", "unknown"),
                        model_parameters={
                            "max_output_tokens": settings.llm_max_output_tokens,
                        },
                        metadata={
                            "provider": request.provider,
                        },
                    )
                    if self.langfuse
                    else nullcontext(None)
                )

                with generation_context as generation:
                    try:
                        result = await provider.generate(
                            system_prompt=request.system_prompt,
                            user_prompt=request.question,
                            max_output_tokens=settings.llm_max_output_tokens,
                        )

                        if generation:
                            usage_details = {}

                            if result.input_tokens is not None:
                                usage_details["input"] = result.input_tokens

                            if result.output_tokens is not None:
                                usage_details["output"] = result.output_tokens

                            generation.update(
                                model=result.model,
                                output=result.answer,
                                usage_details=usage_details or None,
                                metadata={
                                    "provider": result.provider,
                                    "request_id": result.request_id,
                                    "response_id": result.response_id,
                                    "finish_reason": result.finish_reason,
                                    "is_truncated": result.is_truncated,
                                    "incomplete_reason": result.incomplete_reason,
                                },
                            )

                    except Exception as exc:
                        if generation:
                            generation.update(
                                level="ERROR",
                                status_message=str(exc),
                            )
                        raise

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
                    finish_reason=result.finish_reason,
                    is_truncated=result.is_truncated,
                    incomplete_reason=result.incomplete_reason,
                )

                logger.info(
                    "LLM request completed | provider=%s model=%s "
                    "latency_ms=%.2f input_tokens=%s output_tokens=%s "
                    "request_id=%s response_id=%s finish_reason=%s "
                    "is_truncated=%s incomplete_reason=%s",
                    metadata.provider,
                    metadata.model,
                    metadata.latency_ms,
                    metadata.input_tokens,
                    metadata.output_tokens,
                    metadata.request_id,
                    metadata.response_id,
                    metadata.finish_reason,
                    metadata.is_truncated,
                    metadata.incomplete_reason,
                )

                if root_span:
                    root_span.update(
                        output={
                            "status": "success",
                            "provider": metadata.provider,
                            "model": metadata.model,
                            "latency_ms": metadata.latency_ms,
                        }
                    )

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

                if root_span:
                    root_span.update(
                        level="ERROR",
                        status_message="LLM request failed",
                        output={"status": "error"},
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

                return ChatResponse(
                    answer="The assistant could not process your request.",
                    conversation_id=conversation_id,
                    status="error",
                    metadata=metadata,
                )        

    # async def process_request(self, request: ChatRequest) -> ChatResponse:

    #     conversation_id = (
    #         request.conversation_id or str(uuid.uuid4())
    #     )

    #     provider = self.provider_registry.get_provider(
    #         request.provider
    #     )

    #     start_time = time.perf_counter()

    #     try:
    #         result = await provider.generate(
    #             system_prompt=request.system_prompt,
    #             user_prompt=request.question,
    #             max_output_tokens=settings.llm_max_output_tokens,
    #         )

    #         latency_ms = round(
    #             (time.perf_counter() - start_time) * 1000,
    #             2,
    #         )

    #         metadata = LLMMetadata(
    #             provider=result.provider,
    #             model=result.model,
    #             latency_ms=latency_ms,
    #             input_tokens=result.input_tokens,
    #             output_tokens=result.output_tokens,
    #             request_id=result.request_id,
    #             response_id=result.response_id,
    #             status="success",
    #             finish_reason=result.finish_reason,
    #             is_truncated=result.is_truncated,      
    #             incomplete_reason=result.incomplete_reason,          
    #         )

    #         logger.info(
    #             "LLM request completed | provider=%s model=%s "
    #             "latency_ms=%.2f input_tokens=%s output_tokens=%s "
    #             "request_id=%s response_id=%s finish_reason=%s "
    #             "is_truncated=%s incomplete_reason=%s",
    #             metadata.provider,
    #             metadata.model,
    #             metadata.latency_ms,
    #             metadata.input_tokens,
    #             metadata.output_tokens,
    #             metadata.request_id,
    #             metadata.response_id,
    #             metadata.finish_reason,
    #             metadata.is_truncated,
    #             metadata.incomplete_reason,
    #         )

    #         return ChatResponse(
    #             answer=result.answer,
    #             conversation_id=conversation_id,
    #             status="success",
    #             metadata=metadata,
    #         )

    #     except Exception:
    #         latency_ms = round(
    #             (time.perf_counter() - start_time) * 1000,
    #             2,
    #         )

    #         logger.exception(
    #             "LLM request failed | provider=%s",
    #             request.provider,
    #         )

    #         deployment = getattr(provider, "deployment", None)

    #         if not isinstance(deployment, str):
    #             deployment = "unknown"

    #         metadata = LLMMetadata(
    #             provider=request.provider,
    #             model=deployment,
    #             latency_ms=latency_ms,
    #             status="error",
    #         )

    #         return ChatResponse(
    #             answer="The assistant could not process your request.",
    #             conversation_id=conversation_id,
    #             status="error",
    #             metadata=metadata,
    #         )

