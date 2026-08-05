from agentflow.domain.code_review import (
    CodeReviewResult,
    ReviewDecision,
    ReviewValidationResult,
    ReviewValidationStatus,
)
from agentflow.workflows.jira_to_pr.routes import route_code_review
from agentflow.workflows.jira_to_pr.state import JiraToPRState


def make_state(attempts: int) -> JiraToPRState:
    return JiraToPRState(
        ticket_key="SCRUM-1",
        repository_url="https://github.com/owner/repository",
        code_review=CodeReviewResult(
            decision=ReviewDecision.CHANGES_REQUESTED,
            summary="Integration is incomplete",
            findings=[],
            acceptance_criteria_covered=[],
            risks=[],
        ),
        review_validation=ReviewValidationResult(
            status=ReviewValidationStatus.VALID,
            errors=[],
            warnings=[],
        ),
        review_repair_attempts=attempts,
        max_review_repair_attempts=2,
    )


def test_routes_review_changes_to_bounded_repair() -> None:
    assert route_code_review(make_state(0)) == "CHANGES_REQUESTED"
    assert route_code_review(make_state(1)) == "CHANGES_REQUESTED"
    assert (
        route_code_review(make_state(2))
        == "REVIEW_REPAIR_LIMIT_REACHED"
    )
