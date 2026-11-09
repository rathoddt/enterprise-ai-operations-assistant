
import logging

from app.web_search.provider import WebSearchProvider
from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
)

logger = logging.getLogger(__name__)


class WebSearchService:

    def __init__(self, provider: WebSearchProvider):
        self.provider = provider

    async def search(
        self,
        request: WebSearchRequest,
    ) -> WebSearchResponse:

        logger.info(
            "Web search started | provider=%s query_length=%s",
            self.provider.__class__.__name__,
            len(request.query),
        )

        response = await self.provider.search(request)

        logger.info(
            "Web search completed | provider=%s results=%s "
            "response_time=%s",
            response.provider,
            len(response.results),
            response.response_time,
        )

        return response
