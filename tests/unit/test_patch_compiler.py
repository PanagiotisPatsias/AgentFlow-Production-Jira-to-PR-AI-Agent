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

    apply_result = subprocess.run(
        ["git", "-C", str(tmp_path), "apply", "--recount", "-"],
        input=unified_diff,
        check=False,
        capture_output=True,
        text=True,
    )
    assert apply_result.returncode == 0, apply_result.stderr

    whitespace_result = subprocess.run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "-C",
            str(tmp_path),
            "diff",
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert whitespace_result.returncode == 0, whitespace_result.stderr
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

    apply_result = subprocess.run(
        ["git", "-C", str(tmp_path), "apply", "--recount", "-"],
        input=unified_diff,
        check=False,
        capture_output=True,
        text=True,
    )
    assert apply_result.returncode == 0, apply_result.stderr

    whitespace_result = subprocess.run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "-C",
            str(tmp_path),
            "diff",
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert whitespace_result.returncode == 0, whitespace_result.stderr


def test_python_content_preserves_crlf_and_removes_trailing_spaces(
    tmp_path,
) -> None:
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    source = tmp_path / "service.py"
    source.write_bytes(b"def old():\r\n    return 1\r\n")

    patch = PatchProposal(
        summary="Update service",
        acceptance_criteria_ids=[1],
        file_changes=[
            FileChange(
                path="service.py",
                operation=FileOperation.MODIFY,
                content="def updated():   \n    return 2\t\n",
            )
        ],
        unified_diff="",
        notes=[],
    )

    unified_diff = StructuredPatchCompiler().compile(
        str(tmp_path),
        patch,
    )
    result = subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "apply",
            "--check",
            "--recount",
            "--whitespace=error-all",
            "-",
        ],
        input=unified_diff,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "+def updated():   " not in unified_diff
    assert "+    return 2\t" not in unified_diff
