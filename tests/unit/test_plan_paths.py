from agentflow.domain.implementation_plan import ImplementationPlan, Planstep
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
