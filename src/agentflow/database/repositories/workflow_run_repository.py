from agentflow.database.models.workflow_run import WorkflowRun
from agentflow.database.models.workflow_event import WorkflowEvent
from agentflow.database.enums import WorkflowRunStatus
from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

class WorkflowRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(self, ticket_key:str , repository_url:str, input_data: dict)-> WorkflowRun:
        workflow_run = WorkflowRun(
        ticket_key=ticket_key,
        repository_url=repository_url,
        status=WorkflowRunStatus.PENDING.value,
        current_stage="CREATED",
        input_data=input_data,
    )

        self.session.add(workflow_run)
        self.session.commit()
        self.session.refresh(workflow_run)

        return workflow_run

        

    def get_run(self,run_id:uuid.UUID) -> WorkflowRun | None:
        statetment  = select(WorkflowRun)
        statetment = statetment.where(WorkflowRun.id == run_id)
        result = self.session.execute(statetment)
        return result.scalar_one_or_none()
        

    def update_status(
        self,
        run_id: uuid.UUID,
        status: WorkflowRunStatus | str,
        current_stage: str,
        result_data: dict | None = None,
        error_message: str | None = None,
    ) -> WorkflowRun:

        workflow_run = self.get_run(run_id)
        if not workflow_run:
            raise ValueError (f"Workflow run was not found: {run_id}")

        status_value = (
            status.value
            if isinstance(status, WorkflowRunStatus)
            else status
        )

        workflow_run.status = status_value
        workflow_run.current_stage = current_stage

        if result_data is not None:
            workflow_run.result_data = result_data

        if error_message is not None:
            workflow_run.error_message = error_message

        terminal_statuses = {
            WorkflowRunStatus.COMPLETED.value,
            WorkflowRunStatus.FAILED.value,
            WorkflowRunStatus.REJECTED.value,
        }
        if status_value in terminal_statuses:
            workflow_run.completed_at = datetime.now(timezone.utc)

        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(workflow_run)


        return workflow_run

    def set_celery_task_id(self, run_id: uuid.UUID, celery_task_id: str) -> WorkflowRun:
        workflow_run = self.get_run(run_id)
        if workflow_run is None:
            raise ValueError(f"Workflow run was not found: {run_id}")

        workflow_run.celery_task_id = celery_task_id

        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(workflow_run)
        return workflow_run




    def add_event(self, run_id: uuid.UUID, node_name:str , status: str, details:dict, error_message:str |None = None, duration_ms: int | None = None) -> WorkflowEvent:


        event = WorkflowEvent(run_id = run_id, node_name =node_name, 
                             status = status, details = details, 
                             error_message = error_message , duration_ms = duration_ms)

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event
        
