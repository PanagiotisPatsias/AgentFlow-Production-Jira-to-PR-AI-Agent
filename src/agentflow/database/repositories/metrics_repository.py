from agentflow.database.models.workflow_run import WorkflowRun
from agentflow.database.models.workflow_event import WorkflowEvent
from sqlalchemy import select, func
from sqlalchemy.orm import Session

class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def count_workflows_by_status(self):
        statement = (
            select(
                WorkflowRun.status,
                func.count(WorkflowRun.id),
            )
            .group_by(WorkflowRun.status)
        )

        return self.session.execute(statement).all()

    def count_nodes_by_status(self):
        statement = (
                select(
                    WorkflowEvent.node_name,
                    WorkflowEvent.status,
                    func.count(WorkflowEvent.id),
                )
                .group_by(
                    WorkflowEvent.node_name,
                    WorkflowEvent.status,
                )
            )

        return self.session.execute(statement).all()

    def get_node_duration_statistics(self):
        statement = (
            select(
                WorkflowEvent.node_name,
                func.count(
                    WorkflowEvent.duration_ms
                ).label("execution_count"),
                func.sum(
                    WorkflowEvent.duration_ms
                ).label("duration_sum_ms"),
                func.avg(
                    WorkflowEvent.duration_ms
                ).label("duration_avg_ms"),
            )
            .where(
                WorkflowEvent.duration_ms.is_not(None)
            )
            .group_by(
                WorkflowEvent.node_name
            )
        )

        return self.session.execute(statement).all()
        