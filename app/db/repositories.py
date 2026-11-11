
from uuid import UUID

from sqlalchemy import update

from app.db.database import AsyncSessionLocal
from app.db.models import (
    AssistantRequestEvent,
    SearchDecisionEvent,
    WebSearchExecutionEvent,
)


class EventRepository:
    """Persists operational events without storing prompts or model responses."""

    async def create_assistant_request(
        self,
        event_id: UUID,
        conversation_id: str,
        provider: str,
    ) -> None:
        async with AsyncSessionLocal() as session:
            event = AssistantRequestEvent(
                id=event_id,
                conversation_id=conversation_id,
                provider=provider,
                model="pending",
                status="in_progress",
            )
            session.add(event)
            await session.commit()

    async def update_assistant_request(
        self,
        event_id: UUID,
        **values,
    ) -> None:
        async with AsyncSessionLocal() as session:
            statement = (
                update(AssistantRequestEvent)
                .where(AssistantRequestEvent.id == event_id)
                .values(**values)
            )
            await session.execute(statement)
            await session.commit()

    async def record_search_decision(
        self,
        event_id: UUID,
        decision,
    ) -> None:
        async with AsyncSessionLocal() as session:
            event = SearchDecisionEvent(
                request_event_id=event_id,
                decision="search" if decision.requires_search else "no_search",
                decision_source=decision.decision_source,
                search_type=decision.search_type,
                freshness=decision.freshness,
                confidence=decision.confidence,
            )
            session.add(event)
            await session.commit()

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
            await session.commit()
