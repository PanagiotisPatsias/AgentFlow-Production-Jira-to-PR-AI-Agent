from pydantic import BaseModel

from agentflow.domain.enums import TicketValidationStatus
from agentflow.domain.jira_ticket import JiraTicket

class TicketValidationResult(BaseModel):
    status: TicketValidationStatus
    reasons: list[str]
    missing_fields: list[str]


def validate_ticket(ticket: JiraTicket) -> TicketValidationResult:
    reasons: list[str] = []
    missing_fields: list[str] = []
    if not ticket.key or not ticket.key.strip():
        raise ValueError("Jira ticket key is required")

    if not ticket.title or not ticket.title.strip():
        missing_fields.append("title")
        reasons.append("Ticket title is required.")

    if not ticket.description or not ticket.description.strip():
        missing_fields.append("description")
        reasons.append("Ticket description is required.")

    valid_criteria = [ criterion for criterion in (ticket.acceptance_criteria or []) if criterion.strip()]

    if not valid_criteria:
        missing_fields.append("acceptance_criteria")
        reasons.append("At least one non-empty acceptance criterion is required.")


    if missing_fields:
        validation_status = (
            TicketValidationStatus.CLARIFICATION_REQUIRED
        ) 
    else:
        validation_status = TicketValidationStatus.READY

    return TicketValidationResult(
        status=validation_status,
        reasons=reasons,
        missing_fields=missing_fields
    )   