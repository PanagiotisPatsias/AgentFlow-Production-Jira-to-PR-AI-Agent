import os
import subprocess
import tempfile
from pathlib import Path


class GitPushError(RuntimeError):
    """Raised when a validated branch cannot be pushed safely."""


class GitPushManager:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GitHub token is required")

        self._token = token

    def push(
        self,
        workspace_path: str,
        branch_name: str,
        expected_commit_sha: str,
        expected_repository_url: str,
    ) -> None:
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

        if current_branch != branch_name:
            raise GitPushError(
                "Refusing to push an unexpected branch: "
                f"expected {branch_name}, found {current_branch}"
            )

        current_commit_sha = self._run_git(
            repo_path,
            ["rev-parse", "HEAD"],
        ).stdout.strip()

        if current_commit_sha != expected_commit_sha:
            raise GitPushError(
                "Refusing to push an unexpected commit: "
                f"expected {expected_commit_sha}, "
                f"found {current_commit_sha}"
            )

        origin_url = self._run_git(
            repo_path,
            ["remote", "get-url", "origin"],
        ).stdout.strip()

        if self._normalize_repository_url(origin_url) != (
            self._normalize_repository_url(expected_repository_url)
        ):
            raise GitPushError(
                "Origin remote does not match the requested repository"
            )

        if not origin_url.startswith("https://github.com/"):
            raise GitPushError(
                "Token-authenticated push requires an HTTPS GitHub origin"
            )

        self._push_with_token(repo_path, branch_name)

    def _push_with_token(
        self,
        repo_path: Path,
        branch_name: str,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="agentflow-git-auth-"
        ) as temporary_directory:
            askpass_path = Path(temporary_directory) / "askpass.sh"
            askpass_path.write_text(
                """#!/bin/sh
case "$1" in
  *Username*) printf '%s\\n' 'x-access-token' ;;
  *Password*) printf '%s\\n' "$AGENTFLOW_GITHUB_TOKEN" ;;
  *) exit 1 ;;
esac
""",
                encoding="utf-8",
            )
            askpass_path.chmod(0o700)

            environment = os.environ.copy()
            environment.update(
                {
                    "GIT_ASKPASS": str(askpass_path),
                    "GIT_TERMINAL_PROMPT": "0",
                    "AGENTFLOW_GITHUB_TOKEN": self._token,
                }
            )

            try:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo_path),
                        "push",
                        "--set-upstream",
                        "origin",
                        branch_name,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=environment,
                )
            except subprocess.TimeoutExpired as exc:
                raise GitPushError("Git push timed out") from exc
            except subprocess.CalledProcessError as exc:
                detail = (
                    exc.stderr.strip()
                    or exc.stdout.strip()
                    or "Unknown Git push error"
                )
                raise GitPushError(
                    f"Git push failed: {detail[:1000]}"
                ) from exc

    @staticmethod
    def _normalize_repository_url(repository_url: str) -> str:
        return repository_url.rstrip("/").removesuffix(".git")

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
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitPushError(
                f"Git command timed out: {' '.join(arguments)}"
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = (
                exc.stderr.strip()
                or exc.stdout.strip()
                or "Unknown Git error"
            )
            raise GitPushError(
                f"Git command failed: {detail[:1000]}"
            ) from exc
