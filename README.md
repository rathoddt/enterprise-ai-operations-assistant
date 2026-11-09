# Enterprise AI Operations Assistant

An enterprise-oriented AI assistant built to demonstrate production-minded AI application engineering, multi-model orchestration, observability, and responsible AI operations.

The project integrates **GPT-5 and Claude Sonnet 5.5 through Microsoft Azure AI Foundry**, exposes a FastAPI backend, and provides a Streamlit interface for interacting with and comparing model responses.

The development approach emphasizes modular architecture, provider abstraction, reliability, configurable token limits, response metadata, testing, and observability.

## 1. Project Objectives

Build an extensible AI operations assistant that demonstrates:

- Multi-provider LLM integration.
- Centralized model-provider abstraction and orchestration.
- Configurable system prompts and output token limits.
- Side-by-side model response comparison.
- Request and response metadata tracking.
- Error handling and resilience.
- Automated testing.
- LLM observability using Langfuse.
- Foundation for enterprise RAG, AI agents, tools, and human-in-the-loop workflows.

## 2. Development Progress

| Development phase | Scope | Status |
|---|---|---|
| Day 1 | FastAPI project foundation, configuration, schemas, health and chat APIs | Completed |
| Day 2 | Provider abstraction, dependency injection, exception handling, resilience and tests | Completed |
| Day 3 | Azure AI Foundry integration with GPT-5 and Claude Sonnet 5.5 | Completed |
| Day 3.5 | Streamlit UI and side-by-side model comparison | Completed |
| Day 3 improvements | Response truncation detection, token metadata and configurable output limits | Implemented; verification ongoing |
| Langfuse setup | Local Langfuse OSS deployment and project API key configuration | Completed |
| Langfuse integration | Application-level trace and generation instrumentation | Next step |

## 3. Architecture

```text
                  User
                   |
                   v
             Streamlit UI
                   |
                   v
              FastAPI API
                   |
                   v
             AssistantService
                   |
             Provider Registry
                   |
           +-------+-------+
           |               |
           v               v
      GPT-5 Provider   Claude Provider
           |               |
           v               v
       Azure AI Foundry / Model Deployments
           |               |
           +-------+-------+
                   |
                   v
             Model Response
                   |
                   v
          Response Metadata
                   |
                   v
             Streamlit UI


       Planned Observability Integration
                   |
                   v
                Langfuse
                   |
          +--------+--------+
          |        |        |
        Traces  Latency   Token Usage
```

The architecture separates API handling, assistant orchestration, model-provider implementations, and user-interface responsibilities.

## 4. Technology Stack

| Category | Technology |
|---|---|
| Programming language | Python 3.12 |
| Backend framework | FastAPI |
| Data validation | Pydantic |
| Configuration | Pydantic Settings, python-dotenv |
| LLM hosting | Microsoft Azure AI Foundry |
| LLM providers | GPT-5, Claude Sonnet 5.5 |
| OpenAI integration | OpenAI Python SDK |
| Anthropic integration | Anthropic Python SDK |
| Frontend | Streamlit |
| API server | Uvicorn |
| Testing | Pytest |
| Resilience | Retry and timeout utilities |
| Observability platform | Langfuse OSS |
| Local infrastructure | Docker Desktop, Docker Compose |
| Source control | Git, GitHub |

## 5. Features Implemented

### 5.1 FastAPI backend foundation

- Application configuration and environment-based settings.
- Versioned API routing.
- Health-check endpoint.
- Assistant chat endpoint.
- Pydantic request and response schemas.
- Centralized logging.
- Application-level exception handling.
- Dependency injection for assistant services and provider registry.

### 5.2 Multi-provider LLM integration

Integrated two models through Azure AI Foundry.

**GPT-5**
- Uses the OpenAI Python SDK.
- Connects through the Azure AI Foundry OpenAI-compatible endpoint.
- Supports system instructions and user input.
- Captures response and usage metadata.

**Claude Sonnet 5.5**
- Uses the Anthropic Python SDK.
- Connects through the Azure AI Foundry Anthropic endpoint.
- Supports system prompts and user messages.
- Captures response and usage metadata.

Both providers implement a common provider interface, allowing the assistant service to work independently of provider-specific SDK implementations.

### 5.3 Provider abstraction and orchestration

Implemented:

- Common LLM provider protocol.
- Provider registry.
- Centralized assistant service.
- Provider selection based on the incoming request.
- Consistent response structure across providers.

This makes it possible to introduce additional model providers without redesigning the API layer.

### 5.4 Streamlit user interface

Implemented a Streamlit interface with:

- Shared system prompt configuration.
- User prompt input.
- Compare Both mode.
- GPT Only mode.
- Claude Only mode.
- Side-by-side model responses.
- Separate response histories.
- Response metadata display.

The interface supports interactive comparison of GPT-5 and Claude Sonnet 5.5 using the same user prompt.

### 5.5 Response metadata and token management

Implemented response metadata collection, including:

- Provider name.
- Model/deployment name.
- Request latency.
- Input token count.
- Output token count.
- Provider request ID.
- Response ID.
- Completion status.
- Finish reason.
- Truncation indicator.
- Incomplete response reason.

Output token limits are centrally configurable through application settings.

Current default:

```env
LLM_MAX_OUTPUT_TOKENS=1500
```

Response truncation detection is implemented for both providers to help identify incomplete model responses.

### 5.6 Reliability and error handling

Implemented foundational reliability capabilities:

- Centralized application exception handling.
- Provider-level error handling.
- Retry and timeout utilities.
- Structured application logging.
- Consistent error responses.
- Request latency measurement.

### 5.7 Automated testing

Pytest is used for backend validation.

Test coverage currently includes:

- Health endpoint.
- Assistant service behavior.
- Provider interaction.
- Resilience and retry behavior.

The initial backend test suite completed successfully with 8 passing tests. Tests should be rerun after subsequent changes.

### 5.8 Langfuse local deployment

A local Langfuse OSS environment has been deployed using Docker Compose.

**Local Langfuse repository:**

```text
C:\all-gits\my-gits\langfuse-local
```

**Langfuse dashboard:**

```text
http://localhost:3000
```

The local deployment includes:

- Langfuse Web.
- Langfuse Worker.
- PostgreSQL.
- ClickHouse.
- Redis.
- MinIO.
- Langfuse AI Gateway.

The Langfuse web application started successfully, database migrations completed, and the project was created.

A dedicated Langfuse project has been created:

```text
enterprise-ai-operations-assistant
```

Application environment variables have been configured:

```env
LANGFUSE_SECRET_KEY=<your-secret-key>
LANGFUSE_PUBLIC_KEY=<your-public-key>
LANGFUSE_BASE_URL=http://localhost:3000
```

**Current integration status:** Local Langfuse infrastructure and API credentials are ready. Python application instrumentation, trace creation, and generation-level observations are pending.

Planned observability capabilities:

- Request-level traces.
- Model-generation observations.
- Provider and model identification.
- Input and output token usage.
- Model latency.
- Error tracking.
- Model comparison and performance analysis.

## 6. Project Structure and Component Responsibilities

The application follows a modular structure, separating API endpoints, business orchestration, model integrations, configuration, and tests.

### Component responsibility mapping

| Responsibility | Existing file |
|---|---|
| FastAPI application | `app/main.py` |
| Configuration and environment | `app/core/config.py` |
| API dependencies | `app/api/dependencies.py` |
| Chat endpoint | `app/api/routes/assistant.py` |
| Assistant orchestration | `app/services/assistant.py` |
| Provider interface | `app/llm/provider.py` |
| Provider registry | `app/llm/registry.py` |
| GPT-5 integration | `app/llm/openai_provider.py` |
| Claude integration | `app/llm/anthropic_provider.py` |
| Response schemas | `app/llm/schemas.py` |
| Tests | `tests/` |

### Repository directory structure

```text
enterprise-ai-operations-assistant/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── assistant.py
│   │   │   └── health.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── resilience.py
│   │
│   ├── llm/
│   │   ├── anthropic_provider.py
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── provider.py
│   │   ├── registry.py
│   │   └── schemas.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   └── assistant.py
│   │
│   └── main.py
│
├── frontend/
│   ├── api_client.py
│   └── streamlit_app.py
│
├── tests/
│   ├── test_assistant_service.py
│   ├── test_health.py
│   └── test_resilience.py
│
├── scripts/
├── figs/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 7. Local Development Setup

### Prerequisites

- Python 3.12
- Git
- Docker Desktop
- Microsoft Azure AI Foundry resource with configured model deployments
- Langfuse local deployment

### Clone the repository

```powershell
git clone <your-repository-url>
cd enterprise-ai-operations-assistant
```

### Create and activate virtual environment

```powershell
python -m venv .venv

.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the project root.

```env
APP_NAME=Enterprise AI Operations Assistant
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_PREFIX=/api/v1
LOG_LEVEL=INFO

LLM_MAX_INPUT_TOKENS=10000
LLM_MAX_OUTPUT_TOKENS=1500

# GPT-5 - Microsoft Azure AI Foundry
FOUNDRY_OPENAI_ENDPOINT=<your-openai-endpoint>
FOUNDRY_OPENAI_API_KEY=<your-foundry-key>
FOUNDRY_OPENAI_DEPLOYMENT=gpt-5

# Claude Sonnet 5.5 - Microsoft Azure AI Foundry
FOUNDRY_ANTHROPIC_ENDPOINT=<your-anthropic-endpoint>
FOUNDRY_ANTHROPIC_API_KEY=<your-foundry-key>
FOUNDRY_ANTHROPIC_DEPLOYMENT=claude-sonnet-5-5

# Langfuse
LANGFUSE_SECRET_KEY=<your-langfuse-secret-key>
LANGFUSE_PUBLIC_KEY=<your-langfuse-public-key>
LANGFUSE_BASE_URL=http://localhost:3000
```

Do not commit `.env` or expose API keys in source control.

### Start the FastAPI backend

```powershell
uvicorn app.main:app --reload
```

API base URL:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### Start the Streamlit frontend

Open another terminal, activate the virtual environment, and run:

```powershell
streamlit run frontend/streamlit_app.py
```

### Run automated tests

```powershell
pytest -v
```

## 8. Langfuse Local Infrastructure

Langfuse is deployed separately from the application.

Navigate to the Langfuse repository:

```powershell
cd C:\all-gits\my-gits\langfuse-local
```

Start services:

```powershell
docker compose up -d
```

Check container status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs --tail=50 langfuse-web

docker compose logs --tail=50 langfuse-worker

docker compose logs --tail=50 redis
```

Open the dashboard:

```text
http://localhost:3000
```


## 09. Engineering Principles

1. **Provider independence:** Model-specific SDK logic remains isolated behind a common provider interface.
2. **Separation of concerns:** API, orchestration, provider, configuration, and frontend responsibilities remain modular.
3. **Reliability:** Timeouts, retries, exception handling, and structured logging are incorporated into the foundation.
4. **Observability:** Model calls should be traceable, measurable, and diagnosable.
5. **Security:** Credentials are managed through environment variables rather than hardcoded values.
6. **Responsible AI operations:** Sensitive business operations require application-level authorization and appropriate approval controls; an LLM response alone does not authorize an action.
7. **Testability:** Services and providers should remain independently testable.

## 10. Current Milestone and Next Steps

**Completed:**

- FastAPI foundation.
- Dual-model Azure AI Foundry integration.
- Streamlit comparison interface.
- Response metadata and token management.
- Initial automated tests.
- Local Langfuse infrastructure and project setup.

**Next immediate milestone:**

Integrate Langfuse tracing into the FastAPI assistant service and verify that real GPT-5 and Claude requests appear in the Langfuse dashboard.

The objective is to evolve this foundation into a production-minded enterprise AI assistant with RAG, agent orchestration, controlled tools, evaluation, and end-to-end observability.