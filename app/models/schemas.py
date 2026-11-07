from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from app.llm.schemas import LLMMetadata

DEFAULT_SYSTEM_PROMPT = (
    "Provide a concise, well-structured answer. "
    "Use approximately 400–600 words unless the question "
    "requires more detail. Avoid unnecessary repetition."
)

class ChatRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")
    provider: Literal["openai", "anthropic"] = "openai"

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="User question"
    )

    system_prompt: str = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        max_length=8000,
    )

    conversation_id: str | None = None


# class ChatResponse(BaseModel):

#     answer: str

#     conversation_id: str

#     status: Literal[
#         "success",
#         "pending",
#         "error"
#     ] = "success"

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    status: Literal["success", "pending", "error"]
    metadata: LLMMetadata | None = None

class HealthResponse(BaseModel):
    status: str
    application: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str | None = None