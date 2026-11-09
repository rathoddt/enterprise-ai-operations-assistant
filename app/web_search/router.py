import logging
import re

from app.llm.provider import LLMProvider
from app.web_search.classifier import LLMSearchClassifier
from app.web_search.routing import SearchDecision

from contextlib import nullcontext

from app.core.observability import get_langfuse_client

logger = logging.getLogger(__name__)


class SearchRouter:

    CONFIDENCE_THRESHOLD = 0.80

    LIVE_KEYWORDS = [
        "today",
        "right now",
        "currently",
        "current",
        "latest",
        "as of now",
        "real-time",
        "realtime",
        "weather",
        "stock price",
        "share price",
        "exchange rate",
        "live score",
    ]

    RECENT_KEYWORDS = [
        "recent",
        "recently",
        "this week",
        "this month",
        "this year",
        "new release",
        "released",
        "announced",
        "what changed",
        "updates",
        "news",
    ]

    PRICING_KEYWORDS = [
        "pricing",
        "price",
        "cost",
        "subscription",
        "plan cost",
    ]

    WEATHER_KEYWORDS = [
        "weather",
        "temperature",
        "rain",
        "forecast",
    ]

    NEWS_KEYWORDS = [
        "news",
        "announced",
        "announcement",
        "released",
        "release",
        "this week",
    ]

    # def __init__(
    #     self,
    #     classifier: LLMSearchClassifier | None = None,
    # ):
    #     self.classifier = classifier or LLMSearchClassifier()
    def __init__(
        self,
        classifier: LLMSearchClassifier | None = None,
    ):
        self.classifier = classifier or LLMSearchClassifier()
        self.langfuse = get_langfuse_client()
        

    def _contains_keyword(
        self,
        query: str,
        keywords: list[str],
    ) -> bool:

        normalized_query = query.lower()

        return any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized_query,
            )
            for keyword in keywords
        )

    def route_rules(self, query: str) -> SearchDecision:

        if self._contains_keyword(query, self.WEATHER_KEYWORDS):
            return SearchDecision(
                requires_search=True,
                reason="Weather information requires current data.",
                search_query=query,
                search_type="weather",
                freshness="live",
                confidence=1.0,
                decision_source="rules",
            )

        if self._contains_keyword(query, self.PRICING_KEYWORDS):
            return SearchDecision(
                requires_search=True,
                reason="Pricing information can change over time.",
                search_query=query,
                search_type="pricing",
                freshness="recent",
                confidence=0.95,
                decision_source="rules",
            )

        if self._contains_keyword(query, self.LIVE_KEYWORDS):
            return SearchDecision(
                requires_search=True,
                reason="The query requests current or live information.",
                search_query=query,
                search_type="general",
                freshness="live",
                confidence=0.95,
                decision_source="rules",
            )

        if self._contains_keyword(query, self.RECENT_KEYWORDS):
            return SearchDecision(
                requires_search=True,
                reason="The query requests recent information or updates.",
                search_query=query,
                search_type=(
                    "news"
                    if self._contains_keyword(
                        query,
                        self.NEWS_KEYWORDS,
                    )
                    else "general"
                ),
                freshness="recent",
                confidence=0.95,
                decision_source="rules",
            )

        return SearchDecision(
            requires_search=False,
            reason="No explicit freshness requirement detected.",
            search_query=None,
            search_type="general",
            freshness="none",
            confidence=0.70,
            decision_source="rules",
        )

    async def route(
        self,
        query: str,
        provider: LLMProvider,
    ) -> SearchDecision:

        routing_context = (
            self.langfuse.start_as_current_observation(
                as_type="span",
                name="search-routing",
                metadata={
                    "routing_strategy": "hybrid",
                    "confidence_threshold": self.CONFIDENCE_THRESHOLD,
                },
            )
            if self.langfuse
            else nullcontext(None)
        )

        with routing_context as routing_span:

            try:
                rule_decision = self.route_rules(query)

                if rule_decision.confidence >= self.CONFIDENCE_THRESHOLD:

                    decision = rule_decision

                    logger.info(
                        "Search routing completed | source=rules "
                        "requires_search=%s confidence=%.2f",
                        decision.requires_search,
                        decision.confidence,
                    )

                else:

                    logger.info(
                        "Rule-based search routing uncertain | "
                        "confidence=%.2f threshold=%.2f. "
                        "Invoking LLM classifier.",
                        rule_decision.confidence,
                        self.CONFIDENCE_THRESHOLD,
                    )

                    decision = await self.classifier.classify(
                        query=query,
                        provider=provider,
                    )

                    logger.info(
                        "Search routing completed | source=llm "
                        "requires_search=%s confidence=%.2f",
                        decision.requires_search,
                        decision.confidence,
                    )

                if routing_span:
                    routing_span.update(
                        output={
                            "requires_search": decision.requires_search,
                            "search_type": decision.search_type,
                            "freshness": decision.freshness,
                            "confidence": decision.confidence,
                            "decision_source": decision.decision_source,
                        },
                        metadata={
                            "routing_status": "success",
                            "decision_source": decision.decision_source,
                            "requires_search": decision.requires_search,
                        },
                    )

                return decision

            except Exception as exc:

                if routing_span:
                    routing_span.update(
                        level="ERROR",
                        status_message="Search routing failed",
                        output={"status": "error"},
                    )

                logger.exception(
                    "Search routing failed. Falling back to rule-based decision."
                )

                return self.route_rules(query)
        
    # async def route(
    #     self,
    #     query: str,
    #     provider: LLMProvider,
    # ) -> SearchDecision:

    #     rule_decision = self.route_rules(query)

    #     if rule_decision.confidence >= self.CONFIDENCE_THRESHOLD:

    #         logger.info(
    #             "Search routing completed | source=rules "
    #             "requires_search=%s confidence=%.2f",
    #             rule_decision.requires_search,
    #             rule_decision.confidence,
    #         )

    #         return rule_decision

    #     logger.info(
    #         "Rule-based search routing uncertain | "
    #         "confidence=%.2f threshold=%.2f. "
    #         "Invoking LLM classifier.",
    #         rule_decision.confidence,
    #         self.CONFIDENCE_THRESHOLD,
    #     )

    #     try:
    #         decision = await self.classifier.classify(
    #             query=query,
    #             provider=provider,
    #         )

    #         logger.info(
    #             "Search routing completed | source=llm "
    #             "requires_search=%s confidence=%.2f",
    #             decision.requires_search,
    #             decision.confidence,
    #         )

    #         return decision

    #     except Exception:
    #         logger.exception(
    #             "LLM search classification failed. "
    #             "Falling back to rule-based decision."
    #         )

    #         return rule_decision
        
# import re

# from app.web_search.routing import SearchDecision


# class SearchRouter:

#     LIVE_KEYWORDS = [
#         "today",
#         "right now",
#         "currently",
#         "current",
#         "latest",
#         "as of now",
#         "real-time",
#         "realtime",
#         "weather",
#         "stock price",
#         "share price",
#         "exchange rate",
#         "live score",
#     ]

#     RECENT_KEYWORDS = [
#         "recent",
#         "recently",
#         "this week",
#         "this month",
#         "this year",
#         "new release",
#         "released",
#         "announced",
#         "what changed",
#         "updates",
#         "news",
#     ]

#     PRICING_KEYWORDS = [
#         "pricing",
#         "price",
#         "cost",
#         "subscription",
#         "plan cost",
#     ]

#     WEATHER_KEYWORDS = [
#         "weather",
#         "temperature",
#         "rain",
#         "forecast",
#     ]

#     NEWS_KEYWORDS = [
#         "news",
#         "announced",
#         "announcement",
#         "released",
#         "release",
#         "this week",
#     ]

#     def _contains_keyword(
#         self,
#         query: str,
#         keywords: list[str],
#     ) -> bool:
#         normalized_query = query.lower()

#         return any(
#             re.search(
#                 rf"\b{re.escape(keyword)}\b",
#                 normalized_query,
#             )
#             for keyword in keywords
#         )

#     def route(self, query: str) -> SearchDecision:

#         if self._contains_keyword(query, self.WEATHER_KEYWORDS):
#             return SearchDecision(
#                 requires_search=True,
#                 reason="Weather information requires current data.",
#                 search_query=query,
#                 search_type="weather",
#                 freshness="live",
#                 confidence=1.0,
#                 decision_source="rules",
#             )

#         if self._contains_keyword(query, self.PRICING_KEYWORDS):
#             return SearchDecision(
#                 requires_search=True,
#                 reason="Pricing information can change over time.",
#                 search_query=query,
#                 search_type="pricing",
#                 freshness="recent",
#                 confidence=0.95,
#                 decision_source="rules",
#             )

#         if self._contains_keyword(query, self.LIVE_KEYWORDS):
#             return SearchDecision(
#                 requires_search=True,
#                 reason="The query requests current or live information.",
#                 search_query=query,
#                 search_type="general",
#                 freshness="live",
#                 confidence=0.95,
#                 decision_source="rules",
#             )

#         if self._contains_keyword(query, self.RECENT_KEYWORDS):
#             return SearchDecision(
#                 requires_search=True,
#                 reason="The query requests recent information or updates.",
#                 search_query=query,
#                 search_type=(
#                     "news"
#                     if self._contains_keyword(query, self.NEWS_KEYWORDS)
#                     else "general"
#                 ),
#                 freshness="recent",
#                 confidence=0.95,
#                 decision_source="rules",
#             )

#         return SearchDecision(
#             requires_search=False,
#             reason="No explicit freshness requirement detected.",
#             search_query=None,
#             search_type="general",
#             freshness="none",
#             confidence=0.70,
#             decision_source="rules",
#         )