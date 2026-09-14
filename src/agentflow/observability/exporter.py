from agentflow.database.session import SessionLocal
from agentflow.database.repositories.metrics_repository import MetricsRepository
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
)


class MetricsExporter:
    def render(self) -> bytes:
        registry = CollectorRegistry()

        workflows_by_status = Gauge(
            "agentflow_workflows_by_status",
            "Number of workflows grouped by status",
            ["status"],
            registry=registry,
        )

        nodes_by_status = Gauge(
            "agentflow_node_executions_by_status",
            "Number of LangGraph node executions grouped by node and status",
            ["node_name", "status"],
            registry=registry,
        )

        node_duration_count = Gauge(
            "agentflow_node_duration_seconds_count",
            "Number of recorded LangGraph node execution durations",
            ["node_name"],
            registry=registry,
        )

        node_duration_sum = Gauge(
            "agentflow_node_duration_seconds_sum",
            "Total LangGraph node execution duration in seconds",
            ["node_name"],
            registry=registry,
        )

        node_duration_average = Gauge(
            "agentflow_node_duration_seconds_average",
            "Average LangGraph node execution duration in seconds",
            ["node_name"],
            registry=registry,
        )

        with SessionLocal() as session:
            repository = MetricsRepository(session)

            workflow_counts = repository.count_workflows_by_status()
            node_counts = repository.count_nodes_by_status()
            duration_statistics = (
                repository.get_node_duration_statistics()
            )

            for status, count in workflow_counts:
                workflows_by_status.labels(
                    status=status,
                ).set(count)

            for node_name, status, count in node_counts:
                nodes_by_status.labels(
                    node_name=node_name,
                    status=status,
                ).set(count)

            for (
                node_name,
                execution_count,
                duration_sum_ms,
                duration_average_ms,
            ) in duration_statistics:
                node_duration_count.labels(
                    node_name=node_name,
                ).set(execution_count)

                node_duration_sum.labels(
                    node_name=node_name,
                ).set(float(duration_sum_ms) / 1000)

                node_duration_average.labels(
                    node_name=node_name,
                ).set(float(duration_average_ms) / 1000)

        return generate_latest(registry)

            
