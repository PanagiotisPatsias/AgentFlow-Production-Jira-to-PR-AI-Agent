from agentflow.domain.code_review import CodeReviewResult
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.domain.verification import VerificationResult
from agentflow.llm.openai_client import Client
from agentflow.prompts.review import (
    build_review_system_prompt,
    build_review_user_prompt,
)


class ReviewAgent:
    def __init__(self, client: Client):
        self.client = client

    def review(
        self,
        ticket: JiraTicket,
        plan: ImplementationPlan,
        initial_patch: PatchProposal,
        repair_patch: PatchProposal | None,
        verification_result: VerificationResult,
        repository_context: str,
    ) -> CodeReviewResult:
        system_prompt = build_review_system_prompt()
        user_prompt = build_review_user_prompt(
            ticket=ticket,
            plan=plan,
            initial_patch=initial_patch,
            repair_patch=repair_patch,
            verification_result=verification_result,
            repository_context=repository_context,
        )

        return self.client.response(user_prompt, system_prompt)
