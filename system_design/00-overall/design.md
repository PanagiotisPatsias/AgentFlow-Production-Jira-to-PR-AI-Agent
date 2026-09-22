# Overall architecture

[![AgentFlow architecture](diagram.svg)](diagram.svg)

This is the README-level view of the current application with the proposed Kong API Gateway clearly marked **planned**. The dashboard currently calls FastAPI directly; no gateway has been added to the running system by this documentation change.

## Reading the diagram

1. Next.js provides start, status and approval controls. FastAPI delegates to `WorkflowService`, which persists run data and dispatches Celery tasks through Redis.
2. A Celery worker calls `JiraPRWorkflowRunner`. The compiled LangGraph and its PostgreSQL checkpoint pool are initialized in the worker process. They are not independent network services.
3. PostgreSQL holds both operational tables (`workflow_runs`, `workflow_events`) and LangGraph checkpoint tables. The service reads/writes run records; the runner updates run lifecycle status; tracked nodes write event records; the graph checkpointer persists graph state.
4. Graph nodes call structured-output agents and controlled tools. These connect to OpenAI, Jira and GitHub, operate on a local Git workspace, and use Docker for verification.
5. FastMCP is a second control interface. It serves stdio tools to an MCP-compatible client and calls `WorkflowService` directly, bypassing HTTP and the proposed gateway.

The main drawing groups the API with its service and the worker with its runner for readability. The MCP arrow specifically points to the service, not an HTTP endpoint.

## Approval and durability

There are two graph interrupts: plan approval before creating the implementation branch, and publication approval after verification/review, before commit/push/PR creation.

At an interrupt, the graph persists state via PostgreSQL and returns to the runner. The runner records `WAITING_FOR_APPROVAL`, adds an event and returns a task result. The task ends; the worker process stays alive. Submitting a decision enqueues a new resume task with the same `run_id`/`thread_id`.

A checkpoint can be loaded by another compatible worker process. Moving execution to another host additionally requires access to the existing local workspace; shared PostgreSQL/Redis alone do not provide that.

## Metrics and logs

- Prometheus scrapes FastAPI's `/metrics`, whose exporter queries PostgreSQL run/event records.
- API and worker processes write JSONL files. Alloy tails the files, adds labels and sends logs to Loki.
- Grafana queries Prometheus and Loki. Observability arrows indicate the direction of data flow, rather than the HTTP initiator.

## Planned gateway

The amber route shows the proposed `Next.js → Kong → FastAPI` HTTP boundary. TLS termination, rate limiting and authentication are planned responsibilities, not implemented guarantees. Adding Kong does not replace Celery, Redis, LangGraph or persistence.

## Sources and rendering

Edit the overview nodes and edges in [`../render-diagrams.mjs`](../render-diagrams.mjs), then run from the repository root:

```bash
node system_design/render-diagrams.mjs
```

This generates `diagram.svg` and the semantic Mermaid export `diagram.mmd` together. The SVG uses locally vendored brand marks, original colour variants where available, no component background panels, and no remote image dependencies. See [logo provenance](../assets/logos/README.md).

Implementation references: [WorkflowService](../../src/agentflow/services/workflow_service.py), [tasks](../../src/agentflow/workers/tasks.py), [runner](../../src/agentflow/workflows/jira_to_pr/runner.py), [graph](../../src/agentflow/workflows/jira_to_pr/graph.py), [MCP](../../src/agentflow/mcp/server.py), [infrastructure](../../infra/).
