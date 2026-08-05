from agentflow.domain.jira_ticket import JiraTicket
import requests
from requests.auth import HTTPBasicAuth
from agentflow.core.config import Setting
from agentflow.integrations.jira.mapper import map_jira_issue_to_ticket
from agentflow.integrations.jira.exceptions import JiraAuthenticationError, JiraPermissionError,JiraError,JiraRateLimitError,JiraTemporaryError,JiraTicketNotFoundError

class JiraClient:

    def __init__(self, settings: Setting):
        self.settings = settings

    def _handle_response_errors(self,response: requests.Response) -> None:
        status_code = response.status_code

        if status_code == 401:
            raise JiraAuthenticationError(
                "Jira authentication failed."
            )

        if status_code == 403:
            raise JiraPermissionError(
                "The authenticated user does not have permission."
            )

        if status_code == 404:
            raise JiraTicketNotFoundError(
                "The Jira ticket does not exist or is not accessible."
            )

        if status_code == 429:
            raise JiraRateLimitError(
                "Jira rate limit exceeded."
            )

        if 500 <= status_code < 600:
            raise JiraTemporaryError(
                f"Jira is temporarily unavailable. Status: {status_code}"
            )

    def get_ticket(self, ticket_key: str) -> JiraTicket:
        base_url = f"https://api.atlassian.com/ex/jira/{self.settings.JIRA_CLOUD_ID}"
        url = f"{base_url}/rest/api/3/issue/{ticket_key}"
        auth = HTTPBasicAuth(self.settings.JIRA_EMAIL, self.settings.JIRA_API_TOKEN.get_secret_value())
        headers = {"Accept": "application/json"}

        response = requests.get(url, headers=headers, auth=auth, timeout=10)
        self._handle_response_errors(response)
        response.raise_for_status()

        data = response.json()
        ticket = map_jira_issue_to_ticket(data)

        return ticket

    def push_ticket(self, ticket_key: str, comment_text:str):

        base_url = f"https://api.atlassian.com/ex/jira/{self.settings.JIRA_CLOUD_ID}"
        url = f"{base_url}/rest/api/3/issue/{ticket_key}/comment"
        auth = HTTPBasicAuth(self.settings.JIRA_EMAIL, self.settings.JIRA_API_TOKEN.get_secret_value())
        headers = {"Accept": "application/json"}


        data = {
    "body": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": comment_text,
                    }
                ],
            }
        ],
    }
}

        response = requests.post(url, json=data,  headers=headers, auth=auth, timeout=10)

        data = response.json()