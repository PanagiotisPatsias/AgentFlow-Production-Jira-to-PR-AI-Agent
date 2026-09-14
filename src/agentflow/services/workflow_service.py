from agentflow.database.repositories.workflow_run_repository import WorkflowRunRepository
from agentflow.workers.celery_app import celery_app
from agentflow.database.enums import WorkflowRunStatus
from agentflow.database.session import SessionLocal
from kombu.exceptions import OperationalError
from uuid import UUID
from agentflow.services.exceptions import (
    WorkflowDispatchError,
    WorkflowNotFoundError,
    WorkflowStateConflictError,
)

class WorkflowService:


    def start_workflow(self, ticket_key:str, repository_url:str, base_branch:str)->dict:
        input_data = {
                    "ticket_key": ticket_key,
                    "repository_url": repository_url,
                    "base_branch": base_branch,
                    }
        with SessionLocal()  as session:
            repository = WorkflowRunRepository(session)

            workflow_run = repository.create_run(ticket_key = ticket_key,  repository_url = repository_url, input_data = input_data  )
            workflow_id = str(workflow_run.id)
            workflow_run_id = workflow_run.id

        try:
            result = celery_app.send_task(
                "agentflow.run_jira_to_pr_workflow",
                kwargs={
                    "run_id": workflow_id,
                    "ticket_key": ticket_key,
                    "repository_url": repository_url,
                    "base_branch": base_branch,
                },
            )
        except OperationalError as exc:
            with SessionLocal() as session:
                repository = WorkflowRunRepository(session)
                repository.update_status(
                    run_id=workflow_run_id,
                    status=WorkflowRunStatus.FAILED,
                    current_stage="task_dispatch",
                    error_message=str(exc),
                )
            raise WorkflowDispatchError(
                "Workflow could not be queued because Celery is unavailable"
            ) from exc

        with SessionLocal()  as session:
            repository = WorkflowRunRepository(session)
            repository.set_celery_task_id(workflow_run_id, result.id)

        return {
                    "run_id": workflow_id,
                    "celery_task_id": result.id,
                    "status": WorkflowRunStatus.PENDING.value,
                }
        
        


    def submit_approval(self, run_id:str, decision:str, feedback:str) -> dict:
        workflow_run_id = UUID(run_id)

        with SessionLocal()  as session:
            repository = WorkflowRunRepository(session)

            workflow = repository.get_run(workflow_run_id)

            if workflow is None:
                raise WorkflowNotFoundError(
                    f"Workflow run was not found: {run_id}"
                )

            if workflow.status != WorkflowRunStatus.WAITING_FOR_APPROVAL.value:
                raise WorkflowStateConflictError("Workflow is not waiting for approval")

        try:
            result = celery_app.send_task(
                "agentflow.resume_jira_to_pr_workflow",
                kwargs={
                    "run_id": run_id,
                    "decision": decision,
                    "feedback": feedback,
                },
            )
        except OperationalError as exc:
            raise WorkflowDispatchError(
                "Approval could not be queued because Celery is unavailable"
            ) from exc

        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)
            repository.set_celery_task_id(
                workflow_run_id,
                result.id,
            )

        return {
            "run_id": run_id,
            "celery_task_id": result.id,
            "status": "APPROVAL_QUEUED",
        }
    



    def get_workflow(self, run_id: str) -> dict:
        workflow_run_id = UUID(run_id)

        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)
            workflow = repository.get_run(workflow_run_id)

            if workflow is None:
                raise WorkflowNotFoundError(
                    f"Workflow run was not found: {run_id}"
                )

            return {
                "run_id": str(workflow.id),
                "ticket_key": workflow.ticket_key,
                "repository_url": workflow.repository_url,
                "status": workflow.status,
                "current_stage": workflow.current_stage,
                "celery_task_id": workflow.celery_task_id,
                "result_data": workflow.result_data,
                "error_message": workflow.error_message,
                "created_at": workflow.created_at,
                "updated_at": workflow.updated_at,
                "completed_at": workflow.completed_at,
            }
