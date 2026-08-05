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
    acceptance_criteria_ids: list[int]
    file_changes: list[FileChange]
    unified_diff: str = ""
    notes: list[str]

    @property
    def modified_files(self) -> list[str]:
        return [
            change.path
            for change in self.file_changes
            if change.operation == FileOperation.MODIFY
        ]

    @property
    def created_files(self) -> list[str]:
        return [
            change.path
            for change in self.file_changes
            if change.operation == FileOperation.CREATE
        ]

    @property
    def tests_changed(self) -> list[str]:
        test_files: list[str] = []
        for change in self.file_changes:
            file_name = change.path.rsplit("/", 1)[-1]
            path_parts = change.path.split("/")
            if (
                "tests" in path_parts
                or file_name.startswith("test_")
                or file_name.endswith("_test.py")
            ):
                test_files.append(change.path)
        return test_files
