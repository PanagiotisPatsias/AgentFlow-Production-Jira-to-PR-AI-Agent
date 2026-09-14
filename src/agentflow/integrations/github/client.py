from agentflow.domain.pull_request import PullRequestResult
import requests


class GitHubPullRequestError(RuntimeError):
    """Raised when GitHub does not create the requested pull request."""


class GitHubClient:
    def __init__(self, token, base_url: str, timeout: float = 30.0):
        self.token = token

        self.base_url = base_url
        self.timeout = timeout

    def create_draft_pull_request(self,repository_url: str,head_branch: str,base_branch: str,title: str,body: str) -> PullRequestResult:

        owner, project = self.parse_github_repository_url(repository_url)

        url = (
            f"{self.base_url.rstrip('/')}"
            f"/repos/{owner}/{project}/pulls"
        )

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

        body_request = {
                        "title": title,
                        "body": body,
                        "head": head_branch,
                        "base": base_branch,
                        "draft": True,
                        }

        response = requests.post(
            url,
            headers=headers,
            json=body_request,
            timeout= self.timeout
        )

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise GitHubPullRequestError(
                "GitHub returned a non-JSON response while creating the "
                f"pull request. Status: {response.status_code}"
            ) from exc

        if response.status_code != 201:
            message = data.get("message", "Unknown GitHub API error")
            errors = data.get("errors")
            detail = f" Details: {errors}" if errors else ""
            raise GitHubPullRequestError(
                "GitHub pull request creation failed with status "
                f"{response.status_code}: {message}.{detail}"
            )

        return PullRequestResult(
            number=data["number"],
            url=data["html_url"],
            title=data["title"],
            draft=data["draft"],

        )



    @staticmethod
    def parse_github_repository_url(
        repository_url: str,
    ) -> tuple[str, str]:

        owner = repository_url.split("/")[3]
        project = repository_url.split("/")[4]

        return owner, project
