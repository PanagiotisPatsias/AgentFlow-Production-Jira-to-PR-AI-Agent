import shlex
import subprocess
from pathlib import Path

from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.patch_proposal import FileOperation, PatchProposal
from agentflow.domain.patch_validation import (
    PatchValidationResult,
    PatchValidationStatus,
)
from agentflow.tools.git.patch_compiler import (
    PatchCompilationError,
    StructuredPatchCompiler,
)


class PatchValidator:
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

        if not (repo_path / ".git").exists():
            raise ValueError(
                f"Workspace is not a Git repository: {workspace_path}"
            )

        if not patch.summary.strip():
            errors.append("Patch summary is missing")

        if not patch.file_changes:
            errors.append(
                "Patch must contain structured file_changes; "
                "LLM-generated unified diffs are not accepted"
            )
            patch.unified_diff = ""
        else:
            structured_files = {change.path for change in patch.file_changes}
            declared_files = set(patch.modified_files) | set(patch.created_files)
            if structured_files != declared_files:
                errors.append(
                    "Structured file changes do not match declared files: "
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
                    errors.append(f"Cannot compile structured patch: {exc}")

        modified_files = set(patch.modified_files)
        created_files = set(patch.created_files)
        changed_files = modified_files | created_files

        for change in patch.file_changes:
            if (
                change.operation == FileOperation.MODIFY
                and change.path not in modified_files
            ):
                errors.append(
                    "Structured modify operation is not declared in "
                    f"modified_files: {change.path}"
                )
            if (
                change.operation == FileOperation.CREATE
                and change.path not in created_files
            ):
                errors.append(
                    "Structured create operation is not declared in "
                    f"created_files: {change.path}"
                )

        planned_modified_files = set(plan.files_to_modify)
        planned_created_files = set(plan.files_to_create)

        duplicated_files = modified_files & created_files

        if duplicated_files:
            errors.append(
                "Files cannot be both modified and created: "
                f"{sorted(duplicated_files)}"
            )

        # Compare patch files with the approved plan.
        for file_path in modified_files:
            if file_path not in planned_modified_files:
                errors.append(
                    "Patch modifies a file not approved by the plan: "
                    f"{file_path}"
                )

        for file_path in planned_modified_files:
            if file_path not in modified_files:
                warnings.append(
                    "Planned file was not modified by the patch: "
                    f"{file_path}"
                )

        for file_path in created_files:
            if file_path not in planned_created_files:
                errors.append(
                    "Patch creates a file not approved by the plan: "
                    f"{file_path}"
                )

        for file_path in planned_created_files:
            if file_path not in created_files:
                warnings.append(
                    "File planned for creation was not created by "
                    f"the patch: {file_path}"
                )

        # Resolve a path and ensure it remains inside the workspace.
        def resolve_patch_path(file_path: str) -> Path | None:
            path = Path(file_path)

            if path.is_absolute():
                errors.append(
                    f"Patch contains an absolute path: {file_path}"
                )
                return None

            if ".." in path.parts:
                errors.append(
                    f"Patch contains an unsafe path: {file_path}"
                )
                return None

            candidate = (repo_path / path).resolve()

            try:
                candidate.relative_to(repo_path)
            except ValueError:
                errors.append(
                    f"Patch path escapes the workspace: {file_path}"
                )
                return None

            return candidate

        # Modified files must already exist.
        for file_path in modified_files:
            candidate = resolve_patch_path(file_path)

            if candidate is not None and not candidate.is_file():
                errors.append(
                    f"Modified file does not exist: {file_path}"
                )

        # Created files must not exist yet.
        for file_path in created_files:
            candidate = resolve_patch_path(file_path)

            if candidate is not None and candidate.exists():
                errors.append(
                    f"Created file already exists: {file_path}"
                )

        # Validate test declarations.
        test_files = set(patch.tests_changed)

        if not test_files:
            errors.append("Patch does not include test changes")

        for file_path in test_files:
            resolve_patch_path(file_path)

            if file_path not in changed_files:
                errors.append(
                    "Test file is not declared as modified or created: "
                    f"{file_path}"
                )

        # Validate acceptance-criteria coverage.
        expected_criteria_ids = set(
            range(1, len(ticket.acceptance_criteria) + 1)
        )

        covered_criteria_ids = set(
            patch.acceptance_criteria_ids
        )

        missing_ids = (
            expected_criteria_ids - covered_criteria_ids
        )

        unknown_ids = (
            covered_criteria_ids - expected_criteria_ids
        )

        if missing_ids:
            errors.append(
                "Patch does not cover acceptance criteria IDs: "
                f"{sorted(missing_ids)}"
            )

        if unknown_ids:
            errors.append(
                "Patch references acceptance criteria IDs that do "
                f"not exist in the ticket: {sorted(unknown_ids)}"
            )

        # Validate the unified diff.
        unified_diff = patch.unified_diff.strip()

        if not unified_diff:
            errors.append("Patch does not contain a unified diff")

        if len(patch.unified_diff) > self.MAX_DIFF_CHARS:
            errors.append(
                "Unified diff exceeds the maximum allowed size of "
                f"{self.MAX_DIFF_CHARS} characters"
            )

        if "rename from " in unified_diff:
            errors.append("Patch renames files, which is not allowed")

        if "rename to " in unified_diff:
            errors.append("Patch renames files, which is not allowed")

        if "+++ /dev/null" in unified_diff:
            errors.append("Patch deletes files, which is not allowed")

        if "GIT binary patch" in unified_diff:
            errors.append("Binary patches are not allowed")

        if "Binary files " in unified_diff:
            errors.append("Binary file changes are not allowed")

        # Extract the actual files declared in the diff headers.
        diff_files: set[str] = set()

        if unified_diff:
            for line in unified_diff.splitlines():
                if not line.startswith("diff --git "):
                    continue

                try:
                    parts = shlex.split(line)
                except ValueError:
                    errors.append(
                        f"Invalid Git diff header: {line}"
                    )
                    continue

                if len(parts) != 4:
                    errors.append(
                        f"Invalid Git diff header: {line}"
                    )
                    continue

                new_path = parts[3]

                if not new_path.startswith("b/"):
                    errors.append(
                        f"Invalid path in Git diff header: {new_path}"
                    )
                    continue

                relative_path = new_path[2:]
                diff_files.add(relative_path)
                resolve_patch_path(relative_path)

        if unified_diff and not diff_files:
            errors.append(
                "Unified diff contains no valid Git file headers"
            )

        undeclared_diff_files = diff_files - changed_files
        missing_diff_files = changed_files - diff_files

        if undeclared_diff_files:
            errors.append(
                "Unified diff changes files not declared in the "
                f"PatchProposal: {sorted(undeclared_diff_files)}"
            )

        if missing_diff_files:
            errors.append(
                "PatchProposal declares files that are missing from "
                f"the unified diff: {sorted(missing_diff_files)}"
            )

        # Confirm that Git can apply the patch without modifying files.
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
                errors.append(
                    "Git patch validation timed out"
                )
            except subprocess.CalledProcessError as exc:
                git_error = (
                    exc.stderr.strip()
                    or exc.stdout.strip()
                    or "Unknown Git apply error"
                )

                errors.append(
                    f"Git cannot apply the proposed patch: "
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
