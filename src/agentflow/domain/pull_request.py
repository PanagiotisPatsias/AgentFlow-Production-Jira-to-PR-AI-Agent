from pydantic import BaseModel

class PullRequestResult(BaseModel):
    number: int
    url: str
    title: str
    draft: bool