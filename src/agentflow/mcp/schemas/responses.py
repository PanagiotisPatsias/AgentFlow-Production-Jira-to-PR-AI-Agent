from datetime import datetime

from pydantic import BaseModel


class WorkflowTaskResult(BaseModel):
    run_id: str
    celery_task_id: str
    status: str


class WorkflowStatusResult(BaseModel):
    run_id: str
    ticket_key: str
    repository_url: str
    status: str
    current_stage: str | None = None
    celery_task_id: str | None = None
    result_data: dict | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
