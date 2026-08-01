from pathlib import Path
import subprocess
import time
from uuid import uuid4

from agentflow.domain.verification import (
    CommandResult,
    VerificationResult,
    VerificationStatus,
)


class VerificationRunner:
    BUILD_TIMEOUT_SECONDS = 600
    TEST_TIMEOUT_SECONDS = 300

    def run(self, workspace_path: str) -> VerificationResult:
        if not workspace_path:
            raise ValueError("Workspace path is required")

        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise ValueError(
                f"Workspace does not exist or is not a directory: {repo_path}"
            )

        if not (repo_path / ".git").is_dir():
            raise ValueError(
                f"Workspace is not a Git repository: {repo_path}"
            )

        project_path = self._detect_project_root(repo_path)

        if not self._has_tests(project_path):
            return VerificationResult(
                status=VerificationStatus.FAILED,
                command_results=[],
                errors=["No test files were found in the repository"],
            )

        started_at = time.monotonic()

        try:
            if self._has_repository_dockerfile(project_path):
                command_results = self._run_with_repository_dockerfile(
                    project_path
                )
            else:
                strategy = self._detect_dependency_strategy(project_path)
                command_results = self._run_with_controlled_image(
                    project_path,
                    strategy,
                )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started_at
            stdout = self._normalise_output(exc.stdout)
            stderr = self._normalise_output(exc.stderr)

            return VerificationResult(
                status=VerificationStatus.ERROR,
                command_results=[
                    CommandResult(
                        command="docker verification",
                        exit_code=-1,
                        stdout=stdout,
                        stderr=stderr,
                        duration_seconds=duration,
                    )
                ],
                errors=["Docker verification exceeded its timeout"],
            )
        except FileNotFoundError:
            duration = time.monotonic() - started_at

            return VerificationResult(
                status=VerificationStatus.ERROR,
                command_results=[
                    CommandResult(
                        command="docker",
                        exit_code=-1,
                        stdout="",
                        stderr="Docker executable was not found",
                        duration_seconds=duration,
                    )
                ],
                errors=[
                    "Docker is not installed or is not available in PATH"
                ],
            )

        failed_results = [
            result
            for result in command_results
            if result.exit_code != 0
        ]

        if failed_results:
            infrastructure_failure = any(
                result.exit_code in {125, 126, 127}
                for result in failed_results
            )
            return VerificationResult(
                status=(
                    VerificationStatus.ERROR
                    if infrastructure_failure
                    else VerificationStatus.FAILED
                ),
                command_results=command_results,
                errors=[
                    (
                        "Verification command failed with exit code "
                        f"{result.exit_code}: {result.command}"
                    )
                    for result in failed_results
                ],
            )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            command_results=command_results,
            errors=[],
        )

    @staticmethod
    def _has_tests(repo_path: Path) -> bool:
        excluded_directories = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
        }

        for file_path in repo_path.rglob("*"):
            relative_path = file_path.relative_to(repo_path)

            if any(
                part in excluded_directories
                for part in relative_path.parts
            ):
                continue

            if file_path.is_file() and (
                file_path.name.startswith("test_")
                or file_path.name.endswith("_test.py")
            ):
                return True

        return False

    @classmethod
    def _detect_project_root(cls, repo_path: Path) -> Path:
        """Locate the Python project instead of assuming repository root."""
        manifest_names = {
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "setup.cfg",
        }
        candidates = {repo_path}

        for manifest_name in manifest_names:
            for manifest in repo_path.rglob(manifest_name):
                relative_path = manifest.relative_to(repo_path)
                if any(
                    part in {".git", ".venv", "venv", "node_modules"}
                    for part in relative_path.parts
                ):
                    continue
                candidates.add(manifest.parent)

        candidates_with_tests = [
            candidate
            for candidate in candidates
            if cls._has_tests(candidate)
        ]

        if not candidates_with_tests:
            return repo_path

        def candidate_score(candidate: Path) -> tuple[int, int, int]:
            has_pyproject = int((candidate / "pyproject.toml").is_file())
            has_manifest = int(
                any((candidate / name).is_file() for name in manifest_names)
            )
            depth = len(candidate.relative_to(repo_path).parts)
            return has_pyproject, has_manifest, depth

        return max(candidates_with_tests, key=candidate_score)

    @staticmethod
    def _has_repository_dockerfile(repo_path: Path) -> bool:
        return (repo_path / "Dockerfile").is_file()

    def _run_with_repository_dockerfile(
        self,
        repo_path: Path,
    ) -> list[CommandResult]:
        identifier = uuid4().hex
        image_tag = f"agentflow-repository-{identifier}"
        verifier_image_tag = f"agentflow-verification-{identifier}"

        try:
            build_command = [
                "docker",
                "build",
                "--tag",
                image_tag,
                str(repo_path),
            ]
            build_result = self._run_command(
                command=build_command,
                cwd=repo_path,
                timeout=self.BUILD_TIMEOUT_SECONDS,
            )

            if build_result.exit_code != 0:
                return [build_result]

            # Keep test tooling out of the target repository's production
            # dependencies. Build an ephemeral layer on top of its image.
            verifier_dockerfile = (
                f"FROM {image_tag}\n"
                "RUN python -m pip install --no-cache-dir pytest\n"
                "WORKDIR /workspace\n"
                "COPY . /workspace\n"
            )
            verifier_build_command = [
                "docker",
                "build",
                "--tag",
                verifier_image_tag,
                "--file",
                "-",
                str(repo_path),
            ]
            verifier_build_result = self._run_command(
                command=verifier_build_command,
                cwd=repo_path,
                timeout=self.BUILD_TIMEOUT_SECONDS,
                input_text=verifier_dockerfile,
            )

            if verifier_build_result.exit_code != 0:
                return [build_result, verifier_build_result]

            test_command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                "1g",
                "--cpus",
                "1",
                "--pids-limit",
                "256",
                "--workdir",
                "/workspace",
                "--entrypoint",
                "python",
                verifier_image_tag,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
            ]
            test_result = self._run_command(
                command=test_command,
                timeout=self.TEST_TIMEOUT_SECONDS,
            )

            return [
                build_result,
                verifier_build_result,
                test_result,
            ]
        finally:
            self._remove_image(verifier_image_tag)
            self._remove_image(image_tag)

    def _run_with_controlled_image(
        self,
        repo_path: Path,
        strategy: str,
    ) -> list[CommandResult]:
        image_tag = f"agentflow-controlled-{uuid4().hex}"
        dockerfile = self._build_controlled_dockerfile(strategy)

        try:
            build_command = [
                "docker",
                "build",
                "--tag",
                image_tag,
                "--file",
                "-",
                str(repo_path),
            ]
            build_result = self._run_command(
                command=build_command,
                cwd=repo_path,
                timeout=self.BUILD_TIMEOUT_SECONDS,
                input_text=dockerfile,
            )

            if build_result.exit_code != 0:
                return [build_result]

            test_command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                "1g",
                "--cpus",
                "1",
                "--pids-limit",
                "256",
                "--workdir",
                "/workspace",
                "--entrypoint",
                "python",
                image_tag,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
            ]
            test_result = self._run_command(
                command=test_command,
                timeout=self.TEST_TIMEOUT_SECONDS,
            )

            return [build_result, test_result]
        finally:
            self._remove_image(image_tag)

    @staticmethod
    def _build_controlled_dockerfile(strategy: str) -> str:
        if strategy == "requirements":
            return """
FROM python:3.12-slim
WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir pytest -r /tmp/requirements.txt
COPY . /workspace
""".strip()

        if strategy == "pyproject":
            return """
FROM python:3.12-slim
WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir pytest .
""".strip()

        if strategy == "none":
            return """
FROM python:3.12-slim
WORKDIR /workspace
RUN pip install --no-cache-dir pytest
COPY . /workspace
""".strip()

        raise ValueError(
            f"Unsupported dependency strategy: {strategy}"
        )

    @staticmethod
    def _detect_dependency_strategy(repo_path: Path) -> str:
        if (repo_path / "requirements.txt").is_file():
            return "requirements"

        if (repo_path / "pyproject.toml").is_file():
            return "pyproject"

        return "none"

    @staticmethod
    def _run_command(
        command: list[str],
        timeout: int,
        cwd: Path | None = None,
        input_text: str | None = None,
    ) -> CommandResult:
        started_at = time.monotonic()
        result = subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return CommandResult(
            command=" ".join(command),
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=time.monotonic() - started_at,
        )

    @staticmethod
    def _remove_image(image_tag: str) -> None:
        try:
            subprocess.run(
                ["docker", "image", "rm", "--force", image_tag],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            # Cleanup must not hide the original build or test failure.
            pass

    @staticmethod
    def _normalise_output(output: str | bytes | None) -> str:
        if output is None:
            return ""

        if isinstance(output, bytes):
            return output.decode(errors="replace")

        return output
