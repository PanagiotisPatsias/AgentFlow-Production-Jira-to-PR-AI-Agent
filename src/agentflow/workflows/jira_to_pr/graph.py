from langgraph.graph import StateGraph,START, END
from agentflow.workflows.jira_to_pr.state import JiraToPRState
from agentflow.workflows.jira_to_pr.nodes import create_fetch_ticket_node ,validate_ticket_node,plan_approval_node
from agentflow.integrations.jira.client import JiraClient
from agentflow.core.config import Setting
from agentflow.workflows.jira_to_pr.routes import route_validation,route_plan_validation, route_plan_approval
from agentflow.tools.repository.workspace import WorkspaceManager
from agentflow.workflows.jira_to_pr.nodes import create_prepare_workspace_node
from agentflow.workflows.jira_to_pr.nodes import create_repository_context_builder, create_planning_agent_node,validate_implementation_plan_node
from agentflow.tools.repository.context import RepositoryContextBuilder
from agentflow.agents.planning_agent import PlanningAgent
from agentflow.llm.openai_client import Client
from langgraph.checkpoint.memory import InMemorySaver
from uuid import uuid4
from langgraph.types import Command



setting = Setting()
graph = StateGraph(JiraToPRState)
client = JiraClient(settings=setting)
fetch_ticket_node = create_fetch_ticket_node(client)
workspace_manager = WorkspaceManager()
prepare_workspace_node = create_prepare_workspace_node(workspace_manager)
repo_context = RepositoryContextBuilder()
repository_context_builder = create_repository_context_builder(repo_context)
client = Client(setting.OPENAI_API_KEY,setting.OPENAI_MODEL)
planning_agent = PlanningAgent(client)
planning_agent_node = create_planning_agent_node(planning_agent)

graph.add_edge(START, "fetch_ticket_node")
graph.add_node("fetch_ticket_node",fetch_ticket_node)
graph.add_node("validate_ticket_node",validate_ticket_node)
graph.add_node("prepare_workspace_node",prepare_workspace_node)
graph.add_node("retrieve_repository_context",repository_context_builder)
graph.add_node("planning_agent",planning_agent_node)
graph.add_node("validate_implementation_plan",validate_implementation_plan_node)
graph.add_node("plan_approval_node",plan_approval_node)


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
        "approve": "create_branch",
        "reject": END,
        "request_changes": "planning_agent",

    },
)

graph.add_edge("fetch_ticket_node", "validate_ticket_node")
graph.add_edge("prepare_workspace_node", "retrieve_repository_context" )
graph.add_edge("retrieve_repository_context",  "planning_agent")
graph.add_edge("planning_agent","validate_implementation_plan" )
graph.add_edge("plan_approval_node", END)

memory = InMemorySaver()
graph = graph.compile(checkpointer=memory)

initial_input = {
    "ticket_key": "SCRUM-1",
    "repository_url": "https://github.com/PanagiotisPatsias/DENGUE-FORECASTING-IN-BRAZIL",
    "base_branch": "main",
}

config = {
    "configurable": {
        "thread_id": str(uuid4()),
    }
}

paused_state = graph.invoke(
    initial_input,
    config=config,
)

interrupts = paused_state.get("__interrupt__",[])
if interrupts:
    approval_request = interrupts[0].value
    print(approval_request)

else:
    print("The graph did not reach an interrupt")
    print(paused_state.get("plan_validation"))

approval_request = interrupts[0].value

print(approval_request["ticket_key"])
print(approval_request["implementation_plan"])
print(approval_request["plan_validation"])

decision = input(
    "Decision [approve/reject/request_changes]: "
).strip()

feedback = input("Feedback: ").strip()

final_state = graph.invoke(
    Command(
        resume={
            "decision": decision,
            "feedback": feedback,
        }
    ),
    config=config,
)



print(final_state)
# print(final_state["validation"])


# from pathlib import Path

# workspace_path = final_state["workspace_path"]

# print(workspace_path)
# print(Path(workspace_path).exists())
# print((Path(workspace_path) / ".git").exists())

# print(final_state["implementation_plan"])