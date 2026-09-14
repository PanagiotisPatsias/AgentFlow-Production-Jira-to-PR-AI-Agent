from fastapi import APIRouter, Response
from agentflow.observability.exporter import MetricsExporter
from prometheus_client import CONTENT_TYPE_LATEST


router = APIRouter(
    tags=["observability"],
)

metrics_exporter = MetricsExporter()


@router.get("/metrics", include_in_schema=False)
def get_metrics() -> Response:
    metrics_content = metrics_exporter.render()

    return Response(
        content=metrics_content,
        media_type=CONTENT_TYPE_LATEST,
    )
