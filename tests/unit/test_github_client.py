from unittest.mock import Mock, patch

import pytest

from agentflow.integrations.github.client import (
    GitHubClient,
    GitHubPullRequestError,
)


@patch("agentflow.integrations.github.client.requests.post")
def test_reports_github_api_error_instead_of_key_error(post: Mock) -> None:
    response = Mock(status_code=422)
    response.json.return_value = {
        "message": "Validation Failed",
        "errors": [{"message": "A pull request already exists"}],
    }
    post.return_value = response

    with pytest.raises(GitHubPullRequestError) as error:
        GitHubClient("token", "https://api.github.com").create_draft_pull_request(
            repository_url="https://github.com/example/project",
            head_branch="agentflow/test-1",
            base_branch="main",
            title="Test PR",
            body="Test body",
        )

    assert "status 422" in str(error.value)
    assert "Validation Failed" in str(error.value)


@patch("agentflow.integrations.github.client.requests.post")
def test_returns_created_pull_request(post: Mock) -> None:
    response = Mock(status_code=201)
    response.json.return_value = {
        "number": 42,
        "html_url": "https://github.com/example/project/pull/42",
        "title": "Test PR",
        "draft": True,
    }
    post.return_value = response

    result = GitHubClient(
        "token",
        "https://api.github.com",
    ).create_draft_pull_request(
        repository_url="https://github.com/example/project",
        head_branch="agentflow/test-1",
        base_branch="main",
        title="Test PR",
        body="Test body",
    )

    assert result.number == 42
    assert result.draft is True
