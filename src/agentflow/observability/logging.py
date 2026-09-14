import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format Python log records as one JSON object per line."""

    CONTEXT_FIELDS = (
        "run_id",
        "ticket_key",
        "node_name",
        "celery_task_id",
        "status",
        "duration_ms",
        "error_type",
        "attempt",
    )

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in self.CONTEXT_FIELDS:
            field_value = getattr(record, field_name, None)
            if field_value is not None:
                log_data[field_name] = field_value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            log_data,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
    service: str,
    level: str = "INFO",
) -> None:
    """Emit structured logs to stdout and a bounded local JSONL file."""

    formatter = JsonFormatter(service=service)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    log_directory = Path(
        os.getenv("AGENTFLOW_LOG_DIR", "logs")
    )
    log_directory.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_directory / f"{service}.jsonl",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    for existing_handler in root_logger.handlers:
        existing_handler.close()

    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
