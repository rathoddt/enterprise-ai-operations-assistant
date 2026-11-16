
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

DOCUMENT_UPLOAD_ENDPOINT = (
    f"{API_BASE_URL.rstrip('/')}/api/v1/documents/upload"
)

MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

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
        logger.info(
            "API request started | provider=%s timeout=%s",
            provider,
            REQUEST_TIMEOUT,
        )
        response = httpx.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        logger.info(
            "API response received | provider=%s status=%s",
            provider,
            response.status_code,
        )        

        response.raise_for_status()
        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000        
        logger.info(
            "Frontend API completed | provider=%s latency_ms=%.2f",
            provider,
            elapsed_ms,
            REQUEST_TIMEOUT,
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


def upload_document(
    filename: str,
    file_content: bytes,
) -> dict:
    """Upload a document to the RAG ingestion API."""

    if not filename:
        raise APIClientError("Filename cannot be empty.")

    if not file_content:
        raise APIClientError("Selected file is empty.")

    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise APIClientError(
            f"File exceeds the {MAX_UPLOAD_SIZE_MB} MB limit."
        )

    try:
        response = httpx.post(
            DOCUMENT_UPLOAD_ENDPOINT,
            files={
                "file": (
                    filename,
                    file_content,
                    "application/octet-stream",
                )
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
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
            f"Unable to connect to document upload API: {exc}"
        ) from exc