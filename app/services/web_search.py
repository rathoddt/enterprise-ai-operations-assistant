
import logging

from app.web_search.provider import WebSearchProvider
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
)

from contextlib import nullcontext
from app.core.observability import get_langfuse_client
from app.core.metrics import web_search_executions_total

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(self, provider: WebSearchProvider):
        self.provider = provider
        self.langfuse = get_langfuse_client()
    async def search(
        self,
        request: WebSearchRequest,
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

            try:
                logger.info(
                    "Web search started | provider=%s query_length=%s",
                    self.provider.__class__.__name__,
                    len(request.query),
                )

                response = await self.provider.search(request)
                web_search_executions_total.labels(
                    provider=response.provider,
                    status="success",
                ).inc()

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
                    "response_time=%s",
                    response.provider,
                    len(response.results),
                    response.response_time,
                )

                return response

            except Exception as exc:
                web_search_executions_total.labels(
                    provider=self.provider.__class__.__name__.replace(
                        "SearchProvider", ""
                    ).lower(),
                    status="error",
                ).inc()

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

