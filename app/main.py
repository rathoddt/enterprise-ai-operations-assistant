from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

from app.api.routes import health, assistant


setup_logging()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise AI Operations Assistant "
        "API foundation"
    ),
    debug=settings.debug
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