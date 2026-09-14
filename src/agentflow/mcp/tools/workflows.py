from mcp.server.fastmcp import FastMCP

from agentflow.mcp.schemas.requests import StartWorkflowInput
from agentflow.mcp.schemas.responses import (
    WorkflowStatusResult,
    WorkflowTaskResult,
)
from agentflow.services.workflow_service import WorkflowService


def register_workflow_tools(
    mcp: FastMCP,
    workflow_service: WorkflowService,
) -> None:
    @mcp.tool()
    def start_workflow(
        ticket_key: str,
        repository_url: str,
        base_branch: str = "main",
    ) -> dict:
        """Start an asynchronous Jira-to-GitHub pull request workflow."""

        request = StartWorkflowInput(
            ticket_key=ticket_key,
            repository_url=repository_url,
            base_branch=base_branch,
        )
        result = workflow_service.start_workflow(
            ticket_key=request.ticket_key,
            repository_url=request.repository_url,
            base_branch=request.base_branch,
        )
        return WorkflowTaskResult.model_validate(result).model_dump(
            mode="json"
        )

    @mcp.tool()
    def get_workflow_status(run_id: str) -> dict:
        """Return the status and current stage of a workflow run."""

        result = workflow_service.get_workflow(run_id)
        return WorkflowStatusResult.model_validate(result).model_dump(
            mode="json"
        )
