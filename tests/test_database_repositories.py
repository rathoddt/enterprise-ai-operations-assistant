from datetime import datetime, timedelta, timezone
import asyncio
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import URL, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.database import Base
from app.db.models import (
    AssistantRequestEvent,
    SearchDecisionEvent,
    WebSearchExecutionEvent,
)
from app.db.repositories import EventRepository
from app.web_search.routing import SearchDecision
import app.db.repositories as repositories


# @asynccontextmanager
# async def test_database():
@asynccontextmanager
async def database_context():    

    test_database_url = URL.create(
        drivername="postgresql+asyncpg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database="eaoa_test",
    )

    engine = create_async_engine(
        test_database_url,
        echo=False,
    )

    TestSessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    original_session_factory = repositories.AsyncSessionLocal

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        repositories.AsyncSessionLocal = TestSessionLocal

        yield TestSessionLocal

    finally:
        repositories.AsyncSessionLocal = original_session_factory

        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
        finally:
            await engine.dispose()


def test_event_repository_persists_all_events():

    async def run_test():

        # async with test_database() as TestSessionLocal:
        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            # 1. Create parent assistant request
            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="integration-test-conversation",
                provider="openai",
            )

            # 2. Update assistant request
            await repository.update_assistant_request(
                event_id=event_id,
                model="gpt-5",
                status="success",
                latency_ms=1250.5,
                input_tokens=100,
                output_tokens=50,
                provider_request_id="test-request-123",
                provider_response_id="test-response-456",
                finish_reason="end_turn",
                is_truncated=False,
            )

            # 3. Record search decision
            decision = SearchDecision(
                requires_search=True,
                reason="Integration test",
                search_query="Azure AI Foundry",
                search_type="general",
                freshness="live",
                confidence=0.95,
                decision_source="rules",
            )

            await repository.record_search_decision(
                event_id=event_id,
                decision=decision,
            )

            # 4. Record successful web-search execution
            await repository.record_web_search_execution(
                event_id=event_id,
                provider="tavily",
                status="success",
                response_time=1.25,
                result_count=5,
                answer_available=True,
            )

            # 5. Verify actual PostgreSQL records
            async with TestSessionLocal() as session:

                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert parent is not None
                assert parent.conversation_id == "integration-test-conversation"
                assert parent.provider == "openai"
                assert parent.model == "gpt-5"
                assert parent.status == "success"
                assert parent.latency_ms == 1250.5
                assert parent.input_tokens == 100
                assert parent.output_tokens == 50

                search_events = (
                    await session.execute(
                        select(SearchDecisionEvent).where(
                            SearchDecisionEvent.request_event_id == event_id
                        )
                    )
                ).scalars().all()

                assert len(search_events) == 1
                assert search_events[0].decision == "search"
                assert search_events[0].confidence == 0.95

                web_events = (
                    await session.execute(
                        select(WebSearchExecutionEvent).where(
                            WebSearchExecutionEvent.request_event_id == event_id
                        )
                    )
                ).scalars().all()

                assert len(web_events) == 1
                assert web_events[0].provider == "tavily"
                assert web_events[0].status == "success"
                assert web_events[0].result_count == 5
                assert web_events[0].answer_available is True
                assert web_events[0].response_time == 1.25

                # Verify parent-child UUID relationships
                assert search_events[0].request_event_id == parent.id
                assert web_events[0].request_event_id == parent.id

    asyncio.run(run_test())


def test_web_search_failure_event_persists_in_postgres():

    async def run_test():

        # async with test_database() as TestSessionLocal:
        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            # Create parent assistant request
            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="failed-search-test",
                provider="openai",
            )

            # Record failed web-search execution
            await repository.record_web_search_execution(
                event_id=event_id,
                provider="tavily",
                status="error",
                response_time=2.45,
                error_type="RuntimeError",
            )

            # Verify persisted failure event
            async with TestSessionLocal() as session:

                result = await session.execute(
                    select(WebSearchExecutionEvent).where(
                        WebSearchExecutionEvent.request_event_id == event_id
                    )
                )

                failure_event = result.scalar_one()

                assert failure_event.request_event_id == event_id
                assert failure_event.provider == "tavily"
                assert failure_event.status == "error"
                assert failure_event.response_time == 2.45
                assert failure_event.error_type == "RuntimeError"
                assert failure_event.result_count is None
                assert failure_event.answer_available is None

    asyncio.run(run_test())


def test_foreign_key_rejects_events_without_parent():

    async def run_test():

        # async with test_database():
        async with database_context():

            repository = EventRepository()

            # UUID does not exist in assistant_request_events
            invalid_event_id = uuid.uuid4()

            decision = SearchDecision(
                requires_search=True,
                reason="Foreign key integration test",
                search_query="Azure AI Foundry",
                search_type="general",
                freshness="live",
                confidence=0.95,
                decision_source="rules",
            )

            # Search decision must not accept an invalid parent UUID
            with pytest.raises(IntegrityError):
                await repository.record_search_decision(
                    event_id=invalid_event_id,
                    decision=decision,
                )

            # Web-search execution must not accept an invalid parent UUID
            with pytest.raises(IntegrityError):
                await repository.record_web_search_execution(
                    event_id=invalid_event_id,
                    provider="tavily",
                    status="success",
                    response_time=1.2,
                    result_count=5,
                    answer_available=True,
                )

    asyncio.run(run_test())

def test_assistant_request_timestamps_are_created():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="timestamp-creation-test",
                provider="openai",
            )

            async with TestSessionLocal() as session:

                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert parent is not None
                assert parent.created_at is not None
                assert parent.updated_at is not None

                # Both timestamps should be timezone-aware.
                assert parent.created_at.tzinfo is not None
                assert parent.updated_at.tzinfo is not None

                # Initial timestamps should be equal or nearly equal.
                assert parent.updated_at >= parent.created_at

    asyncio.run(run_test())

def test_assistant_request_updated_at_changes():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="timestamp-update-test",
                provider="openai",
            )

            async with TestSessionLocal() as session:

                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                original_updated_at = parent.updated_at

            # Ensure the next transaction has a later timestamp.
            await asyncio.sleep(0.05)

            await repository.update_assistant_request(
                event_id=event_id,
                model="gpt-5",
                status="success",
                latency_ms=1200,
            )

            async with TestSessionLocal() as session:

                updated_parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert updated_parent is not None
                assert updated_parent.updated_at > original_updated_at

    asyncio.run(run_test())


def test_recover_stale_assistant_request():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="stale-request-test",
                provider="openai",
            )

            stale_timestamp = datetime.now(timezone.utc) - timedelta(
                minutes=10
            )

            await repository.update_assistant_request(
                event_id=event_id,
                updated_at=stale_timestamp,
            )

            recovered_count = (
                await repository.recover_stale_assistant_requests()
            )

            assert recovered_count == 1

            async with TestSessionLocal() as session:

                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert parent.status == "incomplete"
                assert parent.incomplete_reason == "stale_request_recovery"
                assert parent.updated_at > stale_timestamp

    asyncio.run(run_test())

def test_recovery_preserves_recent_and_completed_requests():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()

            recent_id = uuid.uuid4()
            completed_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=recent_id,
                conversation_id="recent-request-test",
                provider="openai",
            )

            await repository.create_assistant_request(
                event_id=completed_id,
                conversation_id="completed-request-test",
                provider="anthropic",
            )

            await repository.update_assistant_request(
                event_id=completed_id,
                model="claude-sonnet-5-5",
                status="success",
            )

            recovered_count = (
                await repository.recover_stale_assistant_requests()
            )

            assert recovered_count == 0

            async with TestSessionLocal() as session:

                recent = await session.get(
                    AssistantRequestEvent,
                    recent_id,
                )

                completed = await session.get(
                    AssistantRequestEvent,
                    completed_id,
                )

                assert recent.status == "in_progress"
                assert completed.status == "success"

    asyncio.run(run_test())

def test_heartbeat_updates_active_assistant_request():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="heartbeat-test",
                provider="openai",
            )

            async with TestSessionLocal() as session:
                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )
                original_updated_at = parent.updated_at

            await asyncio.sleep(0.05)

            heartbeat_result = (
                await repository.heartbeat_assistant_request(event_id)
            )

            assert heartbeat_result is True

            async with TestSessionLocal() as session:
                updated_parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert updated_parent.status == "in_progress"
                assert updated_parent.updated_at > original_updated_at

    asyncio.run(run_test())

def test_heartbeat_does_not_update_completed_request():

    async def run_test():

        async with database_context() as TestSessionLocal:

            repository = EventRepository()
            event_id = uuid.uuid4()

            await repository.create_assistant_request(
                event_id=event_id,
                conversation_id="completed-heartbeat-test",
                provider="openai",
            )

            await repository.update_assistant_request(
                event_id=event_id,
                model="gpt-5",
                status="success",
            )

            async with TestSessionLocal() as session:
                parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )
                original_updated_at = parent.updated_at

            await asyncio.sleep(0.05)

            heartbeat_result = (
                await repository.heartbeat_assistant_request(event_id)
            )

            assert heartbeat_result is False

            async with TestSessionLocal() as session:
                updated_parent = await session.get(
                    AssistantRequestEvent,
                    event_id,
                )

                assert updated_parent.status == "success"
                assert updated_parent.updated_at == original_updated_at

    asyncio.run(run_test())