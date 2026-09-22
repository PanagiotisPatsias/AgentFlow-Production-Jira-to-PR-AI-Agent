# AgentFlow system design

These four diagrams have been reconciled with the current API, service, worker,
graph, persistence and observability code. The proposed Kong API Gateway is
explicitly marked **planned**.

| Diagram | What it explains | Details |
| --- | --- | --- |
| [Overall architecture](00-overall/diagram.svg) | Clients, gateway proposal, backend, queue, worker, persistence, integrations and observability | [Design notes](00-overall/design.md) |
| [End-to-End Request Lifecycle](02-async-execution/diagram.svg) | Start → execute → pause → approve → resume → publish, including both human gates | [Design notes](02-async-execution/design.md) |
| [LangGraph workflow](03-langgraph-workflow/diagram.svg) | Exact nodes, conditional routes, repair loops and terminal paths | [Design notes](03-langgraph-workflow/design.md) |
| [Durable persistence](06-persistence/diagram.svg) | Operational run history, LangGraph checkpoint state and resume correlation | [Design notes](06-persistence/design.md) |

The dashboard screenshot used by the root README is stored at
[`assets/screenshots/dashboard.png`](assets/screenshots/dashboard.png).

## Edit and regenerate

The refreshed diagrams above are generated from [`render-diagrams.mjs`](render-diagrams.mjs), using [vendored SVG brand assets](assets/logos/README.md). From the repository root:

```bash
node system_design/render-diagrams.mjs
```

No npm installation or internet connection is required. The command regenerates
`diagram.svg` and `diagram.mmd` for all four design sections. Edit the renderer's
source data and paths rather than changing generated files by hand. Mermaid
exports preserve the logical relationships; the SVGs provide the designed layouts.
