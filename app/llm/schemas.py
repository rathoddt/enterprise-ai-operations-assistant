from pydantic import BaseModel
from typing import Literal


class LLMResult(BaseModel):
    answer: str
    provider: Literal["openai", "anthropic"]
    model: str

    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    request_id: str | None = None
    response_id: str | None = None

    request_id: str | None = None
    status: Literal["success", "error"] = "success"

class LLMMetadata(BaseModel):
    provider: Literal["openai", "anthropic"]
    model: str

    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    request_id: str | None = None
    response_id: str | None = None

    request_id: str | None = None
    status: Literal["success", "error"]    