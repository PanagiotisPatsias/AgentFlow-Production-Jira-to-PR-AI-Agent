from unittest.mock import patch

from agentflow.integrations.github.client import GitHubClient


class FakeResponse:
    status_code = 201

    @staticmethod
    def json() -> dict:
        return {
            "number": 42,
            "html_url": "https://github.com/owner/repository/pull/42",
            "title": "SCRUM-1: Implement feature",
            "draft": True,
        }


def test_create_draft_pull_request_sends_github_payload() -> None:
    client = GitHubClient(
        token="test-token",
        base_url="https://api.github.com",
    )

    with patch(
        "agentflow.integrations.github.client.requests.post",
        return_value=FakeResponse(),
    ) as post:
        result = client.create_draft_pull_request(
            repository_url="https://github.com/owner/repository",
            head_branch="agentflow/scrum-1",
            base_branch="main",
            title="SCRUM-1: Implement feature",
            body="PR body",
        )

    post.assert_called_once_with(
        "https://api.github.com/repos/owner/repository/pulls",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer test-token",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        json={
            "title": "SCRUM-1: Implement feature",
            "body": "PR body",
            "head": "agentflow/scrum-1",
            "base": "main",
            "draft": True,
        },
        timeout=30.0,
    )
    assert result.number == 42
    assert result.draft is True
