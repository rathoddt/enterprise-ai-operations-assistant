from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class WebSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=5, ge=1, le=10)
    search_depth: Literal["basic", "advanced"] = "basic"
    topic: Literal["general", "news"] = "general"
    include_answer: bool = False


class WebSearchResult(BaseModel):
    title: str
    url: HttpUrl
    content: str
    score: float | None = None
    published_date: str | None = None


class WebSearchResponse(BaseModel):
    query: str
    provider: str
    answer: str | None = None
    results: list[WebSearchResult] = Field(default_factory=list)
    response_time: float | None = None