from enum import Enum

from pydantic import BaseModel, Field


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewFinding(BaseModel):
    severity: FindingSeverity
    title: str
    description: str
    file_path: str | None = None
    recommendation: str


class CodeReviewResult(BaseModel):
    decision: ReviewDecision
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    acceptance_criteria_covered: list[int] = Field(
        default_factory=list
    )
    risks: list[str] = Field(default_factory=list)


class ReviewValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class ReviewValidationResult(BaseModel):
    status: ReviewValidationStatus
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
