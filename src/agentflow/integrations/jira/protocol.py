from typing import Protocol
from agentflow.domain.jira_ticket import JiraTicket


class JiraClientProtocol(Protocol):
    def get_ticket(self, ticket:str) -> JiraTicket :
        ...