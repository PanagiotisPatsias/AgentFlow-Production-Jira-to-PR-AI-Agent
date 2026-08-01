from enum import Enum
from pydantic import BaseModel

class PatchValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class PatchValidationResult(BaseModel):
    status: PatchValidationStatus
    errors: list[str]
    warnings: list[str]

