# Enterprise AI Operations Assistant
## Original 21-Day Implementation Roadmap

**Project duration:** 21 days  
**Daily preparation:** Approximately 3 hours  
**Primary LLM platform:** Azure AI Foundry  
**Models:** GPT-5 and Claude Sonnet 5.5  
**Backend:** Python, FastAPI  
**Database:** PostgreSQL  
**Deployment target:** Azure Container Apps (ACA)

## Phase 1 — Backend and LLM Foundation

### Day 1 — Project Foundation and FastAPI
- Create project structure and Python virtual environment.
- Initialize GitHub repository.
- Set up FastAPI application.
- Implement health-check and assistant chat endpoints.
- Define Pydantic request and response schemas.
- Configure initial automated tests.

### Day 2 — Python Engineering and Application Architecture
- Object-oriented programming and modular design.
- Pydantic validation.
- Asynchronous programming with AsyncIO.
- Dependency injection.
- Custom exception handling.
- Retry mechanisms and request timeouts.
- Unit testing with mocks.

### Day 3 — Azure AI Foundry and LLM Integration
- Integrate Azure AI Foundry models.
- Configure Azure OpenAI provider.
- Integrate GPT-5 and Claude Sonnet 5.5.
- Implement LLM provider abstraction and registry.
- Standardize structured responses and metadata.
- Capture provider, model, latency and token usage.
- Implement structured logging.

## Phase 2 — Retrieval-Augmented Generation (RAG)

### Day 4 — Document Ingestion, Chunking and Embeddings

**Objective:** Build the document ingestion and preprocessing pipeline.

Tasks:
- Understand the RAG architecture and document processing lifecycle.
- Implement document upload functionality.
- Support PDF, DOCX and TXT documents.
- Extract text from uploaded documents.
- Implement text preprocessing and cleaning.
- Implement document chunking.
- Configure chunk size and overlap.
- Generate embeddings using Azure OpenAI embedding models.
- Maintain document metadata and chunk identifiers.

**Expected deliverable:** A working document ingestion and embedding generation pipeline.

### Day 5 — Vector Database and Semantic Retrieval

**Objective:** Store embeddings and retrieve relevant document chunks.

Tasks:
- Understand vector databases and similarity search.
- Set up FAISS vector index.
- Store document embeddings.
- Associate embeddings with document metadata.
- Implement semantic similarity search.
- Retrieve top-K relevant chunks.
- Experiment with similarity thresholds.
- Validate retrieval quality using sample questions.

**Expected deliverable:** A working vector retrieval component.

### Day 6 — Complete RAG Pipeline and QA Endpoint

**Objective:** Connect retrieval with LLM generation.

Tasks:
- Implement the RAG orchestration pipeline.
- Accept user questions through FastAPI.
- Retrieve relevant document chunks.
- Construct context-aware prompts.
- Send retrieved context to the LLM.
- Generate grounded answers.
- Include document citations and source references.
- Handle questions without sufficient supporting context.
- Test the end-to-end RAG workflow.

**Expected deliverable:** A working RAG-based question-answering API.

### Day 7 — RAG Testing and Documentation

**Objective:** Validate and stabilize the RAG implementation.

Tasks:
- Test PDF, DOCX and TXT ingestion.
- Test chunking and embedding generation.
- Test semantic retrieval.
- Validate answer grounding.
- Validate source citations.
- Test irrelevant and unsupported questions.
- Handle document-processing errors.
- Add automated RAG tests.
- Document the RAG architecture and APIs.

**Expected deliverable:** Tested and documented RAG subsystem.

## Phase 3 — Agentic AI and Workflow Orchestration

### Day 8 — Introduction to LangGraph

- Understand agentic AI architecture.
- Understand LangGraph state, nodes and edges.
- Implement the initial graph.
- Define shared agent state.
- Implement graph execution.
- Integrate the assistant with LangGraph.

**Expected deliverable:** Initial LangGraph-based assistant workflow.

### Day 9 — Intelligent Routing and Agent Selection

- Implement request classification.
- Identify user intent.
- Design conditional routing.
- Route requests to appropriate agents.
- Support RAG, database and API-oriented requests.
- Implement fallback handling.

**Expected deliverable:** Intelligent request-routing workflow.

### Day 10 — RAG and Database Agent Integration

- Convert RAG functionality into an agent node.
- Introduce database query agent.
- Integrate PostgreSQL retrieval.
- Implement routing between RAG and database agents.
- Combine agent responses where appropriate.

**Expected deliverable:** Integrated RAG and database agents.

### Day 11 — REST API Tool Integration

- Understand agent tool calling.
- Define REST API tools.
- Implement API request and response handling.
- Integrate external REST services.
- Implement authentication and error handling.
- Validate tool selection and execution.

**Expected deliverable:** Assistant capable of interacting with REST APIs.

### Day 12 — Human-in-the-Loop Approval

- Identify operations requiring approval.
- Implement approval workflow.
- Introduce human approval checkpoints.
- Pause execution pending approval.
- Resume execution after approval.
- Handle rejection and timeout scenarios.

**Expected deliverable:** Controlled business-operation execution with human approval.

### Day 13 — Conversation Memory and Persistence

- Implement conversation memory.
- Understand LangGraph checkpoints.
- Maintain conversation state.
- Persist conversation context.
- Support multi-turn interactions.
- Restore previous conversation state.

**Expected deliverable:** Stateful assistant with persistent conversation context.

### Day 14 — Agent Integration and Failure Handling

- Integrate RAG, database and API agents.
- Connect all agents through LangGraph.
- Implement end-to-end workflow execution.
- Handle agent failures.
- Introduce retries and fallback paths.
- Validate human approval integration.
- Test multi-agent interactions.

**Expected deliverable:** Integrated agentic AI operations assistant.

## Phase 4 — Observability and Evaluation

### Day 15 — Langfuse Observability

- Integrate Langfuse.
- Trace LLM calls.
- Trace agent execution.
- Capture latency and token usage.
- Monitor tool execution.
- Analyze errors and execution traces.

**Expected deliverable:** Observable LLM and agent workflows.

### Day 16 — RAG Evaluation with Ragas

- Understand RAG evaluation methodology.
- Implement Ragas evaluation.
- Evaluate context precision.
- Evaluate context recall.
- Evaluate faithfulness.
- Evaluate answer relevance.
- Create a sample evaluation dataset.

**Expected deliverable:** Automated RAG evaluation workflow.

### Day 17 — Agent and LLM Evaluation with DeepEval

- Understand LLM evaluation methodologies.
- Integrate DeepEval.
- Create evaluation test cases.
- Evaluate answer correctness.
- Evaluate relevance and hallucination.
- Validate agent behaviour.
- Compare evaluation results across models.

**Expected deliverable:** Repeatable LLM and agent evaluation framework.

## Phase 5 — Security and Production Deployment

### Day 18 — Security and Governance

- Implement authentication and authorization.
- Secure API endpoints.
- Configure secrets management.
- Apply role-based access control.
- Validate user input.
- Consider prompt injection risks.
- Implement sensitive-data handling.
- Secure agent tool execution.

**Expected deliverable:** Security controls for enterprise AI operations.

### Day 19 — Docker, CI/CD and Deployment

- Containerize the FastAPI application.
- Create Docker configuration.
- Configure environment variables.
- Implement CI/CD pipeline.
- Integrate GitHub source control.
- Deploy to Azure Container Apps.
- Configure application health checks.
- Validate deployed application.

**Expected deliverable:** Containerized and deployed application.

## Phase 6 — Optimization and Interview Preparation

### Day 20 — Performance, Cost and Architecture Review

- Analyze API latency.
- Review LLM token consumption.
- Optimize retrieval performance.
- Review vector search efficiency.
- Evaluate caching opportunities.
- Analyze infrastructure costs.
- Review scalability and reliability.
- Document architecture trade-offs.

**Expected deliverable:** Optimized architecture with performance and cost considerations.

### Day 21 — Final Demonstration

- Perform complete end-to-end demonstration.
- Explain the overall architecture.
- Explain RAG implementation.
- Explain agent orchestration.
- Explain LangGraph workflows.
- Explain human approval mechanisms.
- Explain observability and evaluation.
- Discuss production deployment.
- Prepare system-design interview questions.
- Conduct a mock technical interview.

**Expected deliverable:** Portfolio-ready Enterprise AI Operations Assistant and interview walkthrough.

---

# Original Technology and Architecture Scope

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Programming language | Python |
| LLM platform | Azure AI Foundry |
| LLM models | GPT-5, Claude Sonnet 5.5 |
| Embeddings | Azure OpenAI embeddings |
| Document processing | PDF, DOCX, TXT extraction |
| Vector database | FAISS |
| RAG orchestration | Python / LangGraph |
| Agent framework | LangGraph |
| Relational database | PostgreSQL |
| API integration | REST APIs |
| Agent observability | Langfuse |
| RAG evaluation | Ragas |
| LLM evaluation | DeepEval |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Frontend | Streamlit |
| Containerization | Docker |
| Deployment | Azure Container Apps |
| Source control | GitHub |

# Current Progress Against Original Plan

| Day | Original objective | Current status |
|---|---|---|
| Day 1 | FastAPI foundation | <badge color="success">Completed</badge> |
| Day 2 | Python engineering and architecture | <badge color="success">Completed</badge> |
| Day 3 | LLM integration | <badge color="success">Completed</badge> |
| Day 4 | Document ingestion, chunking and embeddings | <badge color="warning">Next</badge> |
| Day 5 | FAISS and semantic retrieval | Pending |
| Day 6 | Complete RAG pipeline | Pending |
| Day 7 | RAG testing and documentation | Pending |
| Day 8–14 | LangGraph and agentic workflows | Pending |
| Day 15–17 | Observability and evaluation | Partially implemented / pending planned evaluation |
| Day 18–21 | Security, deployment, optimization | Pending |

*Note: Some later-phase foundations, such as Langfuse, Prometheus, Grafana and PostgreSQL, have already been implemented ahead of their original scheduled days. They do not change the original roadmap.*

