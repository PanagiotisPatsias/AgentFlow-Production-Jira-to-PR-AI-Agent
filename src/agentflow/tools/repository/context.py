from pathlib import Path
import subprocess


class RepositoryContextBuilder():

    MAX_FILES = 30
    MAX_CHARS_PER_FILE = 10_000
    MAX_TOTAL_CHARS = 100_000
    MAX_TARGETED_FILE_CHARS = 250_000
    MAX_TARGETED_TOTAL_CHARS = 500_000
    MAX_REPAIR_TOTAL_CHARS = 1_000_000

    def build_repair_context(
        self,
        workspace_path: str,
        file_paths: list[str],
    ) -> str:
        """Return complete current and Git-base contents for approved files."""
        repo_path = Path(workspace_path).resolve()
        if not repo_path.is_dir() or not (repo_path / ".git").is_dir():
            raise ValueError(f"Repository does not exist: {repo_path}")

        context_parts: list[str] = []
        total_chars = 0

        for file_path in dict.fromkeys(file_paths):
            relative_path = Path(file_path)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"Unsafe repair context path: {file_path}")

            absolute_path = (repo_path / relative_path).resolve()
            try:
                absolute_path.relative_to(repo_path)
            except ValueError as exc:
                raise ValueError(
                    f"Repair context path escapes repository: {file_path}"
                ) from exc

            if not absolute_path.is_file():
                raise ValueError(
                    f"Repair context file does not exist: {file_path}"
                )

            current_content = absolute_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            if len(current_content) > self.MAX_TARGETED_FILE_CHARS:
                raise ValueError(f"Repair context file is too large: {file_path}")

            base_result = subprocess.run(
                ["git", "-C", str(repo_path), "show", f"HEAD:{file_path}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            base_content = (
                base_result.stdout if base_result.returncode == 0 else None
            )

            section = (
                f"\n## Current complete file: {relative_path.as_posix()}\n"
                f"```text\n{current_content}\n```\n"
            )
            if base_content is not None:
                section += (
                    f"\n## Original Git HEAD file: "
                    f"{relative_path.as_posix()}\n"
                    f"```text\n{base_content}\n```\n"
                )

            if total_chars + len(section) > self.MAX_REPAIR_TOTAL_CHARS:
                raise ValueError("Repair repository context is too large")

            context_parts.append(section)
            total_chars += len(section)

        return "\n".join(context_parts)

    def build_targeted(
        self,
        workspace_path: str,
        file_paths: list[str],
    ) -> str:
        """Return complete contents for explicitly approved existing files."""
        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise ValueError(f"Repository does not exist: {repo_path}")

        context_parts: list[str] = []
        total_chars = 0

        for file_path in dict.fromkeys(file_paths):
            relative_path = Path(file_path)

            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"Unsafe targeted file path: {file_path}")

            absolute_path = (repo_path / relative_path).resolve()

            try:
                absolute_path.relative_to(repo_path)
            except ValueError as exc:
                raise ValueError(
                    f"Targeted file escapes repository: {file_path}"
                ) from exc

            if not absolute_path.is_file():
                raise ValueError(
                    f"Targeted repository file does not exist: {file_path}"
                )

            content = absolute_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            if len(content) > self.MAX_TARGETED_FILE_CHARS:
                raise ValueError(
                    f"Targeted file is too large: {file_path}"
                )

            section = (
                f"\n## Complete file: {relative_path.as_posix()}\n"
                f"```text\n{content}\n```\n"
            )

            if total_chars + len(section) > self.MAX_TARGETED_TOTAL_CHARS:
                raise ValueError("Targeted repository context is too large")

            context_parts.append(section)
            total_chars += len(section)

        return "\n".join(context_parts)


    def build(self, workspace_path:str)->str :
        if workspace_path is None:
            raise ValueError("There is not repository")

        repo_path = Path(workspace_path)


        if not repo_path.exists():
            raise ValueError(f"Repository does not exist: {repo_path}")

        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")

        project_files = []
        python_files = []
        test_files = []

        excluded_directories = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
        }


        important_file = {
            "README.md",
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
        }

        for file in repo_path.rglob("*"):

            if not file.is_file():
                continue

            relative_path = file.relative_to(repo_path)

            if any(part in excluded_directories for part in relative_path.parts):
                continue 

            if file.name in important_file:
                project_files.append(relative_path)


            elif file.suffix == ".py":
                if "tests" in relative_path.parts or file.name.startswith("test_"):
                    test_files.append(relative_path)
                else:
                    python_files.append(relative_path) 

        project_files.sort()
        python_files.sort()
        test_files.sort()

        context_parts: list[str] = []
        total_chars = 0

        selected_files = [
            *project_files,
            *python_files,
            *test_files
        ][:self.MAX_FILES]

        for relative_path in selected_files:
            absolute_path=  repo_path / relative_path

            try:
                content = absolute_path.read_text(
                    encoding = "utf-8",
                    errors = "replace"
                )
            except OSError:
                continue

            content = content[:self.MAX_CHARS_PER_FILE]


            section = (
                f"\n## File: {relative_path}\n"
                f"```text\n{content}\n```\n"
            )

            if total_chars + len(section) > self.MAX_TOTAL_CHARS:
                break

            context_parts.append(section)
            total_chars += len(section)

        return "\n".join(context_parts)
