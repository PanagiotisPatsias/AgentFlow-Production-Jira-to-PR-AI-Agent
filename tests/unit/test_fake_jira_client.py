from agentflow.domain.jira_ticket import JiraTicket
from agentflow.integrations.jira.fake import FakeJiraClient

def test_fake_jira_client():

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

    client = FakeJiraClient({ticket.key:ticket})
    

    assert ticket == client.get_ticket(ticket.key)