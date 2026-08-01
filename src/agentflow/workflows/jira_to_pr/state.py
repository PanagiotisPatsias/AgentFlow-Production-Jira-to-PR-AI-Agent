from pydantic import BaseModel
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.ticket_validation import TicketValidationResult
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.plan_validation import PlanValidationResult
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.domain.patch_validation import PatchValidationResult
from agentflow.domain.verification import VerificationResult
from agentflow.domain.code_review import (
    CodeReviewResult,
    ReviewValidationResult,
)
from agentflow.domain.pull_request import PullRequestResult


class JiraToPRState(BaseModel):
    ticket_key: str
    repository_url: str
    base_branch: str = "main"

    ticket: JiraTicket | None = None
    validation: TicketValidationResult | None = None
    workspace_path: str | None = None
    error: str | None = None
    repository_context: str | None = None
    implementation_plan: ImplementationPlan | None = None

    plan_validation: PlanValidationResult | None = None
    plan_approval_status: str | None = None
    approval_feedback: str | None = None
    branch_name: str | None = None
    patch_proposal: PatchProposal | None = None
    patch_validation: PatchValidationResult | None = None
    patch_generation_attempts: int = 0
    max_patch_generation_attempts: int = 3
    patch_applied: bool = False
    verification_result: VerificationResult | None = None
    repair_attempts: int = 0
    max_repair_attempts: int = 3
    repair_patch_proposal: PatchProposal | None = None
    repair_patch_validation: PatchValidationResult | None = None
    code_review: CodeReviewResult | None = None
    review_validation: ReviewValidationResult | None = None
    pr_approval_status: str | None = None
    pr_approval_feedback: str | None = None
    commit_sha: str | None = None
    branch_pushed: bool = False
    pull_request: PullRequestResult | None = None
