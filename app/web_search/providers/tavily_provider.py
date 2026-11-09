import logging

from tavily import AsyncTavilyClient

from app.core.config import settings
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)

logger = logging.getLogger(__name__)


class TavilySearchProvider:

    def __init__(self):
        if not settings.tavily_api_key:
            raise ValueError(
                "Tavily API key is not configured."
            )

        self.client = AsyncTavilyClient(
            api_key=settings.tavily_api_key
        )

    async def search(
        self,
        request: WebSearchRequest,
    ) -> WebSearchResponse:

        response = await self.client.search(
            query=request.query,
            search_depth=request.search_depth,
            topic=request.topic,
            max_results=request.max_results,
            include_answer=request.include_answer,
            include_raw_content=False,
            timeout=30,
        )

        results = [
            WebSearchResult(
                title=item.get("title", "Untitled"),
                url=item["url"],
                content=item.get("content", ""),
                score=item.get("score"),
                published_date=item.get("published_date"),
            )
            for item in response.get("results", [])
        ]

        logger.info(
            "Tavily search completed | query_length=%s "
            "results=%s response_time=%s",
            len(request.query),
            len(results),
            response.get("response_time"),
        )

        return WebSearchResponse(
            query=request.query,
            provider="tavily",
            answer=response.get("answer"),
            results=results,
            response_time=response.get("response_time"),
        )