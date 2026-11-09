import logging
from functools import lru_cache

from langfuse import Langfuse

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_langfuse_client() -> Langfuse | None:
    """
    Return a reusable Langfuse client.

    Observability is disabled when credentials are not configured.
    """

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning(
            "Langfuse credentials not configured. Observability disabled."
        )
        return None

    try:
        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
            environment=settings.environment,
        )

        logger.info("Langfuse client initialized successfully.")
        return client

    except Exception:
        logger.exception("Failed to initialize Langfuse client.")
        return None