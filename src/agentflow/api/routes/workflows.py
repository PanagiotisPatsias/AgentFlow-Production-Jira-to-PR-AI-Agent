from fastapi import APIRouter, status
from agentflow.services.workflow_service import WorkflowService
from uuid import UUID
from agentflow.api.schemas.workflows import (
    StartWorkflowRequest,
    WorkflowTaskResponse,
    SubmitApprovalRequest,
    WorkflowStatusResponse
)


router = APIRouter(
    prefix="/api/v1/workflows",
    tags = ["workflows"]
)

workflow_service = WorkflowService()


@router.post(
    "",
    response_model=WorkflowTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_workflow(
    request: StartWorkflowRequest,
) -> WorkflowTaskResponse:
    result = workflow_service.start_workflow(
        request.ticket_key,
        request.repository_url,
        request.base_branch,
    )
    return WorkflowTaskResponse(**result)


@router.post(
    "/{run_id}/approval",
    response_model=WorkflowTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def give_approval(
    run_id: UUID,
    request: SubmitApprovalRequest,
) -> WorkflowTaskResponse:
    result = workflow_service.submit_approval(
        str(run_id),
        request.decision,
        request.feedback,
    )
    return WorkflowTaskResponse(**result)


@router.get(
    "/{run_id}",
    response_model=WorkflowStatusResponse,
)
def get_workflow(run_id: UUID) -> WorkflowStatusResponse:
    result = workflow_service.get_workflow(str(run_id))
    return WorkflowStatusResponse(**result)
