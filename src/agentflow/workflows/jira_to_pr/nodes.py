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
from agentflow.tools.repository.branch import GitBranchManager
from agentflow.agents.implementation import ImplementationAgent
from agentflow.tools.git.patch_validator import PatchValidator
from agentflow.tools.git.patch_applier import PatchApplier
from agentflow.tools.verification.runner import VerificationRunner
from agentflow.agents.repair_agent import RepairAgent
from agentflow.tools.git.repair_patch_validator import RepairPatchValidator
from agentflow.agents.review_agent import ReviewAgent
from agentflow.tools.review.validator import ReviewValidator
from agentflow.domain.verification import VerificationStatus
from agentflow.domain.code_review import (
    ReviewDecision,
    ReviewValidationStatus,
)
from agentflow.tools.git.commit import GitCommitManager
from agentflow.tools.git.push import GitPushManager
from agentflow.integrations.github.client import GitHubClient


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

def create_create_branch_node(git_branch_manager: GitBranchManager):

    def create_branch_node(state:JiraToPRState):

        branch_name = git_branch_manager.create_branch(state.workspace_path, state.ticket_key)

        return {"branch_name": branch_name} 


    return create_branch_node

def create_implementation_agent_node(
    implementation_agent: ImplementationAgent,
):
    def implementation_agent_node(
        state: JiraToPRState,
    ) -> dict:
        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        if state.repository_context is None:
            raise ValueError("Repository context is missing")

        current_attempt = state.patch_generation_attempts + 1
        validation_errors = None
        if state.patch_validation is not None:
            validation_errors = state.patch_validation.errors

        patch_proposal = implementation_agent.implementation(
            state.ticket,
            state.implementation_plan,
            state.repository_context,
            validation_errors=validation_errors,
            attempt=current_attempt,
        )

        return {
            "patch_proposal": patch_proposal,
            "patch_generation_attempts": current_attempt,
            "patch_validation": None,
        }

    return implementation_agent_node


def create_patch_validation_node(
    patch_validator: PatchValidator,
):
    def patch_validation_node(
        state: JiraToPRState,
    ) -> dict:
        if state.patch_proposal is None:
            raise ValueError("Patch proposal is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        result = patch_validator.validate(
            state.patch_proposal,
            state.implementation_plan,
            state.ticket,
            state.workspace_path,
        )

        return {
            "patch_validation": result,
            "patch_proposal": state.patch_proposal,
        }

    return patch_validation_node


def create_patch_applier_node(
    patch_applier: PatchApplier,
):
    def patch_applier_node(
        state: JiraToPRState,
    ) -> dict:
        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        if state.patch_proposal is None:
            raise ValueError("Patch proposal is missing")

        patch_applier.apply(
            workspace_path=state.workspace_path,
            unified_diff=state.patch_proposal.unified_diff,
        )

        return {
            "patch_applied": True,
        }

    return patch_applier_node


def create_verification_runner_node(runner: VerificationRunner ):
    def verification_runner_node(state: JiraToPRState):

        result = runner.run(state.workspace_path)

        return {"verification_result": result }

    return verification_runner_node


def create_repair_agent_node(repair_agent: RepairAgent):
    def repair_agent_node(state: JiraToPRState) -> dict:
        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        if state.patch_proposal is None:
            raise ValueError("Original patch proposal is missing")

        if state.verification_result is None:
            raise ValueError("Verification result is missing")

        if state.repository_context is None:
            raise ValueError("Repository context is missing")

        current_attempt = state.repair_attempts + 1
        previous_patch = (
            state.repair_patch_proposal
            or state.patch_proposal
        )

        repair = repair_agent.repair(
            ticket=state.ticket,
            plan=state.implementation_plan,
            previous_patch=previous_patch,
            verification_result=state.verification_result,
            repository_context=state.repository_context,
            repair_attempt=current_attempt,
        )

        return {
            "repair_patch_proposal": repair,
            "repair_attempts": current_attempt,
        }

    return repair_agent_node


def create_repair_patch_validation_node(
    repair_patch_validator: RepairPatchValidator,
):
    def repair_patch_validation_node(
        state: JiraToPRState,
    ) -> dict:
        if state.repair_patch_proposal is None:
            raise ValueError("Repair patch proposal is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        result = repair_patch_validator.validate(
            patch=state.repair_patch_proposal,
            plan=state.implementation_plan,
            ticket=state.ticket,
            workspace_path=state.workspace_path,
        )

        return {
            "repair_patch_validation": result,
            "repair_patch_proposal": state.repair_patch_proposal,
        }

    return repair_patch_validation_node


def create_repair_patch_applier_node(
    patch_applier: PatchApplier,
):
    def repair_patch_applier_node(
        state: JiraToPRState,
    ) -> dict:
        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        if state.repair_patch_proposal is None:
            raise ValueError("Repair patch proposal is missing")

        patch_applier.apply(
            workspace_path=state.workspace_path,
            unified_diff=state.repair_patch_proposal.unified_diff,
        )

        return {"patch_applied": True}

    return repair_patch_applier_node


def create_review_agent_node(review_agent: ReviewAgent):
    def review_agent_node(state: JiraToPRState) -> dict:
        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        if state.patch_proposal is None:
            raise ValueError("Initial patch proposal is missing")

        if state.verification_result is None:
            raise ValueError("Verification result is missing")

        if (
            state.verification_result.status
            != VerificationStatus.PASSED
        ):
            raise ValueError(
                "Code review requires successful verification"
            )

        if state.repository_context is None:
            raise ValueError("Repository context is missing")

        review = review_agent.review(
            ticket=state.ticket,
            plan=state.implementation_plan,
            initial_patch=state.patch_proposal,
            repair_patch=state.repair_patch_proposal,
            verification_result=state.verification_result,
            repository_context=state.repository_context,
        )

        return {"code_review": review}

    return review_agent_node


def create_review_validation_node(
    review_validator: ReviewValidator,
):
    def review_validation_node(state: JiraToPRState) -> dict:
        if state.code_review is None:
            raise ValueError("Code review result is missing")

        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        result = review_validator.validate(
            review=state.code_review,
            ticket=state.ticket,
            workspace_path=state.workspace_path,
        )

        return {"review_validation": result}

    return review_validation_node


def human_pr_approval_node(state: JiraToPRState) -> dict:
    if state.code_review is None:
        raise ValueError("Code review result is missing")

    if state.code_review.decision != ReviewDecision.APPROVED:
        raise ValueError("PR approval requires an approved code review")

    if state.review_validation is None:
        raise ValueError("Review validation result is missing")

    if state.review_validation.status != ReviewValidationStatus.VALID:
        raise ValueError("PR approval requires a valid code review")

    if state.verification_result is None:
        raise ValueError("Verification result is missing")

    approval_request = {
        "type": "pull_request_approval",
        "ticket_key": state.ticket_key,
        "question": "Do you approve committing and publishing this change?",
        "branch_name": state.branch_name,
        "verification_result": state.verification_result.model_dump(
            mode="json"
        ),
        "code_review": state.code_review.model_dump(mode="json"),
        "review_validation": state.review_validation.model_dump(
            mode="json"
        ),
        "initial_patch": (
            state.patch_proposal.model_dump(mode="json")
            if state.patch_proposal is not None
            else None
        ),
        "latest_repair_patch": (
            state.repair_patch_proposal.model_dump(mode="json")
            if state.repair_patch_proposal is not None
            else None
        ),
        "repair_attempts": state.repair_attempts,
        "allowed_decisions": [
            "approve",
            "reject",
            "request_changes",
        ],
    }

    human_response = interrupt(approval_request)

    if not isinstance(human_response, dict):
        raise ValueError("Human PR approval response must be a dictionary")

    decision = human_response.get("decision")
    feedback = human_response.get("feedback", "")

    if decision not in {
        "approve",
        "reject",
        "request_changes",
    }:
        raise ValueError(f"Invalid PR approval decision: {decision}")

    return {
        "pr_approval_status": decision,
        "pr_approval_feedback": feedback,
    }


def create_commit_changes_node(
    commit_manager: GitCommitManager,
):
    def commit_changes_node(state: JiraToPRState) -> dict:
        if state.pr_approval_status != "approve":
            raise ValueError("Changes have not been approved for commit")

        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        if state.branch_name is None:
            raise ValueError("Git branch name is missing")

        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.implementation_plan is None:
            raise ValueError("Implementation plan is missing")

        allowed_files = (
            set(state.implementation_plan.files_to_modify)
            | set(state.implementation_plan.files_to_create)
        )

        commit_sha = commit_manager.commit(
            workspace_path=state.workspace_path,
            expected_branch=state.branch_name,
            allowed_files=allowed_files,
            commit_message=f"{state.ticket.key}: {state.ticket.title}",
        )

        return {"commit_sha": commit_sha}

    return commit_changes_node


def create_push_branch_node(
    push_manager: GitPushManager,
):
    def push_branch_node(state: JiraToPRState) -> dict:
        if state.workspace_path is None:
            raise ValueError("Workspace path is missing")

        if state.branch_name is None:
            raise ValueError("Git branch name is missing")

        if state.commit_sha is None:
            raise ValueError("Commit SHA is missing")

        push_manager.push(
            workspace_path=state.workspace_path,
            branch_name=state.branch_name,
            expected_commit_sha=state.commit_sha,
            expected_repository_url=state.repository_url,
        )

        return {"branch_pushed": True}

    return push_branch_node


def create_pull_request_node(github_client: GitHubClient):
    def pull_request_node(state: JiraToPRState) -> dict:
        if not state.branch_pushed:
            raise ValueError("Branch must be pushed before creating a PR")

        if state.branch_name is None:
            raise ValueError("Git branch name is missing")

        if state.ticket is None:
            raise ValueError("Jira ticket is missing")

        if state.verification_result is None:
            raise ValueError("Verification result is missing")

        if state.code_review is None:
            raise ValueError("Code review result is missing")

        body = (
            f"## Jira ticket\n"
            f"{state.ticket.key}: {state.ticket.title}\n\n"
            f"## Summary\n"
            f"{state.patch_proposal.summary if state.patch_proposal else ''}\n\n"
            f"## Verification\n"
            f"Status: {state.verification_result.status.value}\n\n"
            f"## Agent review\n"
            f"Decision: {state.code_review.decision.value}\n\n"
            "Generated by AgentFlow and approved by a human."
        )

        pull_request = github_client.create_draft_pull_request(
            repository_url=state.repository_url,
            head_branch=state.branch_name,
            base_branch=state.base_branch,
            title=f"{state.ticket.key}: {state.ticket.title}",
            body=body,
        )

        return {"pull_request": pull_request}

    return pull_request_node
