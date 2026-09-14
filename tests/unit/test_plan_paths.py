from agentflow.domain.implementation_plan import ImplementationPlan, Planstep
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.plan_validation import (
    PlanValidationStatus,
    validate_implementation_plan,
)
from agentflow.tools.repository.plan_paths import PlanPathNormalizer


def test_normalizes_nested_project_paths_to_repository_paths(tmp_path) -> None:
    project = tmp_path / "Intellishore"
    (project / "tests").mkdir(parents=True)
    (project / "app.py").write_text("print('app')\n", encoding="utf-8")

    plan = ImplementationPlan(
        summary="Implement feature",
        steps=[
            Planstep(
                order=1,
                description="Update app and add tests",
                files=["app.py", "tests/test_authentication.py"],
                acceptance_criteria_ids=[1],
            )
        ],
        files_to_modify=["app.py"],
        files_to_create=["tests/test_authentication.py"],
        tests_to_add=["tests/test_authentication.py"],
        risks=[],
        assumptions=[],
    )

    normalized = PlanPathNormalizer().normalize(plan, str(tmp_path))

    assert normalized.files_to_modify == ["Intellishore/app.py"]
    assert normalized.files_to_create == [
        "Intellishore/tests/test_authentication.py"
    ]
    assert normalized.steps[0].files == [
        "Intellishore/app.py",
        "Intellishore/tests/test_authentication.py",
    ]


def _nested_project_plan(test_path: str) -> ImplementationPlan:
    return ImplementationPlan(
        summary="Implement validation",
        steps=[
            Planstep(
                order=1,
                description="Update app and add tests",
                files=["Intellishore/app.py", test_path],
                acceptance_criteria_ids=[1],
            )
        ],
        files_to_modify=["Intellishore/app.py"],
        files_to_create=[test_path],
        tests_to_add=[test_path],
        risks=[],
        assumptions=[],
    )


def _ticket() -> JiraTicket:
    return JiraTicket(
        key="SCRUM-1",
        title="Add validation",
        description="Validate inputs",
        priority="Medium",
        acceptance_criteria=["Add validation tests"],
        issue_type="Task",
        status="To Do",
        labels=[],
    )


def test_rejects_new_file_that_drops_nested_project_prefix(tmp_path) -> None:
    project = tmp_path / "Intellishore"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (project / "app.py").write_text("print('app')\n", encoding="utf-8")

    result = validate_implementation_plan(
        _nested_project_plan("tests/test_data_validation.py"),
        _ticket(),
        str(tmp_path),
    )

    assert result.status == PlanValidationStatus.INVALID
    assert any("Intellishore/" in error for error in result.errors)


def test_accepts_new_file_with_nested_project_prefix(tmp_path) -> None:
    project = tmp_path / "Intellishore"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (project / "app.py").write_text("print('app')\n", encoding="utf-8")

    result = validate_implementation_plan(
        _nested_project_plan("Intellishore/tests/test_data_validation.py"),
        _ticket(),
        str(tmp_path),
    )

    assert result.status == PlanValidationStatus.VALID
