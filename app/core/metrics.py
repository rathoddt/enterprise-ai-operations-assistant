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

# Initialize provider series so both are visible from application startup.
assistant_requests_by_provider_total.labels(provider="openai")
assistant_requests_by_provider_total.labels(provider="anthropic")

# Search routing decisions grouped by outcome and decision source.
search_routing_decisions_total = Counter(
    "search_routing_decisions_total",
    "Total search routing decisions",
    ["decision", "source"],
)



# Persistence retry attempts after an initial failure.
assistant_persistence_retries_total = Counter(
    "assistant_persistence_retries_total",
    "Total assistant request persistence retry attempts",
)

# Persistence operations that exhausted all configured attempts.
assistant_persistence_retry_exhausted_total = Counter(
    "assistant_persistence_retry_exhausted_total",
    "Total assistant request persistence operations that exhausted retries",
)

# Failed heartbeat updates.
assistant_heartbeat_failures_total = Counter(
    "assistant_heartbeat_failures_total",
    "Total assistant request heartbeat failures",
)

# Individual stale assistant requests successfully recovered.
assistant_stale_requests_recovered_total = Counter(
    "assistant_stale_requests_recovered_total",
    "Total stale assistant requests recovered",
)
