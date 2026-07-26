from openai import OpenAI
from agentflow.domain.implementation_plan import ImplementationPlan

class Client():
    def __init__(self, api_key:str,model:str,timeout: float = 30):
        self.api_key = api_key
        self.client = OpenAI(api_key = api_key, timeout=timeout)
        self.model = model

    def response(self,user_prompt:str, system_prompt):


        response = self.client.responses.parse(
            instructions=system_prompt,
            input=user_prompt,
            model=self.model,
            text_format=ImplementationPlan,
            )


        plan = response.output_parsed

        if plan is None:
            raise ValueError(
                "The model did not return a valid implementation plan"
            )

        return plan