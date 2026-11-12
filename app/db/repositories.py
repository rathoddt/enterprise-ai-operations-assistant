from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import update

from app.db.database import AsyncSessionLocal
from app.db.models import (
    AssistantRequestEvent,
    SearchDecisionEvent,
    WebSearchExecutionEvent,
)
from app.core.config import settings
from sqlalchemy import update, func

class EventRepository:
    """Persists operational events without storing prompts or model responses."""

    async def create_assistant_request(
        self,
        event_id: UUID,
        conversation_id: str,
        provider: str,
    ) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                event = AssistantRequestEvent(
                    id=event_id,
                    conversation_id=conversation_id,
                    provider=provider,
                    model="pending",
                    status="in_progress",
                )
                session.add(event)

    async def update_assistant_request(
        self,
        event_id: UUID,
        **values,
    ) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                statement = (
                    update(AssistantRequestEvent)
                    .where(AssistantRequestEvent.id == event_id)
                    .values(**values)
                )
                await session.execute(statement)

    async def heartbeat_assistant_request(
        self,
        event_id: UUID,
    ) -> bool:
        """
        Refresh updated_at for an active assistant request.

        Returns True if the request is still in_progress
        and its heartbeat was successfully recorded.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                statement = (
                    update(AssistantRequestEvent)
                    .where(
                        AssistantRequestEvent.id == event_id,
                        AssistantRequestEvent.status == "in_progress",
                    )
                    .values(updated_at=func.now())
                )

                result = await session.execute(statement)

                return (result.rowcount or 0) > 0

    async def record_search_decision(
        self,
        event_id: UUID,
        decision,
    ) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                event = SearchDecisionEvent(
                    request_event_id=event_id,
                    decision="search" if decision.requires_search else "no_search",
                    decision_source=decision.decision_source,
                    search_type=decision.search_type,
                    freshness=decision.freshness,
                    confidence=decision.confidence,
                )
                session.add(event)

    async def record_web_search_execution(
        self,
        event_id: UUID,
        provider: str,
        status: str,
        response_time: float | None = None,
        result_count: int | None = None,
        answer_available: bool | None = None,
        error_type: str | None = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                event = WebSearchExecutionEvent(
                    request_event_id=event_id,
                    provider=provider,
                    status=status,
                    response_time=response_time,
                    result_count=result_count,
                    answer_available=answer_available,
                    error_type=error_type,
                )
                session.add(event)

    async def recover_stale_assistant_requests(self) -> int:
        """
        Mark assistant requests as incomplete when they remain
        in_progress beyond the configured stale-event threshold.

        Returns the number of recovered events.
        """

        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=settings.stale_event_threshold_seconds
        )

        async with AsyncSessionLocal() as session:
            async with session.begin():

                statement = (
                    update(AssistantRequestEvent)
                    .where(
                        AssistantRequestEvent.status == "in_progress",
                        AssistantRequestEvent.updated_at < cutoff_time,
                    )
                    .values(
                        status="incomplete",
                        incomplete_reason="stale_request_recovery",
                    )
                )

                result = await session.execute(statement)

                return max(result.rowcount or 0, 0)