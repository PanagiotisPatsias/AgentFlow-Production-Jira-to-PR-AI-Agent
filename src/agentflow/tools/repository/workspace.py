from tempfile import mkdtemp
import subprocess
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