import time
from uuid import UUID

import logging

from app.web_search.provider import WebSearchProvider
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
)

from contextlib import nullcontext
from app.core.observability import get_langfuse_client
from app.core.metrics import web_search_executions_total
from app.db.repositories import EventRepository

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(
        self,
        provider: WebSearchProvider,
        event_repository: EventRepository | None = None,
    ):
        self.provider = provider
        self.event_repository = event_repository
        self.langfuse = get_langfuse_client()

    async def search(
        self,
        request: WebSearchRequest,
        request_event_id: UUID | None = None,
    ) -> WebSearchResponse:
        search_context = (
            self.langfuse.start_as_current_observation(
                as_type="span",
                name="web-search",
                metadata={
                    "provider": self.provider.__class__.__name__,
                    "search_depth": request.search_depth,
                    "topic": request.topic,
                    "max_results": request.max_results,
                    "include_answer": request.include_answer,
                },
            )
            if self.langfuse
            else nullcontext(None)
        )

        with search_context as search_span:
            search_start_time = time.perf_counter()

            try:
                logger.info(
                    "Web search started | provider=%s query_length=%s",
                    self.provider.__class__.__name__,
                    len(request.query),
                )

                response = await self.provider.search(request)
                measured_response_time = round(
                    time.perf_counter() - search_start_time,
                    4,
                )

                web_search_executions_total.labels(
                    provider=response.provider,
                    status="success",
                ).inc()

                if self.event_repository and request_event_id:
                    try:
                        await self.event_repository.record_web_search_execution(
                            event_id=request_event_id,
                            provider=response.provider,
                            status="success",
                            # response_time=response.response_time,
                            response_time=measured_response_time,
                            result_count=len(response.results),
                            answer_available=bool(response.answer),
                        )
                    except Exception:
                        logger.exception(
                            "Failed to persist successful web search event"
                        )

                if search_span:
                    search_span.update(
                        output={
                            "provider": response.provider,
                            "result_count": len(response.results),
                            "response_time": response.response_time,
                            "answer_available": bool(response.answer),
                        },
                        metadata={
                            "search_status": "success",
                            "result_count": len(response.results),
                        },
                    )

                logger.info(
                    "Web search completed | provider=%s results=%s "
                    "response_time=%s measured_response_time=%s",
                    response.provider,
                    len(response.results),
                    response.response_time,
                    measured_response_time,
                )

                return response

            except Exception as exc:
                web_search_executions_total.labels(
                    provider=self.provider.__class__.__name__.replace(
                        "SearchProvider", ""
                    ).lower(),
                    status="error",
                ).inc()
                if self.event_repository and request_event_id:
                    try:
                        await self.event_repository.record_web_search_execution(
                            event_id=request_event_id,
                            provider=self.provider.__class__.__name__.replace(
                                "SearchProvider", ""
                            ).lower(),
                            status="error",
                            response_time=round(
                                (time.perf_counter() - search_start_time), 4
                            ),
                            error_type=type(exc).__name__,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to persist failed web search event"
                        )

                if search_span:
                    search_span.update(
                        level="ERROR",
                        status_message="Web search failed",
                        output={"status": "error"},
                    )

                logger.exception(
                    "Web search failed | provider=%s",
                    self.provider.__class__.__name__,
                )

                raise

