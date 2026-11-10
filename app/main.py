from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

from app.api.routes import health, assistant

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError

from contextlib import asynccontextmanager
from app.core.observability import get_langfuse_client
from prometheus_client import make_asgi_app

setup_logging()

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")

    yield

    logger.info("Application shutdown: flushing Langfuse events")

    langfuse = get_langfuse_client()

    if langfuse:
        try:
            langfuse.flush()
            logger.info("Langfuse events flushed successfully.")
        except Exception:
            logger.exception("Failed to flush Langfuse events.")

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
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

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