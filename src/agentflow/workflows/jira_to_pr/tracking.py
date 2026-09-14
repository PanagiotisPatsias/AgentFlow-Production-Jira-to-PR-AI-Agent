from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.database.repositories.workflow_run_repository import WorkflowRunRepository
import time 
from agentflow.database.session import SessionLocal
from agentflow.database.enums import WorkflowRunStatus
import logging


logger = logging.getLogger(__name__)

def create_tracked_node( node_name:str, node_function):

    def tracked_node(state:JiraToPRState):
        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)

            repository.update_status(
                state.run_id,
                status=WorkflowRunStatus.RUNNING,
                current_stage=node_name,
            )

        start_time = time.monotonic()
        try:
            
            logger.info(
                 "Node started",
                 extra = {
                      "run_id": str(state.run_id),
                        "node_name": node_name,
                        "status": "RUNNING",
                 }
            )

            result =  node_function(state)

        except Exception as exc:
                duration_ms = int(
                    (time.monotonic() - start_time) * 1000
                )

                details = {
                    "exception_type": type(exc).__name__,
                }

                logger.exception(
                    "Node failed",
                    extra={
                        "run_id": str(state.run_id),
                        "node_name": node_name,
                        "status": "FAILED",
                        "duration_ms": duration_ms,
                        "error_type": type(exc).__name__,
                    },)


                with SessionLocal() as session:
                    repository = WorkflowRunRepository(session)

                    repository.add_event(
                        run_id=state.run_id,
                        node_name=node_name,
                        status="FAILED",
                        details=details,
                        error_message=str(exc),
                        duration_ms=duration_ms,
                    )

                    repository.update_status(
                        run_id=state.run_id,
                        status=WorkflowRunStatus.FAILED,
                        current_stage=node_name,
                        error_message=str(exc),
                    )

                raise
        details = {"message": f"Node {node_name} completed successfully"}
        duration_ms = int((time.monotonic() - start_time) * 1000)
        with SessionLocal() as session:
            repository = WorkflowRunRepository(session)
            repository.add_event(state.run_id, node_name, status="COMPLETED",
                                                            details= details, duration_ms = duration_ms )
        
        logger.info(
                    "Node completed",
                    extra={
                        "run_id": str(state.run_id),
                        "node_name": node_name,
                        "status": "COMPLETED",
                        "duration_ms": duration_ms,
                    },
                )
        return result
    return tracked_node

           
