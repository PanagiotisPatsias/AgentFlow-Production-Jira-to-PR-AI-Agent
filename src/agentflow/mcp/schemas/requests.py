from typing import Literal, TypeAlias

from pydantic import BaseModel, Field


ApprovalDecision: TypeAlias = Literal[
    "approve",
    "reject",
    "request_changes",
]


class StartWorkflowInput(BaseModel):
    ticket_key: str = Field(min_length=1)
    repository_url: str = Field(min_length=1)
    base_branch: str = Field(default="main", min_length=1)


class SubmitApprovalInput(BaseModel):
    run_id: str = Field(min_length=1)
    decision: ApprovalDecision
    feedback: str = ""
