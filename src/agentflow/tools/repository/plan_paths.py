from pathlib import Path

from agentflow.domain.implementation_plan import ImplementationPlan


class PlanPathNormalizer:
    """Convert uniquely resolvable project-relative paths to repo-relative."""

    def normalize(
        self,
        plan: ImplementationPlan,
        workspace_path: str,
    ) -> ImplementationPlan:
        repo_path = Path(workspace_path).resolve()
        if not repo_path.is_dir():
            raise ValueError(f"Workspace does not exist: {workspace_path}")

        path_mapping: dict[str, str] = {}

        normalized_modify = [
            self._normalize_existing(path, repo_path)
            for path in plan.files_to_modify
        ]
        path_mapping.update(
            zip(plan.files_to_modify, normalized_modify)
        )

        normalized_create = [
            self._normalize_new(path, repo_path)
            for path in plan.files_to_create
        ]
        path_mapping.update(
            zip(plan.files_to_create, normalized_create)
        )

        normalized_steps = [
            step.model_copy(
                update={
                    "files": [
                        path_mapping.get(path, path)
                        for path in step.files
                    ]
                }
            )
            for step in plan.steps
        ]

        normalized_tests = [
            path_mapping.get(
                path,
                self._normalize_new(path, repo_path),
            )
            for path in plan.tests_to_add
        ]

        return plan.model_copy(
            update={
                "steps": normalized_steps,
                "files_to_modify": normalized_modify,
                "files_to_create": normalized_create,
                "tests_to_add": normalized_tests,
            }
        )

    @staticmethod
    def _normalize_existing(path_text: str, repo_path: Path) -> str:
        path = Path(path_text)
        if path.is_absolute() or ".." in path.parts:
            return path_text

        direct_candidate = repo_path / path
        if direct_candidate.is_file():
            return path.as_posix()

        candidates = [
            candidate
            for candidate in repo_path.rglob(path.name)
            if candidate.is_file()
            and tuple(candidate.relative_to(repo_path).parts[-len(path.parts):])
            == path.parts
        ]

        if len(candidates) == 1:
            return candidates[0].relative_to(repo_path).as_posix()

        return path_text

    @staticmethod
    def _normalize_new(path_text: str, repo_path: Path) -> str:
        path = Path(path_text)
        if path.is_absolute() or ".." in path.parts:
            return path_text

        if (repo_path / path).parent.is_dir():
            return path.as_posix()

        parent_parts = path.parent.parts
        if not parent_parts:
            return path_text

        candidate_parents = [
            candidate
            for candidate in repo_path.rglob(path.parent.name)
            if candidate.is_dir()
            and tuple(
                candidate.relative_to(repo_path).parts[-len(parent_parts):]
            ) == parent_parts
        ]

        if len(candidate_parents) == 1:
            return (
                candidate_parents[0].relative_to(repo_path) / path.name
            ).as_posix()

        return path_text
