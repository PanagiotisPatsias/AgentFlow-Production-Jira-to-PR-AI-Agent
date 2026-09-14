import subprocess

from agentflow.tools.repository.context import RepositoryContextBuilder


def test_repair_context_contains_current_and_original_file(tmp_path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
    )

    app_file = tmp_path / "Intellishore/app.py"
    app_file.parent.mkdir()
    app_file.write_text("original behavior\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    app_file.write_text("current validation\n", encoding="utf-8")

    context = RepositoryContextBuilder().build_repair_context(
        str(tmp_path),
        ["Intellishore/app.py"],
    )

    assert "## Current complete file: Intellishore/app.py" in context
    assert "current validation" in context
    assert "## Original Git HEAD file: Intellishore/app.py" in context
    assert "original behavior" in context
