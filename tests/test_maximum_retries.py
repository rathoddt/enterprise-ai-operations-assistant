import pytest


def test_retry_fails_after_max_attempts():

    attempts = 0

    async def failing_operation():

        nonlocal attempts
        attempts += 1

        raise ConnectionError("Service unavailable")

    with pytest.raises(ConnectionError):

        asyncio.run(
            call_with_retry(
                operation=failing_operation,
                max_attempts=3,
                base_delay=0.001
            )
        )

    assert attempts == 3