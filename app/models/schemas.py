from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class ChatRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="User question"
    )

    conversation_id: str | None = None


class ChatResponse(BaseModel):

    answer: str

    conversation_id: str

    status: Literal[
        "success",
        "pending",
        "error"
    ] = "success"


class HealthResponse(BaseModel):
    status: str
    application: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str | None = None