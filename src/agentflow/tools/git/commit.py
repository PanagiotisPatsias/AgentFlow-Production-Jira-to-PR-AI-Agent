import subprocess
from pathlib import Path


class GitCommitError(RuntimeError):
    """Raised when validated workspace changes cannot be committed."""


class GitCommitManager:
    def commit(
        self,
        workspace_path: str,
        expected_branch: str,
        allowed_files: set[str],
        commit_message: str,
    ) -> str:
        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise ValueError(
                f"Workspace does not exist: {workspace_path}"
            )

        if not (repo_path / ".git").is_dir():
            raise ValueError(
                f"Workspace is not a Git repository: {workspace_path}"
            )

        current_branch = self._run_git(
            repo_path,
            ["branch", "--show-current"],
        ).stdout.strip()

        if current_branch != expected_branch:
            raise GitCommitError(
                "Refusing to commit on an unexpected branch: "
                f"expected {expected_branch}, found {current_branch}"
            )

        changed_files = self.get_changed_files(repo_path)

        if not changed_files:
            raise GitCommitError("There are no workspace changes to commit")

        unexpected_files = changed_files - allowed_files

        if unexpected_files:
            raise GitCommitError(
                "Workspace contains changes outside the approved plan: "
                f"{sorted(unexpected_files)}"
            )

        self._run_git(
            repo_path,
            ["add", "--", *sorted(changed_files)],
        )
        self._run_git(repo_path, ["diff", "--cached", "--check"])

        normalized_message = " ".join(commit_message.split())[:120]

        if not normalized_message:
            raise ValueError("Commit message is required")

        self._run_git(
            repo_path,
            [
                "-c",
                "user.name=AgentFlow",
                "-c",
                "user.email=agentflow@localhost",
                "commit",
                "--message",
                normalized_message,
            ],
        )

        return self._run_git(
            repo_path,
            ["rev-parse", "HEAD"],
        ).stdout.strip()

    def get_changed_files(self, repo_path: Path) -> set[str]:
        result = self._run_git(
            repo_path,
            [
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ],
        )

        changed_files: set[str] = set()

        for entry in result.stdout.split("\0"):
            if not entry:
                continue

            if len(entry) < 4:
                raise GitCommitError(
                    f"Unexpected Git status entry: {entry!r}"
                )

            status = entry[:2]

            if "R" in status or "C" in status:
                raise GitCommitError(
                    "Renamed or copied files are not supported by the "
                    "commit policy"
                )

            changed_files.add(entry[3:])

        return changed_files

    @staticmethod
    def _run_git(
        repo_path: Path,
        arguments: list[str],
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", "-C", str(repo_path), *arguments],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitCommitError(
                f"Git command timed out: {' '.join(arguments)}"
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = (
                exc.stderr.strip()
                or exc.stdout.strip()
                or "Unknown Git error"
            )
            raise GitCommitError(
                f"Git command failed: {detail[:1000]}"
            ) from exc
