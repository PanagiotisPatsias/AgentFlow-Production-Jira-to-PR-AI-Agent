from agentflow.integrations.jira.mapper import (
    map_jira_issue_to_ticket,
)


def test_map_jira_issue_to_ticket():
    raw_issue = {
        "key": "SCRUM-1",
        "fields": {
            "summary": "Add account lockout",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "codeBlock",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Implement account lockout.\n\n"
                                    "Acceptance Criteria:\n"
                                    "- Lock after five failures.\n"
                                    "- Add unit tests."
                                ),
                            }
                        ],
                    }
                ],
            },
            "priority": {"name": "High"},
            "issuetype": {"name": "Task"},
            "status": {"name": "To Do"},
            "labels": ["authentication", "security"],
        },
    }

    ticket = map_jira_issue_to_ticket(raw_issue)

    assert ticket.key == "SCRUM-1"
    assert ticket.title == "Add account lockout"
    assert ticket.description == "Implement account lockout."
    assert ticket.priority == "High"
    assert ticket.acceptance_criteria == [
        "Lock after five failures.",
        "Add unit tests.",
    ]
    assert ticket.issue_type == "Task"
    assert ticket.status == "To Do"
    assert ticket.labels == ["authentication", "security"]