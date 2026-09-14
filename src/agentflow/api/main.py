from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agentflow.api.exception_handlers import register_exception_handlers
from agentflow.api.routes.workflows import router as workflows_router
from agentflow.api.routes.metrics import router as metrics_router
from agentflow.observability.logging import configure_logging

configure_logging(service="api")



app = FastAPI(
    title="AgentFlow API",
    description="Asynchronous Jira-to-GitHub PR agent workflow API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

register_exception_handlers(app)
app.include_router(workflows_router)
app.include_router(metrics_router)

@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
    }
