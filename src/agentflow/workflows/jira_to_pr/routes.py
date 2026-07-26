from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.domain.enums import TicketValidationStatus
from agentflow.domain.plan_validation import PlanValidationStatus
from agentflow.workflows.jira_to_pr.nodes import create_planning_agent_node

def route_validation(state: JiraToPRState) -> str :
    if state.validation.status is None:
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

def route_plan_approval(state:JiraToPRState):

    if state.plan_approval_status == "approve":
        return "approve"
        
        

    elif state.plan_approval_status == "reject":

        return "reject"

    else: 
        return "request_changes"