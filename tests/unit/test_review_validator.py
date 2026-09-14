from agentflow.domain.code_review import (
    CodeReviewResult,
    FindingSeverity,
    ReviewDecision,
    ReviewFinding,
    ReviewValidationStatus,
)
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.tools.review.validator import ReviewValidator


def _ticket() -> JiraTicket:
    return JiraTicket(
        key="SCRUM-1",
        title="Validate data",
        description="Validate inputs",
        priority="Medium",
        acceptance_criteria=["Validation works"],
        issue_type="Task",
        status="To Do",
        labels=[],
    )


def _review(file_path: str) -> CodeReviewResult:
    return CodeReviewResult(
        decision=ReviewDecision.CHANGES_REQUESTED,
        summary="A concrete change is required",
        findings=[
            ReviewFinding(
                severity=FindingSeverity.HIGH,
                title="Validation issue",
                description="The application path needs correction",
                file_path=file_path,
                recommendation="Correct the application path",
            )
        ],
        acceptance_criteria_covered=[1],
        risks=[],
    )


def test_normalizes_unique_nested_review_path(tmp_path) -> None:
    app_file = tmp_path / "Intellishore/app.py"
    app_file.parent.mkdir()
    app_file.write_text("print('app')\n", encoding="utf-8")
    review = _review("app.py")

    result = ReviewValidator().validate(review, _ticket(), str(tmp_path))

    assert result.status == ReviewValidationStatus.VALID
    assert review.findings[0].file_path == "Intellishore/app.py"


def test_rejects_ambiguous_nested_review_path(tmp_path) -> None:
    for directory in ("one", "two"):
        app_file = tmp_path / directory / "app.py"
        app_file.parent.mkdir()
        app_file.write_text("print('app')\n", encoding="utf-8")

    result = ReviewValidator().validate(
        _review("app.py"),
        _ticket(),
        str(tmp_path),
    )

    assert result.status == ReviewValidationStatus.INVALID
    assert any("ambiguous" in error for error in result.errors)
