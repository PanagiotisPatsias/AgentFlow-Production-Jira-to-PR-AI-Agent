import subprocess

from agentflow.domain.patch_proposal import (
    FileChange,
    FileOperation,
    PatchProposal,
)
from agentflow.tools.git.patch_compiler import StructuredPatchCompiler


def test_compiles_structured_changes_into_applicable_git_diff(
    tmp_path,
) -> None:
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    existing_file = tmp_path / "service.py"
    existing_file.write_text("value = 1\n", encoding="utf-8")

    patch = PatchProposal(
        summary="Update service and add tests",
        modified_files=["service.py"],
        created_files=["tests/test_service.py"],
        tests_changed=["tests/test_service.py"],
        acceptance_criteria_ids=[1],
        file_changes=[
            FileChange(
                path="service.py",
                operation=FileOperation.MODIFY,
                content="value = 2\n",
            ),
            FileChange(
                path="tests/test_service.py",
                operation=FileOperation.CREATE,
                content="def test_value():\n    assert True\n",
            ),
        ],
        unified_diff="",
        notes=[],
    )

    unified_diff = StructuredPatchCompiler().compile(
        str(tmp_path),
        patch,
    )

    result = subprocess.run(
        ["git", "-C", str(tmp_path), "apply", "--check", "--recount", "-"],
        input=unified_diff,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "diff --git a/service.py b/service.py" in unified_diff
    assert "diff --git a/tests/test_service.py b/tests/test_service.py" in unified_diff


def test_compiled_diff_applies_to_existing_crlf_file(tmp_path) -> None:
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    existing_file = tmp_path / "package" / "__init__.py"
    existing_file.parent.mkdir()
    existing_file.write_bytes(b'"""Package."""\r\n\r\nVALUE = 1\r\n')

    patch = PatchProposal(
        summary="Export the service",
        modified_files=["package/__init__.py"],
        created_files=[],
        tests_changed=["package/__init__.py"],
        acceptance_criteria_ids=[1],
        file_changes=[
            FileChange(
                path="package/__init__.py",
                operation=FileOperation.MODIFY,
                content='"""Package."""\n\nVALUE = 1\nSERVICE = "ready"\n',
            ),
        ],
        unified_diff="",
        notes=[],
    )

    unified_diff = StructuredPatchCompiler().compile(
        str(tmp_path),
        patch,
    )
    result = subprocess.run(
        ["git", "-C", str(tmp_path), "apply", "--check", "--recount", "-"],
        input=unified_diff,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
