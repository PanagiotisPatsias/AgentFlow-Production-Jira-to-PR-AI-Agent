from agentflow.domain.pull_request import PullRequestResult
import requests


class GitHubClient:
    def __init__(self, token, base_url: str, timeout: int):
        self.token = token

        self.base_url = base_url
        self.timeout = timeout

    def create_draft_pull_request(self,repository_url: str,head_branch: str,base_branch: str,title: str,body: str) -> PullRequestResult:

        owner, project = self.parse_github_repository_url(repository_url)

        # base_url = "https://api.github.com/repos/"
        url = f"{self.base_url}/{owner}/{project}/pulls"

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
            url=url,
            headers=headers,
            body=body_request,
            timeout= self.timeout
        )

        data = response.json()

        if response.status_code == 403:
            raise ValueError

        elif response.status_code == 422:
            raise ValueError

        return PullRequestResult(
            number = data["number"] ,
            url = data["html_url"],
            title = data["title"],
            draft = data["draft"],

        )



    @staticmethod
    def parse_github_repository_url(
        repository_url: str,
    ) -> tuple[str, str]:

        owner = repository_url.split("/")[3]
        project = repository_url.split("/")[4]

        return owner, project
