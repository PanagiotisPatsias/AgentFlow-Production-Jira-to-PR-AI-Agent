from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.ticket_validation import validate_ticket
from agentflow.domain.enums import TicketValidationStatus
import pytest


def test_complete_ticket_is_ready():
    ticket = JiraTicket(
        key="APP-42",
        title="Add account lockout",
        description="Lock an account after five failed login attempts.",
        priority="High",
        acceptance_criteria=[
            "Lock the account after five failed attempts",
            "Reset the counter after a successful login",
            "Add unit tests",
        ],
        issue_type="Story",
        status="To Do",
        labels=["authentication", "security"],
    )

    result = validate_ticket(ticket)

    assert result.status == TicketValidationStatus.READY
    assert result.missing_fields == []




def test_incomplete_ticket_requires_clarification():
                
    ticket = JiraTicket(
        key="APP-43",
        title="Fix authentication",
        description="",
        priority="Medium",
        acceptance_criteria=[],
        issue_type="Bug",
        status="To Do",
        labels=["authentication"],
    )
    
    result = validate_ticket(ticket)
    assert result.status == TicketValidationStatus.CLARIFICATION_REQUIRED
    assert result.missing_fields == ["description","acceptance_criteria"]
    assert len(result.reasons) == 2


def test_missing_key_raises_error():
    ticket = JiraTicket(
        key="",
        title="Valid title",
        description="Valid description",
        priority="Low",
        acceptance_criteria=["Valid criterion"],
        issue_type="Task",
        status="To Do",
        labels=[],
    )

    with pytest.raises(ValueError):
        validate_ticket(ticket)