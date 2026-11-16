
# # import streamlit as st

# # from concurrent.futures import ThreadPoolExecutor, as_completed

# # from app.models.schemas import DEFAULT_SYSTEM_PROMPT

# import sys
# from pathlib import Path

# import streamlit as st

# from concurrent.futures import ThreadPoolExecutor, as_completed
# import logging
# from frontend.api_client import (
#     send_chat_message,
#     upload_document,
#     APIClientError,
# )

import sys
from pathlib import Path
import logging

import streamlit as st

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.api_client import (
    send_chat_message,
    upload_document,
    APIClientError,
)

from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_SYSTEM_PROMPT = (
    "Provide a concise, well-structured answer. "
    "Use approximately 400–600 words unless the question "
    "requires more detail. Avoid unnecessary repetition."
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Enterprise AI Operations Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================================================
# PROVIDER CONFIGURATION
# ==================================================

PROVIDERS = {
    "openai": {
        "name": "GPT-5",
        "deployment": "gpt-5",
        "icon": "🟢",
    },
    "anthropic": {
        "name": "Claude Sonnet 5.5",
        "deployment": "claude-sonnet-5-5",
        "icon": "🔵",
    },
}


# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

def initialize_session_state():

    defaults = {
        "openai_history": [],
        "anthropic_history": [],
        "openai_conversation_id": None,
        "anthropic_conversation_id": None,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ==================================================
# HELPER: CLEAR CONVERSATION
# ==================================================

def clear_conversation():

    st.session_state["openai_history"] = []
    st.session_state["anthropic_history"] = []

    st.session_state["openai_conversation_id"] = None
    st.session_state["anthropic_conversation_id"] = None

    st.rerun()


# ==================================================
# HELPER: DISPLAY MODEL RESPONSE
# ==================================================

def display_response(message: dict):

    metadata = message.get("metadata") or {}

    if message.get("error"):

        st.error(message["content"])
        return

    st.markdown(message["content"])

    if not metadata:
        return

    st.divider()

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    latency = metadata.get("latency_ms")
    input_tokens = metadata.get("input_tokens")
    output_tokens = metadata.get("output_tokens")

    with metric_col1:

        if latency is not None:

            st.metric(
                "Latency",
                f"{latency / 1000:.2f}s",
            )

    with metric_col2:

        if input_tokens is not None:

            st.metric(
                "Input tokens",
                input_tokens,
            )

    with metric_col3:

        if output_tokens is not None:

            st.metric(
                "Output tokens",
                output_tokens,
            )

    with st.expander("Request and response details"):

        st.write(
            "**Provider:**",
            metadata.get("provider", "Unknown"),
        )

        st.write(
            "**Model:**",
            metadata.get("model", "Unknown"),
        )

        st.write(
            "**Status:**",
            metadata.get("status", "Unknown"),
        )

        st.code(
            metadata.get("request_id") or "Not available",
            language=None,
        )

        st.caption("Request ID")

        st.code(
            metadata.get("response_id") or "Not available",
            language=None,
        )

        st.caption("Response ID")

        st.write(
            "**Finish reason:**",
            metadata.get("finish_reason", "Unknown"),
        )

        if metadata.get("is_truncated", False):
            st.warning(
                "Response may be incomplete: the model reached "
                "its maximum output-token limit."
            )
        else:
            st.success("Model completed its response.")

        st.write(
            "**Incomplete reason:**",
            metadata.get("incomplete_reason") or "None"
        )


# ==================================================
# HELPER: DISPLAY CONVERSATION HISTORY
# ==================================================

def display_history(provider_key: str):

    history_key = f"{provider_key}_history"

    history = st.session_state[history_key]

    if not history:

        st.info(
            "No conversation yet. Enter a prompt below."
        )

        return

    for message in history:

        with st.chat_message(message["role"]):

            display_response(message)


# ==================================================
# HELPER: CALL A SINGLE PROVIDER
# ==================================================
def call_provider(
    provider_key: str,
    system_prompt: str,
    user_prompt: str,
    conversation_id: str | None,
):

    return send_chat_message(
        question=user_prompt,
        provider=provider_key,
        system_prompt=system_prompt,
        conversation_id=conversation_id,
    )

# ==================================================
# HELPER: SAVE PROVIDER RESULT
# ==================================================

def save_provider_result(
    provider_key: str,
    result: dict,
):

    history_key = f"{provider_key}_history"
    conversation_key = f"{provider_key}_conversation_id"

    st.session_state[conversation_key] = (
        result.get("conversation_id")
    )

    st.session_state[history_key].append({

        "role": "assistant",

        "content": result.get(
            "answer",
            "No answer returned.",
        ),

        "metadata": result.get("metadata") or {},

    })


# ==================================================
# HELPER: SAVE PROVIDER ERROR
# ==================================================

def save_provider_error(
    provider_key: str,
    error: str,
):

    history_key = f"{provider_key}_history"

    st.session_state[history_key].append({

        "role": "assistant",

        "content": error,

        "error": True,

    })


# ==================================================
# HELPER: EXECUTE MODEL REQUESTS
# ==================================================

def execute_requests(
    selected_providers: list,
    system_prompt: str,
    user_prompt: str,
):

    # All Streamlit session state access happens
    # on the main Streamlit script thread.

    conversation_ids = {
        provider_key: st.session_state[
            f"{provider_key}_conversation_id"
        ]
        for provider_key in selected_providers
    }

    # Add user prompt to selected model histories.

    for provider_key in selected_providers:

        st.session_state[
            f"{provider_key}_history"
        ].append({
            "role": "user",
            "content": user_prompt,
        })

    results = {}
    errors = {}

    # Execute selected providers concurrently.

    with st.spinner("Waiting for model responses..."):

        with ThreadPoolExecutor(
            max_workers=len(selected_providers)
        ) as executor:

            futures = {
                executor.submit(
                    call_provider,
                    provider_key,
                    system_prompt,
                    user_prompt,
                    conversation_ids[provider_key],
                ): provider_key

                for provider_key in selected_providers
            }

            for future in as_completed(futures):

                provider_key = futures[future]

                try:
                    logger.info(
                        "Future completed | provider=%s",
                        provider_key,
                    )                    
                    results[provider_key] = future.result()

                except APIClientError as exc:
                    logger.exception(
                        "API client error | provider=%s",
                        provider_key,
                    )                    
                    errors[provider_key] = str(exc)

                except Exception as exc:
                    logger.exception(
                        "Unexpected future error | provider=%s",
                        provider_key,
                    )                    
                    errors[provider_key] = (
                        f"Unexpected error: {exc}"
                    )

    # Update Streamlit session state on the main thread.

    for provider_key, result in results.items():

        save_provider_result(
            provider_key,
            result,
        )

    for provider_key, error in errors.items():

        save_provider_error(
            provider_key,
            error,
        )




# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("🤖 Enterprise AI Operations Assistant")

st.caption(
    "Compare Azure AI Foundry GPT-5 and Claude Sonnet 5.5"
)

st.divider()

# ==================================================
# DOCUMENT UPLOAD AND INGESTION
# ==================================================

st.subheader("📚 Document Knowledge Base")

st.caption(
    "Upload PDF, DOCX, TXT or Markdown documents "
    "to extract, chunk and generate embeddings."
)

uploaded_file = st.file_uploader(
    "Choose a document",
    type=["pdf", "docx", "txt", "md"],
    help="Maximum file size: 20 MB",
)

if st.button(
    "Upload and Index Document",
    disabled=uploaded_file is None,
    type="primary",
):

    try:
        with st.spinner(
            "Uploading document and generating embeddings..."
        ):

            result = upload_document(
                filename=uploaded_file.name,
                file_content=uploaded_file.getvalue(),
            )

        st.success(
            result.get(
                "message",
                "Document uploaded and processed successfully.",
            )
        )

        document = result.get("document") or {}
        chunks = result.get("chunks") or []

        if document:
            with st.expander("Document details"):
                st.json(document)

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.metric("Chunks created", len(chunks))

        with metric_col2:
            st.metric(
                "Embeddings generated",
                result.get("embedding_count", 0),
            )

        with metric_col3:
            st.metric(
                "Embedding dimensions",
                result.get("embedding_dimensions", 0),
            )

    except APIClientError as exc:
        st.error(f"Document upload failed: {exc}")

    except Exception as exc:
        logger.exception("Unexpected document upload error")
        st.error(f"Unexpected error: {exc}")

# ==================================================
# SYSTEM PROMPT CONFIGURATION
# ==================================================

st.subheader("⚙️ System Prompt")


system_prompt = st.text_area(
    "Define model behaviour and response instructions",
    height=120,
    max_chars=8000,
    key="system_prompt",
)

st.caption(
    "The same system prompt is applied to every selected model."
)


# ==================================================
# USER PROMPT AND SUBMISSION CONTROLS
# ==================================================

st.subheader("💬 User Prompt")

with st.form("user_prompt_form"):

    user_prompt = st.text_area(

        "Enter your question or task",

        placeholder=(
            "Example: Explain RAG architecture "
            "for an enterprise application."
        ),

        height=110,

        max_chars=2000,

        key="user_prompt",

    )

    button_col1, button_col2, button_col3 = st.columns(3)

    with button_col1:

        compare_button = st.form_submit_button(

            "⚖️ Compare Both Models",

            type="primary",

            use_container_width=True,

        )

    with button_col2:

        openai_button = st.form_submit_button(

            "🟢 GPT-5 Only",

            use_container_width=True,

        )

    with button_col3:

        anthropic_button = st.form_submit_button(

            "🔵 Claude Only",

            use_container_width=True,

        )


# ==================================================
# PROCESS SUBMISSION
# ==================================================

selected_providers = []

if compare_button:

    selected_providers = [
        "openai",
        "anthropic",
    ]

elif openai_button:

    selected_providers = [
        "openai",
    ]

elif anthropic_button:

    selected_providers = [
        "anthropic",
    ]


if selected_providers:

    if not user_prompt.strip():

        st.warning(
            "Please enter a user prompt before submitting."
        )

    elif not system_prompt.strip():

        st.warning(
            "Please enter a system prompt before submitting."
        )

    else:

        execute_requests(
            selected_providers=selected_providers,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        st.rerun()


# ==================================================
# RESPONSE DISPLAY
# ==================================================

st.divider()

st.subheader("📊 Model Responses")

openai_col, anthropic_col = st.columns(
    2,
    gap="large",
)


# ==================================================
# LEFT COLUMN: GPT-5
# ==================================================

with openai_col:

    st.markdown("### 🟢 GPT-5")

    st.caption(
        f"Azure AI Foundry deployment: "
        f"{PROVIDERS['openai']['deployment']}"
    )

    st.divider()

    display_history("openai")


# ==================================================
# RIGHT COLUMN: CLAUDE
# ==================================================

with anthropic_col:

    st.markdown("### 🔵 Claude Sonnet 5.5")

    st.caption(
        f"Azure AI Foundry deployment: "
        f"{PROVIDERS['anthropic']['deployment']}"
    )

    st.divider()

    display_history("anthropic")


# ==================================================
# FOOTER / CONTROLS
# ==================================================

st.divider()

footer_col1, footer_col2 = st.columns([4, 1])

with footer_col1:

    st.caption(
        "Enterprise AI Operations Assistant | "
        "FastAPI + Streamlit + Azure AI Foundry"
    )

with footer_col2:

    if st.button(
        "🗑️ Clear Conversations",
        use_container_width=True,
    ):

        clear_conversation()

