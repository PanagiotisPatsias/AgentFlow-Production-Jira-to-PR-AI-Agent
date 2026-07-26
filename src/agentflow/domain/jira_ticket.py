from pydantic import BaseModel


class JiraTicket(BaseModel):
    key: str
    title: str
    description: str
    priority: str
    acceptance_criteria: list[str]
    issue_type: str
    status: str
    labels: list[str]
