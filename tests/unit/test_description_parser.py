from agentflow.integrations.jira.description_parser import parse_ticket_description

def test_description_parser():
    text = """
            Implement account lockout.

            Acceptance Criteria:
            - Lock after five failures.
            - Add unit tests.
            """
     
    description_original, acceptance_criteria_original = parse_ticket_description(text)
    description = "Implement account lockout."
    acceptance_criteria = [
        "Lock after five failures.",
        "Add unit tests.",
    ]

    assert description == description_original
    assert acceptance_criteria == acceptance_criteria_original
