from agentflow.prompts.implementation import build_implementation_system_prompt,build_implementation_user_prompt
from agentflow.llm.openai_client import Client
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.implementation_plan import ImplementationPlan



class ImplementationAgent():
    def __init__(self, client:Client):
        self.client = client

    def implementation(
        self,
        ticket: JiraTicket,
        plan: ImplementationPlan,
        repository_context: str,
        validation_errors: list[str] | None = None,
        attempt: int = 1,
    ):
        system_prompt = build_implementation_system_prompt()
        user_prompt = build_implementation_user_prompt(
            ticket,
            plan,
            repository_context,
            validation_errors=validation_errors,
            attempt=attempt,
        )
        
        implementation = self.client.response(user_prompt,system_prompt)

        return implementation
