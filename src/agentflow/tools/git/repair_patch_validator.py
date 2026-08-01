import shlex
import subprocess
from pathlib import Path

from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.domain.patch_validation import (
    PatchValidationResult,
    PatchValidationStatus,
)
from agentflow.tools.git.patch_compiler import (
    PatchCompilationError,
    StructuredPatchCompiler,
)


class RepairPatchValidator:
    MAX_DIFF_CHARS = 100_000

    def __init__(self) -> None:
        self._compiler = StructuredPatchCompiler()

    def validate(
        self,
        patch: PatchProposal,
        plan: ImplementationPlan,
        ticket: JiraTicket,
        workspace_path: str,
    ) -> PatchValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise ValueError(
                f"Workspace does not exist: {workspace_path}"
            )

        if not (repo_path / ".git").is_dir():
            raise ValueError(
                f"Workspace is not a Git repository: {workspace_path}"
            )

        if not patch.summary.strip():
            errors.append("Repair patch summary is missing")

        if not patch.file_changes:
            errors.append(
                "Repair patch must contain structured file_changes; "
                "LLM-generated unified diffs are not accepted"
            )
            patch.unified_diff = ""
        else:
            structured_files = {change.path for change in patch.file_changes}
            declared_files = set(patch.modified_files) | set(patch.created_files)
            if structured_files != declared_files:
                errors.append(
                    "Structured repair changes do not match declared files: "
                    f"declared={sorted(declared_files)}, "
                    f"structured={sorted(structured_files)}"
                )
            if structured_files == declared_files:
                try:
                    patch.unified_diff = self._compiler.compile(
                        workspace_path,
                        patch,
                    )
                except (PatchCompilationError, OSError, UnicodeError) as exc:
                    errors.append(
                        f"Cannot compile structured repair patch: {exc}"
                    )

        modified_files = set(patch.modified_files)
        created_files = set(patch.created_files)
        declared_files = modified_files | created_files
        allowed_files = (
            set(plan.files_to_modify)
            | set(plan.files_to_create)
        )

        if not declared_files:
            errors.append("Repair patch does not declare any changed files")

        duplicated_files = modified_files & created_files

        if duplicated_files:
            errors.append(
                "Files cannot be both modified and created: "
                f"{sorted(duplicated_files)}"
            )

        unauthorized_files = declared_files - allowed_files

        if unauthorized_files:
            errors.append(
                "Repair patch changes files not approved by the plan: "
                f"{sorted(unauthorized_files)}"
            )

        def resolve_patch_path(file_path: str) -> Path | None:
            path = Path(file_path)

            if path.is_absolute():
                errors.append(
                    f"Repair patch contains an absolute path: {file_path}"
                )
                return None

            if ".." in path.parts:
                errors.append(
                    f"Repair patch contains an unsafe path: {file_path}"
                )
                return None

            candidate = (repo_path / path).resolve()

            try:
                candidate.relative_to(repo_path)
            except ValueError:
                errors.append(
                    f"Repair patch path escapes the workspace: {file_path}"
                )
                return None

            return candidate

        for file_path in modified_files:
            candidate = resolve_patch_path(file_path)

            if candidate is not None and not candidate.is_file():
                errors.append(
                    "Repair patch declares a modified file that does "
                    f"not exist: {file_path}"
                )

        for file_path in created_files:
            candidate = resolve_patch_path(file_path)

            if candidate is not None and candidate.exists():
                errors.append(
                    "Repair patch declares a created file that already "
                    f"exists: {file_path}"
                )

        test_files = set(patch.tests_changed)

        for file_path in test_files:
            resolve_patch_path(file_path)

            if file_path not in declared_files:
                errors.append(
                    "Repair test file is not declared as modified or "
                    f"created: {file_path}"
                )

        if not test_files:
            warnings.append("Repair patch does not modify tests")

        valid_criteria_ids = set(
            range(1, len(ticket.acceptance_criteria) + 1)
        )
        repair_criteria_ids = set(patch.acceptance_criteria_ids)
        unknown_ids = repair_criteria_ids - valid_criteria_ids

        if unknown_ids:
            errors.append(
                "Repair patch references unknown acceptance criteria IDs: "
                f"{sorted(unknown_ids)}"
            )

        if not repair_criteria_ids:
            warnings.append(
                "Repair patch does not reference an acceptance criterion"
            )

        unified_diff = patch.unified_diff.strip()

        if not unified_diff:
            errors.append("Repair patch does not contain a unified diff")

        if len(patch.unified_diff) > self.MAX_DIFF_CHARS:
            errors.append(
                "Repair unified diff exceeds the maximum allowed size of "
                f"{self.MAX_DIFF_CHARS} characters"
            )

        if "rename from " in unified_diff or "rename to " in unified_diff:
            errors.append("Repair patch renames files, which is not allowed")

        if "+++ /dev/null" in unified_diff:
            errors.append("Repair patch deletes files, which is not allowed")

        if (
            "GIT binary patch" in unified_diff
            or "Binary files " in unified_diff
        ):
            errors.append("Binary repair patches are not allowed")

        diff_files: set[str] = set()

        if unified_diff:
            for line in unified_diff.splitlines():
                if not line.startswith("diff --git "):
                    continue

                try:
                    parts = shlex.split(line)
                except ValueError:
                    errors.append(f"Invalid Git diff header: {line}")
                    continue

                if len(parts) != 4:
                    errors.append(f"Invalid Git diff header: {line}")
                    continue

                old_path = parts[2]
                new_path = parts[3]

                if not old_path.startswith("a/"):
                    errors.append(
                        f"Invalid old path in Git diff header: {old_path}"
                    )
                    continue

                if not new_path.startswith("b/"):
                    errors.append(
                        f"Invalid new path in Git diff header: {new_path}"
                    )
                    continue

                old_relative_path = old_path[2:]
                new_relative_path = new_path[2:]

                if old_relative_path != new_relative_path:
                    errors.append(
                        "Repair diff changes a file path, which is not "
                        f"allowed: {old_relative_path} -> {new_relative_path}"
                    )
                    continue

                diff_files.add(new_relative_path)
                resolve_patch_path(new_relative_path)

        if unified_diff and not diff_files:
            errors.append(
                "Repair unified diff contains no valid Git file headers"
            )

        undeclared_diff_files = diff_files - declared_files
        missing_diff_files = declared_files - diff_files

        if undeclared_diff_files:
            errors.append(
                "Repair unified diff changes files not declared in the "
                f"PatchProposal: {sorted(undeclared_diff_files)}"
            )

        if missing_diff_files:
            errors.append(
                "Repair PatchProposal declares files missing from the "
                f"unified diff: {sorted(missing_diff_files)}"
            )

        if unified_diff and not errors:
            try:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo_path),
                        "apply",
                        "--check",
                        "--recount",
                        "-",
                    ],
                    input=patch.unified_diff,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                errors.append("Git repair patch validation timed out")
            except subprocess.CalledProcessError as exc:
                git_error = (
                    exc.stderr.strip()
                    or exc.stdout.strip()
                    or "Unknown Git apply error"
                )
                errors.append(
                    "Git cannot apply the proposed repair patch: "
                    f"{git_error[:1000]}"
                )

        status = (
            PatchValidationStatus.INVALID
            if errors
            else PatchValidationStatus.VALID
        )

        return PatchValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
        )
