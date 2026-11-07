
import os
import httpx

import time
import logging

logger = logging.getLogger(__name__)

# ==================================================
# API CONFIGURATION
# ==================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

CHAT_ENDPOINT = (
    f"{API_BASE_URL.rstrip('/')}/api/v1/assistant/chat"
)

REQUEST_TIMEOUT = 120.0


# ==================================================
# CUSTOM EXCEPTION
# ==================================================

class APIClientError(Exception):
    """Raised when the FastAPI backend request fails."""


# ==================================================
# SEND CHAT MESSAGE
# ==================================================

def send_chat_message(
    question: str,
    provider: str,
    system_prompt: str,
    conversation_id: str | None = None,
) -> dict:
    """
    Send a chat request to the FastAPI backend.

    Args:
        question: User prompt.
        provider: openai or anthropic.
        system_prompt: Instructions for the LLM.
        conversation_id: Existing conversation ID.

    Returns:
        API response containing answer and metadata.
    """

    payload = {
        "question": question,
        "system_prompt": system_prompt,
        "provider": provider,
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id


    start_time = time.perf_counter()
    try:

        response = httpx.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000        
        logger.info(
            "Frontend API completed | provider=%s latency_ms=%.2f",
            provider,
            elapsed_ms,
        )
        return response.json()

    except httpx.HTTPStatusError as exc:

        try:
            error_detail = exc.response.json()
        except ValueError:
            error_detail = exc.response.text

        raise APIClientError(
            f"HTTP {exc.response.status_code}: {error_detail}"
        ) from exc

    except httpx.RequestError as exc:

        raise APIClientError(
            f"Unable to connect to FastAPI backend. "
            f"URL: {CHAT_ENDPOINT}. Error: {exc}"
        ) from exc


# ------------------- v1 -------------------
# import os
# import httpx

# API_BASE_URL = os.getenv(
#     "API_BASE_URL",
#     "http://127.0.0.1:8000",
# )

# CHAT_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/api/v1/assistant/chat"

# REQUEST_TIMEOUT = 120.0


# class APIClientError(Exception):
#     """Raised when the FastAPI backend returns an error."""

#     def send_chat_message(
#         question: str,
#         provider: str,
#         system_prompt: str,
#         conversation_id: str | None = None,
#     ) -> dict:

#         payload = {
#             "question": question,
#             "system_prompt": system_prompt,
#             "provider": provider,
#         }

#         if conversation_id:
#             payload["conversation_id"] = conversation_id

#         try:
#             response = httpx.post(
#                 CHAT_ENDPOINT,
#                 json=payload,
#                 timeout=REQUEST_TIMEOUT,
#             )

#             response.raise_for_status()

#             return response.json()

#         except httpx.HTTPStatusError as exc:
#             try:
#                 error_detail = exc.response.json()
#             except ValueError:
#                 error_detail = exc.response.text

#             raise APIClientError(
#                 f"Backend returned HTTP "
#                 f"{exc.response.status_code}: {error_detail}"
#             ) from exc

#         except httpx.RequestError as exc:
#             raise APIClientError(
#                 f"Unable to connect to FastAPI backend: {exc}"
#             ) from exc
    
# ------------------- v0 -------------------
# def send_chat_message(
#     question: str,
#     provider: str,
#     conversation_id: str | None = None,
# ) -> dict:
#     """
#     Send a chat request to the FastAPI backend.

#     Args:
#         question: User's question.
#         provider: LLM provider ('openai' or 'anthropic').
#         conversation_id: Provider-specific conversation ID.

#     Returns:
#         Chat API response as a dictionary.
#     """

#     payload = {
#         "question": question,
#         "provider": provider,
#     }

#     if conversation_id:
#         payload["conversation_id"] = conversation_id

#     try:
#         response = httpx.post(
#             CHAT_ENDPOINT,
#             json=payload,
#             timeout=REQUEST_TIMEOUT,
#         )

#         response.raise_for_status()

#         return response.json()

#     except httpx.HTTPStatusError as exc:
#         try:
#             error_detail = exc.response.json()
#         except ValueError:
#             error_detail = exc.response.text

#         raise APIClientError(
#             f"Backend returned HTTP {exc.response.status_code}: "
#             f"{error_detail}"
#         ) from exc

#     except httpx.RequestError as exc:
#         raise APIClientError(
#             f"Unable to connect to FastAPI backend at "
#             f"{CHAT_ENDPOINT}. Is the backend running? Details: {exc}"
#         ) from exc
