"""Definitions for process-level Prometheus metrics.

Workflow and node metrics are exported from durable PostgreSQL records by
``MetricsExporter`` instead of being maintained in Celery worker memory.
"""
