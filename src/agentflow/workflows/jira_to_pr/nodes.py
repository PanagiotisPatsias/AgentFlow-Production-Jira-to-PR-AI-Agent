from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.integrations.jira.client import JiraClient
from agentflow.domain.ticket_validation import validate_ticket
from agentflow.domain.ticket_validation import TicketValidationResult
from agentflow.tools.repository.workspace import WorkspaceManager
from agentflow.tools.repository.context import RepositoryContextBuilder
from agentflow.agents.planning_agent import PlanningAgent
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.plan_validation import validate_implementation_plan
from langgraph.types import interrupt


def create_fetch_ticket_node(client:JiraClient):
    def fetch_ticket_node(state:JiraToPRState)-> dict:
        ticket = client.get_ticket(state.ticket_key)
        return {"ticket": ticket}

    return fetch_ticket_node



def validate_ticket_node(state:JiraToPRState) ->TicketValidationResult:
    validation = validate_ticket(state.ticket)
    return {"validation": validation}

def create_prepare_workspace_node(workspace_manager: WorkspaceManager):
    def prepare_workspace_node(state: JiraToPRState) -> dict :

        workspace_path = workspace_manager.prepare(state.repository_url, state.base_branch)

        return  {"workspace_path": workspace_path}


    return prepare_workspace_node

def create_repository_context_builder(repo_context_builder:RepositoryContextBuilder):
    def repository_context_builder(state:JiraToPRState) -> dict:

        if state.workspace_path is None:
            raise ValueError("Workspace has not been prepared")

        repository_context = repo_context_builder.build(state.workspace_path)

        return {"repository_context":repository_context}
    return repository_context_builder


def create_planning_agent_node(planning_agent: PlanningAgent):
    def planning_agent_node(state:JiraToPRState):

        plan = planning_agent.planning(state.ticket,state.repository_context)

        return {"implementation_plan": plan}
    return planning_agent_node



def validate_implementation_plan_node (state: JiraToPRState):

    validate_implementation = validate_implementation_plan(state.implementation_plan,state.ticket, state.workspace_path)

    return {"plan_validation":validate_implementation}


def plan_approval_node(state: JiraToPRState) -> dict:

    if state.implementation_plan is None:
        raise ValueError("Implementation plan is missing")

    if state.plan_validation is None:
        raise ValueError("Plan validation result is missing")

    approval_request = {
        "type": "plan_approval",
        "ticket_key": state.ticket_key,
        "question": "Do you approve this implementation plan?",
        "implementation_plan": (
            state.implementation_plan.model_dump(mode="json")
        ),
        "plan_validation": (
            state.plan_validation.model_dump(mode="json")
        ),
        "allowed_decisions": [
            "approve",
            "reject",
            "request_changes",
        ],
    }

    human_response = interrupt(approval_request)

    if not isinstance(human_response, dict):
            raise ValueError("Human response must be a dictionary")

    decision = human_response.get("decision")
    feedback = human_response.get("feedback", "")

    if decision not in {
        "approve",
        "reject",
        "request_changes",
    }:
        raise ValueError(
            f"Invalid approval decision: {decision}"
        )

    return {
        "plan_approval_status": decision,
        "approval_feedback": feedback,
    }