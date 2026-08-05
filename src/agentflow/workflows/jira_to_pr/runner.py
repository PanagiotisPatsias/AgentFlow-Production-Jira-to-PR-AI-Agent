from  uuid import UUID
from agentflow.database.repositories.workflow_run_repository import WorkflowRunRepository
from agentflow.database.session import SessionLocal
from agentflow.database.enums import WorkflowRunStatus
from langgraph.types import Command

class JiraPRWorkflowRunner:

    def __init__(self, graph):
        self.graph = graph

    def start(self, run_id:str, ticket_key: str, repository_url:str, base_branch:str, celery_task_id: str | None = None) -> dict:

        workflow_run_id = UUID(run_id)
        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)
            if celery_task_id :
                repository.set_celery_task_id(workflow_run_id, celery_task_id)

            repository.update_status(workflow_run_id,status = WorkflowRunStatus.RUNNING, current_stage = "graph_execution" )

        initial_input = {
                "run_id": workflow_run_id,
                "ticket_key": ticket_key,
                "repository_url": repository_url,
                "base_branch":  base_branch,
            }

        config = {
            "configurable": {
            "thread_id": str(workflow_run_id),
                            }
                }
        try:

            current_state = self.graph.invoke(
                initial_input,
                config = config
            )

            interrupts = current_state.get("__interrupt__",[])

            if interrupts:
                approval_request = interrupts[0].value
                approval_type = approval_request.get(
                                                    "type",
                                                    "human_approval",
                                                    )
                if approval_type == "plan_approval":
                    approval_node_name = "plan_approval_node"

                elif approval_type == "pull_request_approval":
                    approval_node_name = "human_pr_approval_node"

                else:
                    approval_node_name = "unknown_approval_node"


                with SessionLocal() as session:
                    repository = WorkflowRunRepository(session)
                    repository.update_status(
                        run_id=workflow_run_id,
                        status=WorkflowRunStatus.WAITING_FOR_APPROVAL,
                        current_stage=approval_node_name,
                                )

                    repository.add_event(
                                        run_id=workflow_run_id,
                                        node_name=approval_node_name,
                                        status="WAITING_FOR_APPROVAL",
                                        details={"approval_type": approval_type},
                                        )
                return {
                    "run_id": run_id,
                    "status": WorkflowRunStatus.WAITING_FOR_APPROVAL.value,
                    "approval_type": approval_type,
                    "question": approval_request.get("question"),
                    "allowed_decisions": approval_request.get(
                        "allowed_decisions",
                        [],
                    ),
                }


            else:
                with SessionLocal() as session:
                    repository = WorkflowRunRepository(session)
                    repository.update_status(
                        run_id=workflow_run_id,
                        status=WorkflowRunStatus.COMPLETED,
                        current_stage="END",
                                )
                return {
                            "run_id": run_id,
                            "status": WorkflowRunStatus.COMPLETED.value,
                        }


        except Exception as exc:
            with SessionLocal() as session:
                repository = WorkflowRunRepository(session)
                failed_run = repository.get_run(workflow_run_id)
                failed_stage = (
                    failed_run.current_stage
                    if failed_run is not None
                    else "graph_execution"
                )
                repository.update_status(
                    run_id=workflow_run_id,
                    status=WorkflowRunStatus.FAILED,
                    current_stage=failed_stage,
                    error_message=str(exc),
                )
            raise







    def resume(self, run_id: str, decision: str, feedback: str) -> dict:
        workflow_run_id = UUID(run_id)

        allowed_decisions = {
            "approve",
            "reject",
            "request_changes",
        }

        if decision not in allowed_decisions:
            raise ValueError(f"Invalid approval decision: {decision}")

        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)
            workflow_run = repository.get_run(workflow_run_id)

            if workflow_run is None:
                raise ValueError(
                    f"Workflow run was not found: {workflow_run_id}"
                )

            if workflow_run.status != WorkflowRunStatus.WAITING_FOR_APPROVAL.value:
                raise ValueError("Workflow is not waiting for approval")

            approval_node_name = workflow_run.current_stage
            approval_types = {
                "plan_approval_node": "plan_approval",
                "human_pr_approval_node": "pull_request_approval",
            }
            approval_type = approval_types.get(approval_node_name)

            if approval_type is None:
                raise ValueError(
                    f"Unknown approval stage: {approval_node_name}"
                )

            decision_event_status = {
                "approve": "APPROVED",
                "reject": "REJECTED",
                "request_changes": "CHANGES_REQUESTED",
            }[decision]

            repository.add_event(
                run_id=workflow_run_id,
                node_name=approval_node_name,
                status=decision_event_status,
                details={
                    "approval_type": approval_type,
                    "decision": decision,
                    "has_feedback": bool(feedback),
                },
            )

            repository.update_status(
                run_id=workflow_run_id,
                status=WorkflowRunStatus.RUNNING,
                current_stage=approval_node_name,
            )

        config = {
            "configurable": {
                "thread_id": str(workflow_run_id),
            }
        }

        try:
            current_state = self.graph.invoke(
                Command(
                    resume={
                        "decision": decision,
                        "feedback": feedback,
                    }
                ),
                config=config,
            )

            interrupts = current_state.get("__interrupt__", [])
            if interrupts:
                approval_request = interrupts[0].value
                next_approval_type = approval_request.get(
                    "type",
                    "human_approval",
                )
                approval_nodes = {
                    "plan_approval": "plan_approval_node",
                    "pull_request_approval": "human_pr_approval_node",
                }
                next_approval_node = approval_nodes.get(
                    next_approval_type,
                    "unknown_approval_node",
                )

                with SessionLocal() as session:
                    repository = WorkflowRunRepository(session)
                    repository.update_status(
                        run_id=workflow_run_id,
                        status=WorkflowRunStatus.WAITING_FOR_APPROVAL,
                        current_stage=next_approval_node,
                    )
                    repository.add_event(
                        run_id=workflow_run_id,
                        node_name=next_approval_node,
                        status="WAITING_FOR_APPROVAL",
                        details={
                            "approval_type": next_approval_type,
                        },
                    )

                return {
                    "run_id": run_id,
                    "status": WorkflowRunStatus.WAITING_FOR_APPROVAL.value,
                    "approval_type": next_approval_type,
                    "question": approval_request.get("question"),
                    "allowed_decisions": approval_request.get(
                        "allowed_decisions",
                        [],
                    ),
                }

            terminal_status = (
                WorkflowRunStatus.REJECTED
                if decision == "reject"
                else WorkflowRunStatus.COMPLETED
            )
            terminal_stage = (
                "REJECTED"
                if terminal_status == WorkflowRunStatus.REJECTED
                else "END"
            )

            with SessionLocal() as session:
                repository = WorkflowRunRepository(session)
                repository.update_status(
                    run_id=workflow_run_id,
                    status=terminal_status,
                    current_stage=terminal_stage,
                )

            return {
                "run_id": run_id,
                "status": terminal_status.value,
            }

        except Exception as exc:
            with SessionLocal() as session:
                repository = WorkflowRunRepository(session)
                failed_run = repository.get_run(workflow_run_id)
                failed_stage = (
                    failed_run.current_stage
                    if failed_run is not None
                    else "graph_execution"
                )
                repository.add_event(
                    run_id=workflow_run_id,
                    node_name="workflow_resume",
                    status="FAILED",
                    details={
                        "exception_type": type(exc).__name__,
                    },
                    error_message=str(exc),
                )
                repository.update_status(
                    run_id=workflow_run_id,
                    status=WorkflowRunStatus.FAILED,
                    current_stage=failed_stage,
                    error_message=str(exc),
                )
            raise


