from enum import Enum

from pydantic import BaseModel


class FileOperation(str, Enum):
    MODIFY = "modify"
    CREATE = "create"


class FileChange(BaseModel):
    path: str
    operation: FileOperation
    content: str

class PatchProposal(BaseModel):
    summary: str
    modified_files: list[str]
    created_files: list[str]
    tests_changed: list[str]
    acceptance_criteria_ids: list[int]
    file_changes: list[FileChange]
    unified_diff: str = ""
    notes: list[str]
