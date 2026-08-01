import subprocess
from pathlib import Path


class PatchApplicationError(RuntimeError):
    pass


class PatchApplier:
    TIMEOUT_SECONDS = 30

    def apply(
        self,
        workspace_path: str,
        unified_diff: str,
    ) -> None:
        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise PatchApplicationError(
                f"Workspace does not exist: {workspace_path}"
            )

        if not (repo_path / ".git").exists():
            raise PatchApplicationError(
                f"Workspace is not a Git repository: "
                f"{workspace_path}"
            )

        if not unified_diff.strip():
            raise PatchApplicationError(
                "Cannot apply an empty unified diff"
            )

        # Confirm that the patch can be applied.
        self._run_git_apply(
            repo_path=repo_path,
            unified_diff=unified_diff,
            arguments=["--check", "--recount"],
        )

        # Apply the patch to the local workspace.
        self._run_git_apply(
            repo_path=repo_path,
            unified_diff=unified_diff,
            arguments=["--recount"],
        )

        # Check the resulting Git diff for whitespace errors.
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "diff",
                    "--check",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as exc:
            # Attempt to restore the workspace if post-apply
            # validation fails.
            rollback_error = self._rollback_patch(
                repo_path=repo_path,
                unified_diff=unified_diff,
            )

            error_message = self._error_message(exc)

            if rollback_error:
                error_message += (
                    f" Rollback also failed: {rollback_error}"
                )

            raise PatchApplicationError(
                f"Applied patch failed Git diff validation: "
                f"{error_message}"
            ) from exc

    def _run_git_apply(
        self,
        repo_path: Path,
        unified_diff: str,
        arguments: list[str],
    ) -> None:
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "apply",
                    *arguments,
                    "-",
                ],
                input=unified_diff,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as exc:
            raise PatchApplicationError(
                f"Git could not apply the patch: "
                f"{self._error_message(exc)}"
            ) from exc

    def _rollback_patch(
        self,
        repo_path: Path,
        unified_diff: str,
    ) -> str | None:
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "apply",
                    "--reverse",
                    "--recount",
                    "-",
                ],
                input=unified_diff,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as exc:
            return self._error_message(exc)

        return None

    @staticmethod
    def _error_message(
        exc: subprocess.CalledProcessError
        | subprocess.TimeoutExpired,
    ) -> str:
        if isinstance(exc, subprocess.TimeoutExpired):
            return "Git command timed out"

        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()

        return (stderr or stdout or "Unknown Git error")[:1000]
