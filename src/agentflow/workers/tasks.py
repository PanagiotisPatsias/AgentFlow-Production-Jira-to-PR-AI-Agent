from agentflow.workers.celery_app import celery_app
from agentflow.workflows.jira_to_pr.graph import graph
from agentflow.workflows.jira_to_pr.runner import JiraPRWorkflowRunner


workflow_runner = JiraPRWorkflowRunner(graph)


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
    return workflow_runner.start(
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
    return workflow_runner.resume(
        run_id=run_id,
        decision=decision,
        feedback=feedback,
    )
