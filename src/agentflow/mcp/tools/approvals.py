from mcp.server.fastmcp import FastMCP

from agentflow.mcp.schemas.requests import (
    ApprovalDecision,
    SubmitApprovalInput,
)
from agentflow.mcp.schemas.responses import WorkflowTaskResult
from agentflow.services.workflow_service import WorkflowService


def register_approval_tools(
    mcp: FastMCP,
    workflow_service: WorkflowService,
) -> None:
    @mcp.tool()
    def submit_workflow_approval(
        run_id: str,
        decision: ApprovalDecision,
        feedback: str = "",
    ) -> dict:
        """Approve, reject, or request changes for a paused workflow."""

        request = SubmitApprovalInput(
            run_id=run_id,
            decision=decision,
            feedback=feedback,
        )
        result = workflow_service.submit_approval(
            run_id=request.run_id,
            decision=request.decision,
            feedback=request.feedback,
        )
        return WorkflowTaskResult.model_validate(result).model_dump(
            mode="json"
        )
