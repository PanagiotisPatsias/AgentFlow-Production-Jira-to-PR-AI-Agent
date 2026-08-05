from langgraph.graph import StateGraph,START, END
from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.workflows.jira_to_pr.nodes import create_fetch_ticket_node ,validate_ticket_node,plan_approval_node
from agentflow.integrations.jira.client import JiraClient
from agentflow.core.config import Setting
from agentflow.workflows.jira_to_pr.routes import route_validation,route_plan_validation, route_plan_approval, route_implementation_approval,route_verification, route_repair_patch_validation, route_code_review, route_pr_approval
from agentflow.tools.repository.workspace import WorkspaceManager
from agentflow.workflows.jira_to_pr.nodes import create_prepare_workspace_node,create_patch_validation_node,create_patch_applier_node, create_verification_runner_node,create_repair_agent_node, create_repair_patch_validation_node, create_repair_patch_applier_node, create_review_agent_node, create_review_validation_node, create_review_repair_agent_node, human_pr_approval_node, create_commit_changes_node, create_push_branch_node, create_pull_request_node, create_update_jira_node, create_cleanup_workspace_node
from agentflow.workflows.jira_to_pr.nodes import create_repository_context_builder, create_planning_agent_node,validate_implementation_plan_node, create_create_branch_node,create_implementation_agent_node
from agentflow.tools.repository.context import RepositoryContextBuilder
from agentflow.agents.planning_agent import PlanningAgent
from agentflow.agents.repair_agent import RepairAgent
from agentflow.llm.openai_client import Client
from uuid import uuid4
from langgraph.types import Command
from agentflow.tools.repository.branch import GitBranchManager
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.agents.implementation import ImplementationAgent
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.tools.git.patch_validator import PatchValidator
from agentflow.tools.git.patch_applier import PatchApplier
from agentflow.tools.verification.runner import VerificationRunner
from agentflow.tools.git.repair_patch_validator import RepairPatchValidator
from agentflow.agents.review_agent import ReviewAgent
from agentflow.domain.code_review import CodeReviewResult
from agentflow.tools.review.validator import ReviewValidator
from agentflow.tools.git.commit import GitCommitManager
from agentflow.tools.git.push import GitPushManager
from agentflow.integrations.github.client import GitHubClient
from agentflow.agents.review_repair_agent import ReviewRepairAgent
from agentflow.database.repositories.workflow_run_repository import WorkflowRunRepository
from agentflow.database.session import SessionLocal
from agentflow.workflows.jira_to_pr.tracking import create_tracked_node
from agentflow.database.enums import WorkflowRunStatus
from agentflow.checkpointing.postgres import create_postgres_checkpointer


setting = Setting()
graph = StateGraph(JiraToPRState)
jira_client = JiraClient(settings=setting)
fetch_ticket_node = create_fetch_ticket_node(jira_client)
workspace_manager = WorkspaceManager()
prepare_workspace_node = create_prepare_workspace_node(workspace_manager)
repo_context = RepositoryContextBuilder()
repository_context_builder = create_repository_context_builder(repo_context)
planning_client = Client(setting.OPENAI_API_KEY,setting.OPENAI_MODEL, format = ImplementationPlan, timeout=setting.OPENAI_TIMEOUT)
planning_agent = PlanningAgent(planning_client)
planning_agent_node = create_planning_agent_node(planning_agent)
branch_manager = GitBranchManager()
create_branch_node = create_create_branch_node(branch_manager)
client_implementation =  Client(setting.OPENAI_API_KEY,setting.OPENAI_MODEL, format = PatchProposal, timeout=setting.OPENAI_TIMEOUT)
implementation_agent = ImplementationAgent(client_implementation)
patch_validator = PatchValidator()
implementation_agent_node = create_implementation_agent_node(implementation_agent)
patch_validation_node = create_patch_validation_node(patch_validator)
patch_applier = PatchApplier()
patch_applier_node = create_patch_applier_node(patch_applier)
runner = VerificationRunner()
verification_runner_node = create_verification_runner_node(runner)
client_repair = Client(setting.OPENAI_API_KEY,setting.OPENAI_MODEL, format = PatchProposal, timeout=setting.OPENAI_TIMEOUT)
repair = RepairAgent(client_repair)
repair_agent_node = create_repair_agent_node(repair)
repair_patch_validator = RepairPatchValidator()
repair_patch_validation_node = create_repair_patch_validation_node(repair_patch_validator)
repair_patch_applier_node = create_repair_patch_applier_node(patch_applier)
review_client = Client(setting.OPENAI_API_KEY,setting.OPENAI_MODEL,format=CodeReviewResult,timeout=setting.OPENAI_TIMEOUT)
review_agent = ReviewAgent(review_client)
review_agent_node = create_review_agent_node(review_agent)
review_validator = ReviewValidator()
review_validation_node = create_review_validation_node(review_validator)
review_repair_client = Client(setting.OPENAI_API_KEY, setting.OPENAI_MODEL, format=PatchProposal,timeout=setting.OPENAI_TIMEOUT)
review_repair_agent = ReviewRepairAgent(review_repair_client)
review_repair_agent_node = create_review_repair_agent_node(review_repair_agent)
commit_manager = GitCommitManager()
commit_changes_node = create_commit_changes_node(commit_manager)
push_manager = GitPushManager(setting.GITHUB_TOKEN)
push_branch_node = create_push_branch_node(push_manager)
github_client = GitHubClient(token=setting.GITHUB_TOKEN, base_url=setting.BASE_URL, timeout=setting.OPENAI_TIMEOUT)
pull_request_node = create_pull_request_node(github_client)
update_jira_node = create_update_jira_node(jira_client)
cleanup_workspace_node = create_cleanup_workspace_node(workspace_manager)


graph.add_edge(START, "fetch_ticket_node")
graph.add_node(
    "fetch_ticket_node",
    create_tracked_node("fetch_ticket_node", fetch_ticket_node),
)
graph.add_node(
    "validate_ticket_node",
    create_tracked_node("validate_ticket_node", validate_ticket_node),
)
graph.add_node(
    "prepare_workspace_node",
    create_tracked_node("prepare_workspace_node", prepare_workspace_node),
)
graph.add_node(
    "retrieve_repository_context",
    create_tracked_node(
        "retrieve_repository_context",
        repository_context_builder,
    ),
)
graph.add_node(
    "planning_agent",
    create_tracked_node("planning_agent", planning_agent_node),
)
graph.add_node(
    "validate_implementation_plan",
    create_tracked_node(
        "validate_implementation_plan",
        validate_implementation_plan_node,
    ),
)
# Approval nodes use LangGraph interrupt() and require pause-aware tracking.
graph.add_node("plan_approval_node",plan_approval_node)
graph.add_node(
    "create_branch_node",
    create_tracked_node("create_branch_node", create_branch_node),
)
graph.add_node(
    "implementation_agent",
    create_tracked_node("implementation_agent", implementation_agent_node),
)
graph.add_node(
    "patch_validation_node",
    create_tracked_node("patch_validation_node", patch_validation_node),
)
graph.add_node(
    "patch_applier_node",
    create_tracked_node("patch_applier_node", patch_applier_node),
)
graph.add_node(
    "verification_runner_node",
    create_tracked_node("verification_runner_node", verification_runner_node),
)
graph.add_node(
    "repair_agent_node",
    create_tracked_node("repair_agent_node", repair_agent_node),
)
graph.add_node(
    "refresh_repository_context_for_repair",
    create_tracked_node(
        "refresh_repository_context_for_repair",
        repository_context_builder,
    ),
)
graph.add_node(
    "repair_patch_validation_node",
    create_tracked_node(
        "repair_patch_validation_node",
        repair_patch_validation_node,
    ),
)
graph.add_node(
    "repair_patch_applier_node",
    create_tracked_node(
        "repair_patch_applier_node",
        repair_patch_applier_node,
    ),
)
graph.add_node(
    "refresh_repository_context_for_review",
    create_tracked_node(
        "refresh_repository_context_for_review",
        repository_context_builder,
    ),
)
graph.add_node(
    "review_agent_node",
    create_tracked_node("review_agent_node", review_agent_node),
)
graph.add_node(
    "review_validation_node",
    create_tracked_node("review_validation_node", review_validation_node),
)
graph.add_node(
    "refresh_repository_context_for_review_repair",
    create_tracked_node(
        "refresh_repository_context_for_review_repair",
        repository_context_builder,
    ),
)
graph.add_node(
    "review_repair_agent_node",
    create_tracked_node(
        "review_repair_agent_node",
        review_repair_agent_node,
    ),
)
graph.add_node("human_pr_approval_node", human_pr_approval_node)
graph.add_node(
    "commit_changes_node",
    create_tracked_node("commit_changes_node", commit_changes_node),
)
graph.add_node(
    "push_branch_node",
    create_tracked_node("push_branch_node", push_branch_node),
)
graph.add_node(
    "create_pull_request_node",
    create_tracked_node("create_pull_request_node", pull_request_node),
)
graph.add_node(
    "update_jira_node",
    create_tracked_node("update_jira_node", update_jira_node),
)
graph.add_node(
    "cleanup_workspace_node",
    create_tracked_node("cleanup_workspace_node", cleanup_workspace_node),
)






graph.add_conditional_edges(
    "validate_ticket_node",
    route_validation,
    {
        "READY": "prepare_workspace_node",  
        "CLARIFICATION_REQUIRED": END,
        "REJECTED": END,
    }
)


graph.add_conditional_edges(
    "validate_implementation_plan",
    route_plan_validation,
    {
        "VALID": "plan_approval_node",
        "INVALID": END,
    },
)


graph.add_conditional_edges(
    "plan_approval_node",
    route_plan_approval,
    {
        "approve": "create_branch_node",
        "reject": END,
        "request_changes": "planning_agent",

    },
)

graph.add_conditional_edges(
    "patch_validation_node",
    route_implementation_approval,
    {
        "VALID": "patch_applier_node",
        "RETRY": "implementation_agent",
        "RETRY_LIMIT_REACHED": END,

    },
)



graph.add_conditional_edges(
    "verification_runner_node",
    route_verification,
    {
        "PASSED": "refresh_repository_context_for_review",
        "FAILED": "refresh_repository_context_for_repair",
        "ERROR": END,
        "REPAIR_LIMIT_REACHED": END,

    },
)

graph.add_conditional_edges(
    "repair_patch_validation_node",
    route_repair_patch_validation,
    {
        "VALID": "repair_patch_applier_node",
        "INVALID": END,
    },
)

graph.add_conditional_edges(
    "review_validation_node",
    route_code_review,
    {
        "APPROVED": "human_pr_approval_node",
        "CHANGES_REQUESTED": "refresh_repository_context_for_review_repair",
        "REVIEW_REPAIR_LIMIT_REACHED": END,
        "REJECTED": END,
        "INVALID": END,
    },
)

graph.add_conditional_edges(
    "human_pr_approval_node",
    route_pr_approval,
    {
        "approve": "commit_changes_node",
        "reject": END,
        "request_changes": END,
    },
)


graph.add_edge("fetch_ticket_node", "validate_ticket_node")
graph.add_edge("prepare_workspace_node", "retrieve_repository_context" )
graph.add_edge("retrieve_repository_context",  "planning_agent")
graph.add_edge("planning_agent","validate_implementation_plan" )
graph.add_edge("create_branch_node", "implementation_agent")
graph.add_edge("implementation_agent", "patch_validation_node")
graph.add_edge("patch_applier_node", "verification_runner_node")
graph.add_edge("refresh_repository_context_for_repair","repair_agent_node")
graph.add_edge("repair_agent_node", "repair_patch_validation_node")
graph.add_edge("repair_patch_applier_node", "verification_runner_node")
graph.add_edge("refresh_repository_context_for_review","review_agent_node")
graph.add_edge("review_agent_node", "review_validation_node")
graph.add_edge("refresh_repository_context_for_review_repair","review_repair_agent_node",)
graph.add_edge("review_repair_agent_node", "repair_patch_validation_node")
graph.add_edge("commit_changes_node", "push_branch_node")
graph.add_edge("push_branch_node", "create_pull_request_node")
graph.add_edge("create_pull_request_node", "update_jira_node")
graph.add_edge("update_jira_node", "cleanup_workspace_node")
graph.add_edge("cleanup_workspace_node", END)

checkpointer, checkpoint_pool = create_postgres_checkpointer(setting.LANGGRAPH_DATABASE_URL.get_secret_value())

graph = graph.compile(checkpointer=checkpointer)
