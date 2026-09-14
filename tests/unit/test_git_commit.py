import subprocess

from agentflow.tools.git.commit import GitCommitManager


def test_commit_accepts_crlf_python_file(tmp_path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "checkout", "-b", "agentflow/test-1"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    source = tmp_path / "service.py"
    source.write_bytes(b"value = 1\r\n")
    subprocess.run(["git", "add", "service.py"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "initial",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    source.write_bytes(b"value = 2\r\n")

    commit_sha = GitCommitManager().commit(
        workspace_path=str(tmp_path),
        expected_branch="agentflow/test-1",
        allowed_files={"service.py"},
        commit_message="TEST-1: update service",
    )

    assert len(commit_sha) == 40
    assert subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout == ""
