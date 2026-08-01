from pathlib import Path

from agentflow.domain.code_review import (
    CodeReviewResult,
    FindingSeverity,
    ReviewDecision,
    ReviewValidationResult,
    ReviewValidationStatus,
)
from agentflow.domain.jira_ticket import JiraTicket


class ReviewValidator:
    def validate(
        self,
        review: CodeReviewResult,
        ticket: JiraTicket,
        workspace_path: str,
    ) -> ReviewValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        repo_path = Path(workspace_path).resolve()

        if not repo_path.is_dir():
            raise ValueError(
                f"Workspace does not exist: {workspace_path}"
            )

        if not review.summary.strip():
            errors.append("Code review summary is missing")

        expected_ids = set(
            range(1, len(ticket.acceptance_criteria) + 1)
        )
        covered_ids = set(review.acceptance_criteria_covered)
        missing_ids = expected_ids - covered_ids
        unknown_ids = covered_ids - expected_ids

        if missing_ids:
            errors.append(
                "Code review does not evaluate acceptance criteria IDs: "
                f"{sorted(missing_ids)}"
            )

        if unknown_ids:
            errors.append(
                "Code review references unknown acceptance criteria IDs: "
                f"{sorted(unknown_ids)}"
            )

        blocking_severities = {
            FindingSeverity.HIGH,
            FindingSeverity.CRITICAL,
        }
        actionable_severities = {
            FindingSeverity.MEDIUM,
            FindingSeverity.HIGH,
            FindingSeverity.CRITICAL,
        }

        for index, finding in enumerate(review.findings, start=1):
            if not finding.title.strip():
                errors.append(f"Review finding {index} has no title")

            if not finding.description.strip():
                errors.append(
                    f"Review finding {index} has no description"
                )

            if not finding.recommendation.strip():
                errors.append(
                    f"Review finding {index} has no recommendation"
                )

            if finding.file_path is not None:
                path = Path(finding.file_path)

                if path.is_absolute() or ".." in path.parts:
                    errors.append(
                        "Review finding references an unsafe path: "
                        f"{finding.file_path}"
                    )
                    continue

                candidate = (repo_path / path).resolve()

                try:
                    candidate.relative_to(repo_path)
                except ValueError:
                    errors.append(
                        "Review finding path escapes the workspace: "
                        f"{finding.file_path}"
                    )
                    continue

                if not candidate.is_file():
                    errors.append(
                        "Review finding references a file that does not "
                        f"exist: {finding.file_path}"
                    )

        if review.decision == ReviewDecision.APPROVED and any(
            finding.severity in blocking_severities
            for finding in review.findings
        ):
            errors.append(
                "Code review cannot be APPROVED with HIGH or CRITICAL "
                "findings"
            )

        if review.decision == ReviewDecision.CHANGES_REQUESTED:
            if not any(
                finding.severity in actionable_severities
                for finding in review.findings
            ):
                errors.append(
                    "CHANGES_REQUESTED requires at least one MEDIUM, HIGH, "
                    "or CRITICAL finding"
                )

        if review.decision == ReviewDecision.REJECTED:
            if not any(
                finding.severity in blocking_severities
                for finding in review.findings
            ):
                errors.append(
                    "REJECTED requires at least one HIGH or CRITICAL finding"
                )

        if review.decision == ReviewDecision.APPROVED and review.risks:
            warnings.append(
                "Approved review contains risks that require human review"
            )

        status = (
            ReviewValidationStatus.INVALID
            if errors
            else ReviewValidationStatus.VALID
        )

        return ReviewValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
        )
