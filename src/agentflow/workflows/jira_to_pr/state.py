from pydantic import BaseModel
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.ticket_validation import TicketValidationResult
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.plan_validation import PlanValidationResult



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

    