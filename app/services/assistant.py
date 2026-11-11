import logging
import time
import uuid

from app.llm.registry import LLMProviderRegistry
from app.llm.schemas import LLMMetadata
from app.models.schemas import ChatRequest, ChatResponse
from app.core.config import settings

from contextlib import nullcontext
from app.core.observability import get_langfuse_client
from app.core.metrics import assistant_requests_total

from app.core.metrics import assistant_requests_with_web_search_total
from app.web_search.router import SearchRouter
from app.services.web_search import WebSearchService
from app.web_search.schemas import WebSearchRequest
from app.core.metrics import assistant_requests_by_provider_total
from app.db.repositories import EventRepository

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(
        self,
        provider_registry: LLMProviderRegistry,
        search_router: SearchRouter | None = None,
        web_search_service: WebSearchService | None = None,
        event_repository: EventRepository | None = None,
    ):
        self.provider_registry = provider_registry
        self.search_router = search_router
        self.web_search_service = web_search_service
        self.event_repository = event_repository
        self.langfuse = get_langfuse_client()

    # def __init__(
    #     self,
    #     provider_registry: LLMProviderRegistry,
    #     search_router: SearchRouter | None = None,
    #     web_search_service: WebSearchService | None = None,
    # ):
    #     self.provider_registry = provider_registry
    #     self.search_router = search_router
    #     self.web_search_service = web_search_service
    #     self.langfuse = get_langfuse_client()
        
    # def __init__(self, provider_registry: LLMProviderRegistry):
    #     self.provider_registry = provider_registry
    #     self.langfuse = get_langfuse_client()

    async def process_request(self, request: ChatRequest) -> ChatResponse:
        # Count each incoming assistant request exactly once.
        # assistant_requests_total.inc()
        # Count each incoming assistant request exactly once.
        assistant_requests_total.inc()
        assistant_requests_by_provider_total.labels(
            provider=request.provider
        ).inc()

        conversation_id = (
            request.conversation_id or str(uuid.uuid4())
        )

        request_event_id = uuid.uuid4()
        event_persisted = False

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
            if self.event_repository:
                try:
                    await self.event_repository.create_assistant_request(
                        event_id=request_event_id,
                        conversation_id=conversation_id,
                        provider=request.provider,
                    )
                    event_persisted = True
                except Exception:
                    logger.exception(
                        "Failed to persist assistant request event"
                    )

            start_time = time.perf_counter()            

            start_time = time.perf_counter()
            search_context_text = ""
            web_search_used = False

            try:
                # Dynamically decide whether web search is required.
                if self.search_router and self.web_search_service:

                    search_decision = await self.search_router.route(
                        query=request.question,
                        provider=provider,
                    )
                    if event_persisted:
                        try:
                            await self.event_repository.record_search_decision(
                                event_id=request_event_id,
                                decision=search_decision,
                            )
                        except Exception:
                            logger.exception(
                                "Failed to persist search routing decision"
                            )

                    if search_decision.requires_search:

                        # Count this assistant request only once when search is attempted.
                        if not web_search_used:
                            assistant_requests_with_web_search_total.inc()
                            web_search_used = True

                        search_request = WebSearchRequest(
                            query=search_decision.search_query or request.question,
                            max_results=5,
                            search_depth="basic",
                            topic=search_decision.search_type
                            if search_decision.search_type in ("general", "news")
                            else "general",
                            include_answer=True,
                        )

                        search_response = await self.web_search_service.search(
                            search_request
                        )

                        search_context_parts = []

                        if search_response.answer:
                            search_context_parts.append(
                                f"Search summary:\n{search_response.answer}"
                            )

                        for index, result in enumerate(
                            search_response.results,
                            start=1,
                        ):
                            search_context_parts.append(
                                f"[Source {index}]\n"
                                f"Title: {result.title}\n"
                                f"URL: {result.url}\n"
                                f"Content: {result.content}"
                            )

                        search_context_text = (
                            "\n\nWeb search results:\n"
                            + "\n\n".join(search_context_parts)
                        )

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
                            # user_prompt=request.question,
                            user_prompt=request.question + search_context_text,
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
                if event_persisted:
                    try:
                        await self.event_repository.update_assistant_request(
                            event_id=request_event_id,
                            model=metadata.model,
                            status="success",
                            latency_ms=metadata.latency_ms,
                            input_tokens=metadata.input_tokens,
                            output_tokens=metadata.output_tokens,
                            provider_request_id=metadata.request_id,
                            provider_response_id=metadata.response_id,
                            finish_reason=metadata.finish_reason,
                            is_truncated=metadata.is_truncated,
                            incomplete_reason=metadata.incomplete_reason,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to update successful assistant request event"
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

                if event_persisted:
                    try:
                        await self.event_repository.update_assistant_request(
                            event_id=request_event_id,
                            model=deployment,
                            status="error",
                            latency_ms=latency_ms,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to update failed assistant request event"
                        )

                return ChatResponse(
                    answer="The assistant could not process your request.",
                    conversation_id=conversation_id,
                    status="error",
                    metadata=metadata,
                )        
