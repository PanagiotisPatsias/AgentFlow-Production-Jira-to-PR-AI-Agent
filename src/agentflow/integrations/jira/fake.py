from agentflow.domain.jira_ticket import JiraTicket

class FakeJiraClient():
    def __init__(self, ticket: dict[str, JiraTicket]):
        self._ticket = ticket

    def get_ticket(self, ticket_key:str) -> JiraTicket:
        if ticket_key not in self._ticket:
            raise KeyError(f"Jira ticket not found: {ticket_key}")


        return self._ticket[ticket_key]