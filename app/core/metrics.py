from prometheus_client import Counter

# Total incoming assistant requests.
# Increment exactly once for each accepted user request.
assistant_requests_total = Counter(
    "assistant_requests_total",
    "Total number of incoming assistant requests",
)

# Unique assistant requests that actually trigger web search.
# Increment once per request, even if multiple searches are executed.
assistant_requests_with_web_search_total = Counter(
    "assistant_requests_with_web_search_total",
    "Total number of assistant requests that invoke web search",
)

# Actual web search executions.
# A single assistant request may trigger multiple executions.
web_search_executions_total = Counter(
    "web_search_executions_total",
    "Total number of web search execution attempts",
    ["provider", "status"],
)
# Accepted assistant requests grouped by selected final-answer provider.
assistant_requests_by_provider_total = Counter(
    "assistant_requests_by_provider_total",
    "Total assistant requests grouped by provider",
    ["provider"],
)