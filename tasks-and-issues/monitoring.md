# Enterprise AI Operations Assistant — Prometheus Metrics Reconciliation Issue

**Status:** Deferred for later investigation  
**Date:** 14 November 2026  
**Priority:** Medium  
**Current objective:** Resume Day 4 implementation without spending more time on this issue.

## 1. Issue summary

The Grafana dashboard shows inconsistent values between:
- Total Assistant Requests
- Requests Triggering Web Search
- Router Decided to Search
- Router Decided Not to Search
- Successful Tavily Executions
- Failed Tavily Executions

The expected relationship is:

1. Total Assistant Requests = Total Routing Decisions.
2. Requests Triggering Web Search = Router Decided to Search.
3. Tavily execution counts should reconcile with actual search execution attempts, accounting for failures and retries.

## 2. Application architecture

- FastAPI application.
- Prometheus Python client for metrics.
- Prometheus running on port `9092`.
- Grafana running on port `3001`.
- FastAPI metrics endpoint: `http://127.0.0.1:8000/metrics`.
- Streamlit frontend sends requests to `http://127.0.0.1:8000`.
- Uvicorn currently started using:

```powershell
uvicorn app.main:app --reload
```

## 3. Relevant metric definitions

File: `app/core/metrics.py`

```python
assistant_requests_total
assistant_requests_with_web_search_total
web_search_executions_total
assistant_requests_by_provider_total
search_routing_decisions_total
assistant_persistence_retries_total
assistant_persistence_retry_exhausted_total
assistant_heartbeat_failures_total
assistant_stale_requests_recovered_total
```

Routing metric:

```python
search_routing_decisions_total = Counter(
    "search_routing_decisions_total",
    "Total search routing decisions",
    ["decision", "source"],
)
```

## 4. Relevant implementation

### `app/main.py`

The metrics endpoint uses:

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

It reads from the default Prometheus registry.

### `app/services/assistant.py`

At the beginning of request processing:

```python
assistant_requests_total.inc()

assistant_requests_by_provider_total.labels(
    provider=request.provider
).inc()
```

When a request triggers web search:

```python
if not web_search_used:
    assistant_requests_with_web_search_total.inc()
    web_search_used = True
```

### `app/web_search/router.py`

Routing decisions are recorded through:

```python
def _record_decision(self, decision: SearchDecision) -> None:
    outcome = "search" if decision.requires_search else "no_search"

    search_routing_decisions_total.labels(
        decision=outcome,
        source=decision.decision_source,
    ).inc()
```

The method is called for both successful classifier/rules decisions and fallback decisions.

## 5. Controlled test performed

Two requests were submitted through Streamlit using Claude Sonnet 5.5.

**Request 1:**

```text
What is the latest weather forecast for Pune today?
```

Expected routing: Search.

**Request 2:**

```text
What is the difference between Python lists and tuples?
```

Expected routing: No search.

### FastAPI logs

First request:

```text
Search routing completed | source=rules requires_search=True confidence=1.00
Search decision metric recorded | decision=search source=rules confidence=1.00
Tavily search completed | query_length=51 results=5
LLM request completed | provider=anthropic
```

Second request:

```text
Rule-based search routing uncertain | confidence=0.70 threshold=0.80
Search routing completed | source=llm requires_search=False confidence=0.99
Search decision metric recorded | decision=no_search source=llm confidence=0.99
LLM request completed | provider=anthropic
```

**Conclusion:** Both requests completed successfully, and the application logs confirm that both routing decisions were recorded.

## 6. Prometheus diagnostic results

A 5-minute PromQL diagnostic was run after the two requests.

| Metric | Expected | Observed |
|---|---:|---:|
| Assistant requests | 2 | 2 |
| Requests triggering web search | 1 | 1 |
| Total routing decisions | 2 | 1 |
| Router decided to search | 1 | 1 |
| Router decided not to search | 1 | 0 |
| Successful Tavily executions | 1 | 1 |
| Failed Tavily executions | 0 | No data |

This showed a discrepancy between application logs and Prometheus query results.

## 7. Additional investigation

### A. Process configuration

Uvicorn was running with `--reload`.

Process tree included:

- Uvicorn parent process.
- Python reloader process.
- Python application worker.
- An additional multiprocessing child.

Streamlit was running separately.

### B. API URL

File: `frontend/api_client.py`

```python
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)
```

Port 8000 was owned by the expected Uvicorn application process.

### C. Metric imports

The inspected modules consistently use canonical imports:

```python
from app.core.metrics import ...
```

Files:
- `app/main.py`
- `app/services/assistant.py`
- `app/services/web_search.py`
- `app/web_search/router.py`

### D. Prometheus registry

The inspected code uses the default registry.

No custom `CollectorRegistry` was identified.

The `/metrics` endpoint returns HTTP 200 and valid Prometheus metrics.

### E. Multiprocess configuration

The following environment variable was checked:

```powershell
$env:PROMETHEUS_MULTIPROC_DIR
```

It was empty.

No Prometheus multiprocess environment variables were found.

## 8. Important diagnostic observation

A separate Python diagnostic was run using:

```python
from prometheus_client import REGISTRY, generate_latest
```

It showed zero values.

However, this was a separate Python process, so its in-memory counters were independent of the Uvicorn process. This result should not be used to infer the live application's counter state.

The live API endpoint was separately checked and returned:

```text
assistant_requests_total 0.0
assistant_requests_with_web_search_total 0.0
```

Despite the successful requests and corresponding application logs.

This is the key unresolved inconsistency.

## 9. Proposed next action when resuming

The next planned diagnostic is to stop Uvicorn and start it without automatic reload:

```powershell
# Stop existing Uvicorn using Ctrl+C

uvicorn app.main:app
```

Then:

1. Submit the weather query through Streamlit.
2. Submit the Python lists-versus-tuples query through Streamlit.
3. Inspect `http://127.0.0.1:8000/metrics`.
4. Verify whether the expected counter values are now exposed.

Expected values in a fresh application process:

```text
assistant_requests_total 2.0
assistant_requests_with_web_search_total 1.0
search_routing_decisions_total{decision="search",source="rules"} 1.0
search_routing_decisions_total{decision="no_search",source="llm"} 1.0
web_search_executions_total{provider="tavily",status="success"} 1.0
```

**Important:** Running without `--reload` is a proposed diagnostic, not a confirmed solution.

If the issue persists, investigate metric object identity and runtime process behavior rather than repeatedly changing Grafana queries.

## 10. Files involved

| File | Purpose |
|---|---|
| `app/core/metrics.py` | Prometheus metric definitions |
| `app/main.py` | FastAPI `/metrics` endpoint |
| `app/services/assistant.py` | Assistant request and web-search counters |
| `app/web_search/router.py` | Search-routing decision counter |
| `app/services/web_search.py` | Tavily execution counter |
| `frontend/api_client.py` | Streamlit-to-FastAPI URL configuration |

## 11. Current decision

- Do not reset Prometheus.
- Do not reset Grafana.
- Do not modify metric definitions without evidence.
- Do not spend more time on this issue before Day 4.
- Resume the Prometheus reconciliation investigation later using Section 9.

**Next project milestone: Continue Day 4 of Enterprise AI Operations Assistant.**