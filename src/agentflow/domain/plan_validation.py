from enum import Enum

from pydantic import BaseModel
from pathlib import Path
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket


class PlanValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class PlanValidationResult(BaseModel):
    status: PlanValidationStatus
    errors: list[str]
    warnings: list[str]


def validate_implementation_plan(
    plan: ImplementationPlan,
    ticket: JiraTicket,
    workspace_path: str,
) -> PlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    repo_path = Path(workspace_path).resolve()

    if not repo_path.is_dir():
        raise ValueError(
            f"Workspace does not exist: {workspace_path}"
        )

    # Summary validation
    if not plan.summary.strip():
        errors.append("The implementation plan has no summary")

    # Steps validation
    if not plan.steps:
        errors.append("The implementation plan has no steps")

    orders = [step.order for step in plan.steps]
    expected_orders = list(range(1, len(orders) + 1))

    if len(orders) != len(set(orders)):
        errors.append("Plan step orders are not unique")

    if sorted(orders) != expected_orders:
        errors.append(
            "Plan step orders must be consecutive, starting from 1"
        )

    # Validate that a path remains inside the workspace
    def resolve_plan_path(file_path: str) -> Path | None:
        path = Path(file_path)

        if path.is_absolute() or ".." in path.parts:
            errors.append(f"Unsafe file path: {file_path}")
            return None

        candidate = (repo_path / path).resolve()

        try:
            candidate.relative_to(repo_path)
        except ValueError:
            errors.append(
                f"File path escapes the workspace: {file_path}"
            )
            return None

        return candidate

    modify_files = set(plan.files_to_modify)
    create_files = set(plan.files_to_create)

    # A file cannot be both modified and created
    duplicated_files = modify_files & create_files

    if duplicated_files:
        errors.append(
            f"Files listed for both modification and creation: "
            f"{sorted(duplicated_files)}"
        )

    # Files to modify must already exist
    for file_path in modify_files:
        candidate = resolve_plan_path(file_path)

        if candidate is not None and not candidate.is_file():
            errors.append(
                f"File to modify does not exist: {file_path}"
            )

    # Files to create must not already exist
    for file_path in create_files:
        candidate = resolve_plan_path(file_path)

        if candidate is not None and candidate.exists():
            errors.append(
                f"File to create already exists: {file_path}"
            )

    declared_files = modify_files | create_files

    # Validate every step
    covered_ids: set[int] = set()

    for step in plan.steps:
        if not step.description.strip():
            errors.append(
                f"Step {step.order} has no description"
            )

        if not step.files:
            errors.append(
                f"Step {step.order} does not reference any files"
            )

        for file_path in step.files:
            resolve_plan_path(file_path)

            if file_path not in declared_files:
                errors.append(
                    f"Step {step.order} references an undeclared file: "
                    f"{file_path}"
                )

        if not step.acceptance_criteria_ids:
            warnings.append(
                f"Step {step.order} is not linked to an "
                "acceptance criterion"
            )

        covered_ids.update(step.acceptance_criteria_ids)

    # Acceptance-criteria validation
    expected_ids = set(
        range(1, len(ticket.acceptance_criteria) + 1)
    )

    missing_ids = expected_ids - covered_ids
    unknown_ids = covered_ids - expected_ids

    if missing_ids:
        errors.append(
            f"Missing acceptance criteria IDs: {sorted(missing_ids)}"
        )

    if unknown_ids:
        errors.append(
            f"Unknown acceptance criteria IDs: {sorted(unknown_ids)}"
        )

    # Tests are mandatory
    if not plan.tests_to_add:
        errors.append("The implementation plan includes no tests")

    # Assumptions require attention during approval
    if plan.assumptions:
        warnings.append(
            "The implementation plan contains assumptions "
            "that require human review"
        )

    status = (
        PlanValidationStatus.INVALID
        if errors
        else PlanValidationStatus.VALID
    )

    return PlanValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
    )
