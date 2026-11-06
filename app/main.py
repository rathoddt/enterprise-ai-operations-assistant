from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

from app.api.routes import health, assistant

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError

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