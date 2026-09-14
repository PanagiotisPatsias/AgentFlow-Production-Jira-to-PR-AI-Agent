from agentflow.domain.implementation_plan import ImplementationPlan, Planstep
from agentflow.domain.patch_proposal import (
    FileChange,
    FileOperation,
    PatchProposal,
)
from agentflow.tools.git.repair_patch_validator import RepairPatchValidator


def test_repair_treats_initially_created_existing_file_as_modified(
    tmp_path,
) -> None:
    test_path = "Intellishore/tests/test_data_validation.py"
    existing_file = tmp_path / test_path
    existing_file.parent.mkdir(parents=True)
    existing_file.write_text("old content\n", encoding="utf-8")

    plan = ImplementationPlan(
        summary="Add validation",
        steps=[
            Planstep(
                order=1,
                description="Add tests",
                files=[test_path],
                acceptance_criteria_ids=[1],
            )
        ],
        files_to_modify=[],
        files_to_create=[test_path],
        tests_to_add=[test_path],
        risks=[],
        assumptions=[],
    )
    patch = PatchProposal(
        summary="Repair tests",
        acceptance_criteria_ids=[1],
        file_changes=[
            FileChange(
                path=test_path,
                operation=FileOperation.CREATE,
                content="new content\n",
            )
        ],
        notes=[],
    )

    normalized = RepairPatchValidator._normalize_repair_operations(
        patch,
        plan,
        tmp_path,
    )

    assert normalized.file_changes[0].operation == FileOperation.MODIFY
    assert patch.file_changes[0].operation == FileOperation.CREATE
