import asyncio
from app.db.repositories import EventRepository

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

from app.api.routes import health, assistant

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError

from contextlib import asynccontextmanager
from app.core.observability import get_langfuse_client
# from prometheus_client import make_asgi_app
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from app.db.database import check_db_connection, close_db_connection

setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")

    # Verify PostgreSQL connectivity
    try:
        await check_db_connection()
        logger.info("PostgreSQL connection established successfully.")
    # except Exception:
    #     logger.exception("PostgreSQL connection failed during startup.")
    #     raise

    # yield

    except Exception:
        logger.exception("PostgreSQL connection failed during startup.")
        raise

    recovery_task = asyncio.create_task(
        stale_request_recovery_worker(),
        name="stale-request-recovery",
    )

    logger.info("Stale request recovery worker started.")

    try:
        yield

    finally:
        logger.info("Application shutdown")

        recovery_task.cancel()

        try:
            await recovery_task
        except asyncio.CancelledError:
            logger.info("Stale request recovery worker stopped.")



    logger.info("Application shutdown")

    # Close PostgreSQL connection pool
    try:
        await close_db_connection()
        logger.info("PostgreSQL connections disposed successfully.")
    except Exception:
        logger.exception("Failed to dispose PostgreSQL connections.")

    # Flush Langfuse events
    logger.info("Flushing Langfuse events")

    langfuse = get_langfuse_client()

    if langfuse:
        try:
            langfuse.flush()
            logger.info("Langfuse events flushed successfully.")
        except Exception:
            logger.exception("Failed to flush Langfuse events.")

async def stale_request_recovery_worker():
    """Periodically recover stale assistant requests."""

    repository = EventRepository()

    while True:
        try:
            recovered_count = (
                await repository.recover_stale_assistant_requests()
            )

            if recovered_count > 0:
                logger.warning(
                    "Stale assistant requests recovered | count=%s",
                    recovered_count,
                )
            else:
                logger.debug("Stale request recovery completed | recovered=0")

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Stale assistant request recovery failed"
            )

        await asyncio.sleep(
            settings.stale_recovery_interval_seconds
        )

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise AI Operations Assistant "
        "API foundation"
    ),
    debug=settings.debug,
    lifespan=lifespan,
)

# Prometheus metrics endpoint
# metrics_app = make_asgi_app()
# app.mount("/metrics", metrics_app)
# Prometheus metrics endpoint
@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

@app.exception_handler(ApplicationError)
async def application_error_handler(
    request: Request,
    exc: ApplicationError
):

    logger.error(
        "Application error: %s",
        exc.code
    )

    return JSONResponse(
        status_code=503,
        content={
            "error_code": exc.code,
            "message": "The requested service is temporarily unavailable.",
            "request_id": None
        }
    )

app.include_router(
    health.router,
    prefix=settings.api_prefix
)

app.include_router(
    assistant.router,
    prefix=settings.api_prefix
)


@app.get("/")
async def root():

    logger.info("Root endpoint accessed")

    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "message": "Application is running"
    }