from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.domain.enums import TicketValidationStatus
from agentflow.domain.plan_validation import PlanValidationStatus
from agentflow.domain.patch_validation import PatchValidationStatus
from agentflow.domain.verification import VerificationStatus
from agentflow.domain.code_review import (
    ReviewDecision,
    ReviewValidationStatus,
)

def route_validation(state: JiraToPRState) -> str :
    if state.validation is None:
        raise ValueError("Validation result is missing")

    if state.validation.status == TicketValidationStatus.READY:
        return "READY"

    if state.validation.status == TicketValidationStatus.CLARIFICATION_REQUIRED:
        return "CLARIFICATION_REQUIRED"

    return "REJECTED"

def route_plan_validation(state: JiraToPRState) -> str:
    if state.plan_validation is None:
        raise ValueError("Plan validation result is missing")

    if ( state.plan_validation.status == PlanValidationStatus.VALID):
        return "VALID"

    return "INVALID"

def route_plan_approval(state:JiraToPRState)-> str:

    if state.plan_approval_status == "approve":
        return "approve"
        
        

    elif state.plan_approval_status == "reject":

        return "reject"

    else: 
        return "request_changes"


def route_implementation_approval(state:JiraToPRState)-> str:
    if state.patch_validation is None:
            raise ValueError("Patch validation result is missing")

    if state.patch_validation.status == PatchValidationStatus.VALID:
        return "VALID"

    if (
        state.patch_generation_attempts
        >= state.max_patch_generation_attempts
    ):
        return "RETRY_LIMIT_REACHED"

    return "RETRY"

def  route_verification(state:JiraToPRState)->str:
    if state.verification_result is None:
        raise ValueError("Verification result is missing")

    if state.verification_result.status == VerificationStatus.PASSED:
        return "PASSED"

    if state.verification_result.status == VerificationStatus.ERROR:
        return "ERROR"

    if state.repair_attempts >= state.max_repair_attempts:
        return "REPAIR_LIMIT_REACHED"

    return "FAILED"


def route_repair_patch_validation(state: JiraToPRState) -> str:
    if state.repair_patch_validation is None:
        raise ValueError("Repair patch validation result is missing")

    if (
        state.repair_patch_validation.status
        == PatchValidationStatus.VALID
    ):
        return "VALID"

    return "INVALID"


def route_code_review(state: JiraToPRState) -> str:
    if state.review_validation is None:
        raise ValueError("Review validation result is missing")

    if (
        state.review_validation.status
        == ReviewValidationStatus.INVALID
    ):
        return "INVALID"

    if state.code_review is None:
        raise ValueError("Code review result is missing")

    if state.code_review.decision == ReviewDecision.APPROVED:
        return "APPROVED"

    if (
        state.code_review.decision
        == ReviewDecision.CHANGES_REQUESTED
    ):
        return "CHANGES_REQUESTED"

    return "REJECTED"


def route_pr_approval(state: JiraToPRState) -> str:
    if state.pr_approval_status == "approve":
        return "approve"

    if state.pr_approval_status == "reject":
        return "reject"

    if state.pr_approval_status == "request_changes":
        return "request_changes"

    raise ValueError(
        f"Invalid PR approval status: {state.pr_approval_status}"
    )
