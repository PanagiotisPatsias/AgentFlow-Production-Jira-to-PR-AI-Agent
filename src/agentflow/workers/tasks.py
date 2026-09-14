from celery.signals import worker_process_shutdown, worker_shutdown

from agentflow.workers.celery_app import celery_app
from agentflow.workflows.jira_to_pr.graph import create_compiled_graph
from agentflow.workflows.jira_to_pr.runner import JiraPRWorkflowRunner


_workflow_runner: JiraPRWorkflowRunner | None = None
_checkpoint_pool = None


def _get_workflow_runner() -> JiraPRWorkflowRunner:
    """Initialize graph and checkpoint pool lazily in the Celery worker."""
    global _workflow_runner, _checkpoint_pool

    if _workflow_runner is None:
        compiled_graph, checkpoint_pool = create_compiled_graph()
        _checkpoint_pool = checkpoint_pool
        _workflow_runner = JiraPRWorkflowRunner(compiled_graph)

    return _workflow_runner


def _close_checkpoint_pool(**kwargs) -> None:
    global _workflow_runner, _checkpoint_pool

    if _checkpoint_pool is not None and not _checkpoint_pool.closed:
        _checkpoint_pool.close()

    _checkpoint_pool = None
    _workflow_runner = None


worker_process_shutdown.connect(_close_checkpoint_pool)
worker_shutdown.connect(_close_checkpoint_pool)


@celery_app.task(name="agentflow.health_check")
def health_check(message: str) -> dict:
    return {
        "status": "ok",
        "message": message,
    }


@celery_app.task(
    bind=True,
    name="agentflow.run_jira_to_pr_workflow",
)
def run_jira_to_pr_workflow(
    self,
    run_id: str,
    ticket_key: str,
    repository_url: str,
    base_branch: str = "main",
) -> dict:
    return _get_workflow_runner().start(
        run_id=run_id,
        ticket_key=ticket_key,
        repository_url=repository_url,
        base_branch=base_branch,
        celery_task_id=self.request.id,
    )


@celery_app.task(name="agentflow.resume_jira_to_pr_workflow")
def resume_jira_to_pr_workflow(
    run_id: str,
    decision: str,
    feedback: str = "",
) -> dict:
    return _get_workflow_runner().resume(
        run_id=run_id,
        decision=decision,
        feedback=feedback,
    )
