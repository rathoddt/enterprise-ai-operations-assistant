from typing import Protocol

from app.web_search.schemas import (
    WebSearchRequest,
    WebSearchResponse,
)


class WebSearchProvider(Protocol):

    async def search(
        self,
        request: WebSearchRequest,
    ) -> WebSearchResponse:
        ...