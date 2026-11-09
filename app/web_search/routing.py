from typing import Literal

from pydantic import BaseModel, Field


class SearchDecision(BaseModel):
    requires_search: bool

    reason: str = Field(
        min_length=3,
        max_length=500,
    )

    search_query: str | None = None

    search_type: Literal[
        "general",
        "news",
        "weather",
        "pricing",
    ] = "general"

    freshness: Literal[
        "none",
        "recent",
        "live",
    ] = "none"

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    decision_source: Literal[
        "rules",
        "llm",
    ]