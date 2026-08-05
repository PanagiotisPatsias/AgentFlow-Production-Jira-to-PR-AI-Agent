from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from agentflow.services.exceptions import (
    WorkflowDispatchError,
    WorkflowNotFoundError,
    WorkflowStateConflictError,
)


async def workflow_not_found_handler(
    request: Request,
    exc: WorkflowNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def workflow_state_conflict_handler(
    request: Request,
    exc: WorkflowStateConflictError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


async def workflow_dispatch_error_handler(
    request: Request,
    exc: WorkflowDispatchError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        WorkflowNotFoundError,
        workflow_not_found_handler,
    )
    app.add_exception_handler(
        WorkflowStateConflictError,
        workflow_state_conflict_handler,
    )
    app.add_exception_handler(
        WorkflowDispatchError,
        workflow_dispatch_error_handler,
    )
