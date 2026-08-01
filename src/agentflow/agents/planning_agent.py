from agentflow.llm.openai_client import Client
from agentflow.domain.implementation_plan import Planstep,ImplementationPlan
from agentflow.prompts.planning import build_user_prompt,build_system_prompt,build_planning_messages
from agentflow.domain.jira_ticket import JiraTicket

class PlanningAgent():
    def __init__(self,client:Client):
        self.client = client

    def planning(self,ticket:JiraTicket,repository_context:str):
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(ticket, repository_context)
        
        plan = self.client.response(user_prompt,system_prompt)


        return plan 
        