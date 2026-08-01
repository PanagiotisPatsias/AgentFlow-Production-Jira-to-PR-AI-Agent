import difflib
from pathlib import Path

from agentflow.domain.patch_proposal import (
    FileOperation,
    PatchProposal,
)


class PatchCompilationError(ValueError):
    pass


class StructuredPatchCompiler:
    """Compile structured file contents into a Git-compatible diff."""

    def compile(
        self,
        workspace_path: str,
        patch: PatchProposal,
    ) -> str:
        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise PatchCompilationError(
                f"Workspace does not exist: {workspace_path}"
            )

        if not patch.file_changes:
            raise PatchCompilationError(
                "Patch does not contain structured file changes"
            )

        sections: list[str] = []
        seen_paths: set[str] = set()

        for change in patch.file_changes:
            relative_path = Path(change.path)

            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise PatchCompilationError(
                    f"Unsafe structured file path: {change.path}"
                )

            if change.path in seen_paths:
                raise PatchCompilationError(
                    f"Duplicate structured file change: {change.path}"
                )
            seen_paths.add(change.path)

            candidate = (repo_path / relative_path).resolve()
            try:
                candidate.relative_to(repo_path)
            except ValueError as exc:
                raise PatchCompilationError(
                    f"Structured file path escapes workspace: {change.path}"
                ) from exc

            if change.operation == FileOperation.MODIFY:
                if not candidate.is_file():
                    raise PatchCompilationError(
                        f"Modified file does not exist: {change.path}"
                    )
                # Preserve CRLF/LF exactly. Path.read_text() performs
                # universal-newline conversion, which makes Git context
                # lines differ from repositories that store CRLF files.
                with candidate.open(
                    "r",
                    encoding="utf-8",
                    errors="strict",
                    newline="",
                ) as source_file:
                    old_content = source_file.read()
                from_file = f"a/{change.path}"
            else:
                if candidate.exists():
                    raise PatchCompilationError(
                        f"Created file already exists: {change.path}"
                    )
                old_content = ""
                from_file = "/dev/null"

            old_lines = old_content.splitlines(keepends=True)
            new_content = change.content
            if new_content and not new_content.endswith("\n"):
                new_content += "\n"
            new_lines = new_content.splitlines(keepends=True)

            body = "".join(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=from_file,
                    tofile=f"b/{change.path}",
                    lineterm="\n",
                )
            )

            if not body:
                continue

            header = f"diff --git a/{change.path} b/{change.path}\n"
            if change.operation == FileOperation.CREATE:
                header += "new file mode 100644\n"
            sections.append(header + body)

        return "".join(sections)
