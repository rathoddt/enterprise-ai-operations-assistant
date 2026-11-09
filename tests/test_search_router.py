import asyncio

from app.web_search.router import SearchRouter
from app.web_search.routing import SearchDecision


class MockProvider:
    pass


class MockClassifier:

    def __init__(self):
        self.called = False

    async def classify(self, query, provider):
        self.called = True

        return SearchDecision(
            requires_search=True,
            reason="The query implies a recent product announcement.",
            search_query=query,
            search_type="news",
            freshness="recent",
            confidence=0.90,
            decision_source="llm",
        )


def test_router_uses_rules_for_high_confidence_query():

    async def run_test():
        classifier = MockClassifier()
        router = SearchRouter(classifier=classifier)

        decision = await router.route(
            "What is the latest Gemini model?",
            MockProvider(),
        )

        assert decision.requires_search is True
        assert decision.decision_source == "rules"
        assert classifier.called is False

    asyncio.run(run_test())


def test_router_uses_llm_for_ambiguous_query():

    async def run_test():
        classifier = MockClassifier()
        router = SearchRouter(classifier=classifier)

        decision = await router.route(
            "Can I use Gemini 3 with Vertex AI?",
            MockProvider(),
        )

        assert decision.requires_search is True
        assert decision.decision_source == "llm"
        assert classifier.called is True

    asyncio.run(run_test())