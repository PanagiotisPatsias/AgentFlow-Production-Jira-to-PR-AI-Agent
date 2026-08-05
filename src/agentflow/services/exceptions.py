class WorkflowServiceError(Exception):
    pass


class WorkflowNotFoundError(WorkflowServiceError):
    pass


class WorkflowStateConflictError(WorkflowServiceError):
    pass


class WorkflowDispatchError(WorkflowServiceError):
    pass