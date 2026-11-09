
import json
import logging
from contextlib import nullcontext

from app.core.observability import get_langfuse_client
from app.llm.provider import LLMProvider
from app.web_search.routing import SearchDecision

logger = logging.getLogger(__name__)
CLASSIFIER_MAX_OUTPUT_TOKENS = 1200

SYSTEM_PROMPT = """
You are an intent and information-freshness classifier.

Determine whether answering the user's query requires external,
up-to-date information rather than relying only on the LLM's
existing knowledge.

Search is required when:
- The answer depends on current or latest information.
- The user implicitly asks about a recent release, announcement,
  product, event, or change.
- The answer depends on live or frequently changing data.
- The information may have changed since the model's training data.

Search is generally not required for:
- Stable technical concepts.
- General explanations and tutorials.
- Established programming concepts.
- Mathematical reasoning and general knowledge.

Classify the search type:
- weather: weather, temperature, rainfall, forecast.
- pricing: current product, cloud service, subscription or service costs.
- news: recent announcements, releases, events and developments.
- general: other current-information research.

Return ONLY valid JSON with these fields:
{
  "requires_search": true,
  "reason": "Explanation",
  "search_query": "Optimized search query or null",
  "search_type": "general",
  "freshness": "recent",
  "confidence": 0.95,
  "decision_source": "llm"
}

Allowed freshness values: none, recent, live.
Allowed search types: general, news, weather, pricing.
"""


class LLMSearchClassifier:

    def __init__(self):
        self.langfuse = get_langfuse_client()

    async def classify(
        self,
        query: str,
        provider: LLMProvider,
    ) -> SearchDecision:

        generation_context = (
            self.langfuse.start_as_current_observation(
                as_type="generation",
                name="search-intent-classification",
                model=getattr(provider, "deployment", "unknown"),
                model_parameters={
                    # "max_output_tokens": 200,
                    # max_output_tokens=CLASSIFIER_MAX_OUTPUT_TOKENS,
                    "max_output_tokens": CLASSIFIER_MAX_OUTPUT_TOKENS,
                },
                metadata={
                    "task": "search_intent_classification",
                    "provider": provider.__class__.__name__,
                },
            )
            if self.langfuse
            else nullcontext(None)
        )

        with generation_context as generation:

            try:
                result = await provider.generate(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=query,
                    max_output_tokens=CLASSIFIER_MAX_OUTPUT_TOKENS,
                )
                if not result.answer or not result.answer.strip():
                    raise ValueError(
                        "Classifier returned an empty response. "
                        f"status={result.finish_reason}, "
                        f"truncated={result.is_truncated}, "
                        f"incomplete_reason={result.incomplete_reason}, "
                        f"output_tokens={result.output_tokens}"
                    )

                decision_data = json.loads(result.answer)

                decision_data["decision_source"] = "llm"

                decision = SearchDecision.model_validate(
                    decision_data
                )

                if not decision.requires_search:
                    decision.search_query = None

                if generation:
                    usage_details = {}

                    if result.input_tokens is not None:
                        usage_details["input"] = result.input_tokens

                    if result.output_tokens is not None:
                        usage_details["output"] = result.output_tokens

                    generation.update(
                        model=result.model,
                        output={
                            "requires_search": decision.requires_search,
                            "search_type": decision.search_type,
                            "freshness": decision.freshness,
                            "confidence": decision.confidence,
                        },
                        usage_details=usage_details or None,
                        metadata={
                            "decision_source": "llm",
                            "requires_search": decision.requires_search,
                            "confidence": decision.confidence,
                        },
                    )

                return decision

            except Exception as exc:

                if generation:
                    generation.update(
                        level="ERROR",
                        status_message=str(exc),
                    )

                logger.exception(
                    "LLM search classification failed."
                )

                raise ValueError(
                    "Unable to complete LLM search classification."
                ) from exc


# import json
# import logging

# from app.llm.provider import LLMProvider
# from app.web_search.routing import SearchDecision

# logger = logging.getLogger(__name__)

# SYSTEM_PROMPT = """
# You are an intent and information-freshness classifier.

# Determine whether answering the user's query requires external,
# up-to-date information rather than relying only on the LLM's
# existing knowledge.

# Search is required when:
# - The answer depends on current or latest information.
# - The user implicitly asks about a recent release, announcement,
#   product, event, or change.
# - The answer depends on live or frequently changing data.
# - The information may have changed since the model's training data.

# Search is generally not required for:
# - Stable technical concepts.
# - General explanations and tutorials.
# - Established programming concepts.
# - Mathematical reasoning and general knowledge.

# Classify the search type:
# - weather: weather, temperature, rainfall, forecast.
# - pricing: current product, cloud service, subscription or service costs.
# - news: recent announcements, releases, events and developments.
# - general: other current-information research.

# Return ONLY valid JSON with these fields:
# {
#   "requires_search": true,
#   "reason": "Explanation",
#   "search_query": "Optimized search query or null",
#   "search_type": "general",
#   "freshness": "recent",
#   "confidence": 0.95,
#   "decision_source": "llm"
# }

# Allowed freshness values: none, recent, live.
# Allowed search types: general, news, weather, pricing.
# """


# class LLMSearchClassifier:

#     async def classify(
#         self,
#         query: str,
#         provider: LLMProvider,
#     ) -> SearchDecision:

#         result = await provider.generate(
#             system_prompt=SYSTEM_PROMPT,
#             user_prompt=query,
#             max_output_tokens=200,
#         )

#         try:
#             decision_data = json.loads(result.answer)

#             decision_data["decision_source"] = "llm"

#             decision = SearchDecision.model_validate(
#                 decision_data
#             )

#             if not decision.requires_search:
#                 decision.search_query = None

#             return decision

#         except (json.JSONDecodeError, ValueError) as exc:
#             logger.warning(
#                 "LLM search classification failed: %s",
#                 exc,
#             )

#             raise ValueError(
#                 "Unable to interpret LLM search classification."
#             ) from exc