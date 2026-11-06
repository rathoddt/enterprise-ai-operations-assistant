import asyncio
import logging

from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def call_with_retry(
    operation: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    timeout_seconds: float = 10,
    base_delay: float = 1
) -> T:

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    for attempt in range(1, max_attempts + 1):

        try:

            return await asyncio.wait_for(
                operation(),
                timeout=timeout_seconds
            )

        except (TimeoutError, ConnectionError):

            logger.warning(
                "Operation failed. Attempt %s/%s",
                attempt,
                max_attempts
            )

            if attempt == max_attempts:
                raise

            delay = base_delay * (2 ** (attempt - 1))

            await asyncio.sleep(delay)