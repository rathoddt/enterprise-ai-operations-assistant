# Limitations

### Stale Request Recovery – Deployment Considerations

**Current implementation**

The stale request recovery mechanism runs as an asynchronous background task within the FastAPI application lifespan.

During application startup:
- PostgreSQL connectivity is verified.
- The stale request recovery worker is started.
- The worker periodically identifies stale `in_progress` requests.
- Recovered requests are marked `incomplete` with the reason `stale_request_recovery`.

During application shutdown:
- The recovery task is cancelled and awaited.
- PostgreSQL connections are disposed.
- Langfuse telemetry is flushed.

**Scaling limitation**

The current implementation starts one recovery worker per FastAPI application process. When the application scales to multiple Azure Container Apps replicas, each replica starts its own recovery worker.

The repository uses conditional database updates to reduce duplicate recovery of the same request. However, multiple workers can still perform redundant scans and increase database load.

**Production recommendation**

Before deploying multiple API replicas, decouple stale request recovery from the API application.

Recommended target architecture:
- Deploy the FastAPI service as an independently scalable Azure Container App.
- Deploy stale request recovery as a dedicated worker Container App.
- Configure the worker for one active replica.
- Use PostgreSQL advisory locking or equivalent distributed coordination to protect against overlapping worker instances and deployments.
- Continue using conditional database updates to ensure that only eligible stale requests are recovered.
- Monitor recovery counts, worker health, execution duration, and recovery failures through Prometheus and Grafana.

**Current status:** Suitable for local development and single-instance deployment. Distributed coordination and worker separation are required before production multi-replica scaling.

### To be implemented in Phase 2
# Azure Container Apps – Reliability Architecture Improvements

Status: Deferred

1. Extract stale_request_recovery_worker() from app/main.py.
2. Create a dedicated worker application.
3. Deploy the worker as a separate Azure Container App.
4. Configure one active worker replica.
5. Implement PostgreSQL advisory locking.
6. Preserve conditional stale-request updates.
7. Add worker health and recovery monitoring.
8. Update deployment documentation and architecture diagrams.