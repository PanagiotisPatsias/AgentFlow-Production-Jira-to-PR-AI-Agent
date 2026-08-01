import subprocess
from pathlib import Path
from uuid import uuid4

class GitBranchManager:
    def create_branch(
            self,
            workspace_path: str,
            ticket_key: str,
    ) -> str:


        repo_path = Path(workspace_path)

        run_id = uuid4().hex[:8]
        branch_name = (
            f"agentflow/{ticket_key.lower()}-{run_id}"
        )

        subprocess.run(
            [
        "git",
        "-C",
        str(repo_path),
        "switch",
        "-c",
        branch_name,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

        return branch_name
