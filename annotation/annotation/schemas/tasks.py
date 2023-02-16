from datetime import datetime
from enum import Enum
from typing import Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field, root_validator


class TaskStatusEnumSchema(str, Enum):
    pending = "Pending"
    ready = "Ready"
    in_progress = "In Progress"
    finished = "Finished"


class AnnotationAndValidationActionsSchema(str, Enum):
    initial = "initial"
    auto = "auto"
    not_required = "not_required"


class TaskStatusSchema(BaseModel):
    id: int = Field(..., example=4)
    status: TaskStatusEnumSchema = Field(
        TaskStatusEnumSchema.pending, example=TaskStatusEnumSchema.pending
    )


class ManualAnnotationTaskInSchema(BaseModel):
    file_id: int = Field(..., example=2)
    pages: Set[int] = Field(
        ..., ge=1, min_items=1, example={1, 2, 3}
    )  # type: ignore
    job_id: int = Field(..., example=3)
    user_id: UUID = Field(..., example="4e9c5839-f63b-49c8-b918-614b87813e53")
    is_validation: bool = Field(default=False, example=False)
    deadline: Optional[datetime] = Field(None, example="2021-10-19 01:01:01")


class ManualAnnotationTaskSchema(
    ManualAnnotationTaskInSchema, TaskStatusSchema
):
    class Config:
        orm_mode = True


class NameSchema(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(None, example="NameOfJobOrFile")


class ExpandedManualAnnotationTaskSchema(TaskStatusSchema):
    pages: Set[int] = Field(
        ..., ge=1, min_items=1, example={1, 2, 3}
    )  # type: ignore
    user_id: UUID = Field(..., example="3082242e-15e3-4e18-aad0-e3bf182b8550")
    is_validation: bool = Field(default=False, example=False)
    deadline: Optional[datetime] = Field(None, example="2021-10-19 01:01:01")
    file: NameSchema
    job: NameSchema


class TaskInfoSchema(BaseModel):
    user_ids: Set[UUID] = Field(
        ...,
        min_items=1,
        example={
            "f0474853-f733-41c0-b897-90b788b822e3",
            "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
        },
    )
    files: Set[int] = Field(..., example={1, 2, 3})
    datasets: Set[int] = Field(..., example={1, 2, 3})
    job_id: int = Field(..., example=3)
    deadline: Optional[datetime] = Field(None, example="2021-10-19 01:01:01")

    @root_validator
    def both_fields_not_empty_check(cls, values):
        """
        Fields files and datasets should not be empty at
        the same time.
        """
        files, datasets = values.get("files"), values.get("datasets")
        if not files and not datasets:
            raise ValueError(
                "Fields files and datasets should "
                "not be empty at the same time."
            )
        return values


class PagesInfoSchema(BaseModel):
    validated: Set[int] = Field(..., example={1, 2, 3})
    failed_validation_pages: Set[int] = Field(..., example={4, 5})
    annotated_pages: Set[int] = Field(..., example={1, 2, 3, 4})
    not_processed: Set[int] = Field(..., example={6})


class ValidationEndSchema(BaseModel):
    annotation_user_for_failed_pages: Optional[str] = Field(
        None, example=AnnotationAndValidationActionsSchema.initial
    )
    validation_user_for_reannotated_pages: Optional[str] = Field(
        None, example=AnnotationAndValidationActionsSchema.auto
    )


class TaskPatchSchema(BaseModel):
    file_id: Optional[int] = Field(None, example=2)
    pages: Optional[Set[int]] = Field(
        None, ge=1, min_items=1, example={1, 2, 3}
    )
    job_id: Optional[int] = Field(None, example=3)
    user_id: Optional[UUID] = Field(
        None, example="4e9c5839-f63b-49c8-b918-614b87813e53"
    )
    is_validation: Optional[bool] = Field(None, example=False)
    deadline: Optional[datetime] = Field(None, example="2021-10-19 01:01:01")
