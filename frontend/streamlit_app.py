
# import streamlit as st

# from concurrent.futures import ThreadPoolExecutor, as_completed

# from app.models.schemas import DEFAULT_SYSTEM_PROMPT

import sys
from pathlib import Path

import streamlit as st

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Frontend API client
from frontend.api_client import (
    send_chat_message,
    APIClientError,
)

DEFAULT_SYSTEM_PROMPT = (
    "Provide a concise, well-structured answer. "
    "Use approximately 400–600 words unless the question "
    "requires more detail. Avoid unnecessary repetition."
)

from api_client import (
    send_chat_message,
    APIClientError,
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
# ------------ v0 ------------
# def call_provider(
#     provider_key: str,
#     system_prompt: str,
#     user_prompt: str,
# ):

#     conversation_key = f"{provider_key}_conversation_id"

#     return send_chat_message(
#         question=user_prompt,
#         provider=provider_key,
#         system_prompt=system_prompt,
#         conversation_id=st.session_state[conversation_key],
#     )


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


# ---------------- v0 ----------------
# def execute_requests(
#     selected_providers: list,
#     system_prompt: str,
#     user_prompt: str,
# ):

#     # Add user prompt only to the selected model histories.

#     for provider_key in selected_providers:

#         history_key = f"{provider_key}_history"

#         st.session_state[history_key].append({

#             "role": "user",

#             "content": user_prompt,

#         })

#     results = {}
#     errors = {}

#     # Compare both providers concurrently.

#     if len(selected_providers) == 2:

#         with st.spinner(
#             "Waiting for GPT-5 and Claude responses..."
#         ):

#             with ThreadPoolExecutor(max_workers=2) as executor:

#                 futures = {

#                     executor.submit(
#                         call_provider,
#                         provider_key,
#                         system_prompt,
#                         user_prompt,
#                     ): provider_key

#                     for provider_key in selected_providers

#                 }

#                 for future in as_completed(futures):

#                     provider_key = futures[future]

#                     try:

#                         results[provider_key] = future.result()

#                     except APIClientError as exc:

#                         errors[provider_key] = str(exc)

#                     except Exception as exc:

#                         errors[provider_key] = (
#                             f"Unexpected error: {exc}"
#                         )

#     else:

#         # Single-provider execution.

#         provider_key = selected_providers[0]

#         with st.spinner(
#             f"Waiting for {PROVIDERS[provider_key]['name']}..."
#         ):

#             try:

#                 results[provider_key] = call_provider(
#                     provider_key,
#                     system_prompt,
#                     user_prompt,
#                 )

#             except APIClientError as exc:

#                 errors[provider_key] = str(exc)

#             except Exception as exc:

#                 errors[provider_key] = (
#                     f"Unexpected error: {exc}"
#                 )

#     # Save successful responses.

#     for provider_key, result in results.items():

#         save_provider_result(
#             provider_key,
#             result,
#         )

#     # Save errors independently.

#     for provider_key, error in errors.items():

#         save_provider_error(
#             provider_key,
#             error,
#         )


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("🤖 Enterprise AI Operations Assistant")

st.caption(
    "Compare Azure AI Foundry GPT-5 and Claude Sonnet 5.5"
)

st.divider()


# ==================================================
# SYSTEM PROMPT CONFIGURATION
# ==================================================

st.subheader("⚙️ System Prompt")

# system_prompt = st.text_area(

#     "Define model behaviour and response instructions",

#     value=st.session_state["system_prompt"],

#     height=120,

#     max_chars=8000,

#     key="system_prompt",

#     help=(
#         "These instructions are passed to both models "
#         "using their native system/instructions parameters."
#     ),
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

# ---------------------- v0.1.0 ----------------------
# import streamlit as st
# from concurrent.futures import ThreadPoolExecutor

# from app.models.schemas import DEFAULT_SYSTEM_PROMPT

# # from frontend.api_client import (
# #     send_chat_message,
# #     APIClientError,
# # )

# from api_client import (
#     send_chat_message,
#     APIClientError,
# )


# # --------------------------------------------------
# # Page configuration
# # --------------------------------------------------

# st.set_page_config(
#     page_title="Enterprise AI Operations Assistant",
#     page_icon="🤖",
#     layout="wide",
# )

# st.title("🤖 Enterprise AI Operations Assistant")
# st.caption(
#     "Compare responses from Azure AI Foundry GPT-5 "
#     "and Claude Sonnet 5.5"
# )


# # --------------------------------------------------
# # Provider configuration
# # --------------------------------------------------

# PROVIDERS = {
#     "openai": {
#         "name": "GPT-5",
#         "deployment": "gpt-5",
#         "icon": "🟢",
#     },
#     "anthropic": {
#         "name": "Claude Sonnet 5.5",
#         "deployment": "claude-sonnet-5-5",
#         "icon": "🔵",
#     },
# }


# # --------------------------------------------------
# # Session state initialization
# # --------------------------------------------------

# def initialize_session_state():

#     defaults = {
#         "openai_history": [],
#         "anthropic_history": [],
#         "openai_conversation_id": None,
#         "anthropic_conversation_id": None,
#     }

#     for key, value in defaults.items():
#         if key not in st.session_state:
#             st.session_state[key] = value


# initialize_session_state()


# # --------------------------------------------------
# # Helper: display model response
# # --------------------------------------------------

# def display_response(provider_key: str, response: dict):

#     metadata = response.get("metadata") or {}

#     answer = response.get("answer", "No answer returned.")

#     st.markdown(answer)

#     st.divider()

#     col1, col2 = st.columns(2)

#     with col1:
#         latency = metadata.get("latency_ms")

#         if latency is not None:
#             st.metric(
#                 "Latency",
#                 f"{latency / 1000:.2f} sec",
#             )

#     with col2:
#         output_tokens = metadata.get("output_tokens")

#         if output_tokens is not None:
#             st.metric(
#                 "Output tokens",
#                 output_tokens,
#             )

#     input_tokens = metadata.get("input_tokens")

#     if input_tokens is not None:
#         st.caption(f"Input tokens: {input_tokens}")

#     with st.expander("Request and response details"):

#         st.write(
#             "Provider:",
#             metadata.get("provider", provider_key),
#         )

#         st.write(
#             "Model:",
#             metadata.get("model", "Unknown"),
#         )

#         st.write(
#             "Status:",
#             metadata.get("status", response.get("status")),
#         )

#         st.write(
#             "Request ID:",
#             metadata.get("request_id", "Not available"),
#         )

#         st.write(
#             "Response ID:",
#             metadata.get("response_id", "Not available"),
#         )


# # --------------------------------------------------
# # Helper: display conversation history
# # --------------------------------------------------

# def display_history(provider_key: str):

#     history_key = f"{provider_key}_history"

#     for message in st.session_state[history_key]:

#         with st.chat_message(message["role"]):

#             if message.get("error"):
#                 st.error(message["content"])

#             else:
#                 st.markdown(message["content"])

#                 if message.get("metadata"):
#                     metadata = message["metadata"]

#                     latency = metadata.get("latency_ms")
#                     output_tokens = metadata.get("output_tokens")

#                     details = []

#                     if latency is not None:
#                         details.append(
#                             f"Latency: {latency / 1000:.2f}s"
#                         )

#                     if output_tokens is not None:
#                         details.append(
#                             f"Output tokens: {output_tokens}"
#                         )

#                     if details:
#                         st.caption(" | ".join(details))


# # --------------------------------------------------
# # Sstem prompt and user prompt input
# # --------------------------------------------------

# st.subheader("Prompt Configuration")

# system_prompt = st.text_area(
#     "System Prompt",
#     value=st.session_state.get(
#         "system_prompt",
#         DEFAULT_SYSTEM_PROMPT,
#     ),
#     height=120,
#     key="system_prompt",
#     help="Instructions that control model behaviour.",
# )

# user_prompt = st.text_area(
#     "User Prompt",
#     placeholder="Enter your question or task here...",
#     height=100,
#     key="user_prompt",
# )

# compare = st.button(
#     "Compare Both Models",
#     type="primary",
#     use_container_width=True,
# )

# # --------------------------------------------------
# # Header and controls
# # --------------------------------------------------

# control_col1, control_col2 = st.columns([5, 1])

# with control_col1:
#     st.info(
#         "Enter a question below. The same question will be "
#         "sent to both models simultaneously."
#     )

# with control_col2:
#     if st.button("🗑️ Clear chat", use_container_width=True):

#         for key in [
#             "openai_history",
#             "anthropic_history",
#             "openai_conversation_id",
#             "anthropic_conversation_id",
#         ]:
#             if key in st.session_state:
#                 del st.session_state[key]

#         st.rerun()


# # --------------------------------------------------
# # Two-column model interface
# # --------------------------------------------------

# openai_col, anthropic_col = st.columns(2, gap="large")


# with openai_col:

#     st.subheader("🟢 GPT-5")

#     st.caption(
#         f"Azure AI Foundry deployment: "
#         f"{PROVIDERS['openai']['deployment']}"
#     )

#     display_history("openai")


# with anthropic_col:

#     st.subheader("🔵 Claude Sonnet 5.5")

#     st.caption(
#         f"Azure AI Foundry deployment: "
#         f"{PROVIDERS['anthropic']['deployment']}"
#     )

#     display_history("anthropic")


# # --------------------------------------------------
# # User input
# # --------------------------------------------------

# question = st.chat_input(
#     "Ask a question to compare both models..."
# )


# # --------------------------------------------------
# # Submit to both providers concurrently
# # --------------------------------------------------

# if question:

#     # Add user message to both conversation histories.

#     for provider_key in PROVIDERS:

#         history_key = f"{provider_key}_history"

#         st.session_state[history_key].append({
#             "role": "user",
#             "content": question,
#         })

#     openai_result = None
#     anthropic_result = None

#     openai_error = None
#     anthropic_error = None

#     with st.spinner(
#         "Waiting for GPT-5 and Claude responses..."
#     ):

#         with ThreadPoolExecutor(max_workers=2) as executor:

#             openai_future = executor.submit(
#                 send_chat_message,
#                 question,
#                 "openai",
#                 st.session_state["openai_conversation_id"],
#             )

#             anthropic_future = executor.submit(
#                 send_chat_message,
#                 question,
#                 "anthropic",
#                 st.session_state["anthropic_conversation_id"],
#             )

#             try:
#                 openai_result = openai_future.result()

#             except APIClientError as exc:
#                 openai_error = str(exc)

#             except Exception as exc:
#                 openai_error = f"Unexpected error: {exc}"

#             try:
#                 anthropic_result = anthropic_future.result()

#             except APIClientError as exc:
#                 anthropic_error = str(exc)

#             except Exception as exc:
#                 anthropic_error = f"Unexpected error: {exc}"


#     # Save GPT-5 result.

#     if openai_result is not None:

#         st.session_state["openai_conversation_id"] = (
#             openai_result.get("conversation_id")
#         )

#         st.session_state["openai_history"].append({
#             "role": "assistant",
#             "content": openai_result.get(
#                 "answer",
#                 "No answer returned.",
#             ),
#             "metadata": openai_result.get("metadata") or {},
#         })

#     else:

#         st.session_state["openai_history"].append({
#             "role": "assistant",
#             "content": openai_error or "Unknown error",
#             "error": True,
#         })


#     # Save Claude result.

#     if anthropic_result is not None:

#         st.session_state["anthropic_conversation_id"] = (
#             anthropic_result.get("conversation_id")
#         )

#         st.session_state["anthropic_history"].append({
#             "role": "assistant",
#             "content": anthropic_result.get(
#                 "answer",
#                 "No answer returned.",
#             ),
#             "metadata": anthropic_result.get("metadata") or {},
#         })

#     else:

#         st.session_state["anthropic_history"].append({
#             "role": "assistant",
#             "content": anthropic_error or "Unknown error",
#             "error": True,
#         })


#     # Refresh both columns with the latest responses.

#     st.rerun()
