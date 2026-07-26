from pathlib import Path


class RepositoryContextBuilder():

    MAX_FILES = 30
    MAX_CHARS_PER_FILE = 10_000
    MAX_TOTAL_CHARS = 100_000


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
