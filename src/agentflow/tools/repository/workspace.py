from tempfile import mkdtemp
import subprocess
import shutil
import tempfile
from pathlib import Path


class WorkspaceManager():

    def prepare(self, repository_url:str, base_branch:str)->str:
        temp_dir = mkdtemp(prefix="agentflow-")
        repo_path = Path(temp_dir) / "repo"

        subprocess.run(
            ["git","clone", repository_url, str(repo_path)],
            check = True
        )

        subprocess.run(
            ["git", "-C", str(repo_path), "checkout", base_branch],
            check=True,
        )

        return str(repo_path)

    def cleanup(self, workspace_path: str) -> None:
        repo_path = Path(workspace_path).resolve()
        temporary_root = Path(tempfile.gettempdir()).resolve()
        workspace_root = repo_path.parent

        if repo_path.name != "repo":
            raise ValueError(
                f"Refusing to clean an unexpected workspace: {repo_path}"
            )

        if not workspace_root.name.startswith("agentflow-"):
            raise ValueError(
                f"Refusing to clean an unmanaged workspace: {repo_path}"
            )

        try:
            workspace_root.relative_to(temporary_root)
        except ValueError as exc:
            raise ValueError(
                f"Workspace is outside the temporary directory: {repo_path}"
            ) from exc

        if repo_path.exists() and not (repo_path / ".git").is_dir():
            raise ValueError(
                f"Workspace is not a Git repository: {repo_path}"
            )

        if workspace_root.exists():
            shutil.rmtree(workspace_root)
