import pytest
import asyncio


from app.core.resilience import call_with_retry


def test_retry_succeeds_after_transient_failure():

    attempts = 0

    async def unstable_operation():

        nonlocal attempts

        attempts += 1

        if attempts < 3:
            raise ConnectionError("Temporary network issue")

        return "Success"

    result = asyncio.run(
        call_with_retry(
            operation=unstable_operation,
            max_attempts=3,
            base_delay=0.001
        )
    )

    assert result == "Success"
    assert attempts == 3



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