from pydantic import BaseModel


class Planstep(BaseModel):
    order: int
    description: str
    files: list[str]    
    acceptance_criteria_ids:list[int]

class ImplementationPlan(BaseModel):
    summary: str
    steps: list[Planstep]
    files_to_modify: list[str]
    files_to_create: list[str]
    tests_to_add: list[str]
    risks: list[str]
    assumptions: list[str]