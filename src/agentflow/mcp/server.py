from mcp.server.fastmcp import FastMCP

from agentflow.mcp.tools.approvals import register_approval_tools
from agentflow.mcp.tools.workflows import register_workflow_tools
from agentflow.services.workflow_service import WorkflowService


def create_agentflow_server(
    workflow_service: WorkflowService,
) -> FastMCP:
    mcp = FastMCP("agentflow")

    register_workflow_tools(mcp, workflow_service)
    register_approval_tools(mcp, workflow_service)

    return mcp


if __name__ == "__main__":
    workflow_service = WorkflowService()
    server = create_agentflow_server(workflow_service)

    server.run(transport="stdio")
