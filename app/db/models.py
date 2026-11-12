
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    func,
)

# from sqlalchemy import (
#     Boolean,
#     DateTime,
#     Float,
#     Integer,
#     String,
#     Text,
#     func,
#     server_default,
#     onupdate,
# )
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AssistantRequestEvent(Base):
    __tablename__ = "assistant_request_events"

    # Unique application-level request identifier
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Conversation tracking
    conversation_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    # LLM information
    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Request execution details
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Token usage
    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Provider identifiers
    provider_request_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    provider_response_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Response completion metadata
    finish_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_truncated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    incomplete_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Event timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )    



class SearchDecisionEvent(Base):
    __tablename__ = "search_decision_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    request_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_request_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    decision_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    search_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    freshness: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class WebSearchExecutionEvent(Base):
    __tablename__ = "web_search_execution_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    request_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_request_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    response_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    result_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    answer_available: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
