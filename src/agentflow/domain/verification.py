from pydantic import BaseModel
from enum import Enum

class CommandResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


class VerificationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"

class VerificationResult(BaseModel):
    status: VerificationStatus
    command_results: list[CommandResult]
    errors: list[str] = []
