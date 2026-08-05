from agentflow.domain.code_review import CodeReviewResult
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.llm.openai_client import Client
from agentflow.prompts.review_repair import (
    build_review_repair_system_prompt,
    build_review_repair_user_prompt,
)


class ReviewRepairAgent:
    def __init__(self, client: Client):
        self.client = client

    def repair(
        self,
        ticket: JiraTicket,
        plan: ImplementationPlan,
        review: CodeReviewResult,
        repository_context: str,
        attempt: int,
    ) -> PatchProposal:
        return self.client.response(
            build_review_repair_user_prompt(
                ticket=ticket,
                plan=plan,
                review=review,
                repository_context=repository_context,
                attempt=attempt,
            ),
            build_review_repair_system_prompt(),
        )
