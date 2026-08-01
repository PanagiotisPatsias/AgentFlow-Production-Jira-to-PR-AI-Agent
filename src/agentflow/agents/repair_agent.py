from agentflow.llm.openai_client import Client
from agentflow.domain.jira_ticket import JiraTicket
from agentflow.domain.implementation_plan import ImplementationPlan
from agentflow.domain.patch_proposal import PatchProposal
from agentflow.domain.verification import VerificationResult
from agentflow.prompts.repair import (
    build_repair_system_prompt,
    build_repair_user_prompt,
)


class RepairAgent:
    def __init__(self, client: Client):
        self.client = client

    def repair(
        self,
        ticket: JiraTicket,
        plan: ImplementationPlan,
        previous_patch: PatchProposal,
        verification_result: VerificationResult,
        repository_context: str,
        repair_attempt: int,
    ) -> PatchProposal:
        system_prompt = build_repair_system_prompt()
        user_prompt = build_repair_user_prompt(
            ticket=ticket,
            plan=plan,
            previous_patch=previous_patch,
            verification_result=verification_result,
            repository_context=repository_context,
            repair_attempt=repair_attempt,
        )

        return self.client.response(user_prompt, system_prompt)
