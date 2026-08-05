from fastapi import FastAPI

from agentflow.api.exception_handlers import register_exception_handlers
from agentflow.api.routes.workflows import router as workflows_router


app = FastAPI(
    title="AgentFlow API",
    description="Asynchronous Jira-to-GitHub PR agent workflow API",
    version="0.1.0",
)

register_exception_handlers(app)
app.include_router(workflows_router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
    }

