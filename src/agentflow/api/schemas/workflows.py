from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class StartWorkflowRequest(BaseModel):
    ticket_key:str
    repository_url: str
    base_branch: str = "main"

class SubmitApprovalRequest(BaseModel):
    decision: Literal[
        "approve",
        "reject",
        "request_changes"
    ]
    feedback: str = ""

class WorkflowTaskResponse(BaseModel):
    run_id: str
    celery_task_id: str
    status: str


class WorkflowStatusResponse(BaseModel):
    run_id: str
    ticket_key: str
    repository_url: str
    status: str
    current_stage: str | None
    celery_task_id: str | None
    result_data: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None