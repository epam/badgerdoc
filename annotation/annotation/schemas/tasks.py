from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional, Self, Set
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskStatusEnumSchema(str, Enum):
    pending = "Pending"
    ready = "Ready"
    in_progress = "In Progress"
    finished = "Finished"


class AnnotationAndValidationActionsSchema(str, Enum):
    initial = "initial"
    auto = "auto"
    not_required = "not_required"


class AnnotationStatisticsEventEnumSchema(str, Enum):
    opened = "opened"
    closed = "closed"


class TaskStatusSchema(BaseModel):
    id: int = Field(..., examples=[4])
    status: TaskStatusEnumSchema = Field(
        TaskStatusEnumSchema.pending, examples=[TaskStatusEnumSchema.pending]
    )


class ManualAnnotationTaskInSchema(BaseModel):
    file_id: int = Field(..., examples=[2])
    pages: Set[int] = Field(
        ..., min_length=1, examples=[{1, 2, 3}]
    )  # type: ignore

    job_id: int = Field(..., examples=[3])
    user_id: UUID = Field(
        ..., examples=["4e9c5839-f63b-49c8-b918-614b87813e53"]
    )
    is_validation: bool = Field(default=False, examples=[False])
    deadline: Optional[datetime] = Field(
        None, examples=["2021-10-19 01:01:01"]
    )


class ManualAnnotationTaskSchema(
    ManualAnnotationTaskInSchema, TaskStatusSchema
):
    model_config = ConfigDict(from_attributes=True)


class NameSchema(BaseModel):
    id: int = Field(..., examples=[1])
    name: Optional[str] = Field(None, examples=["NameOfJobOrFile"])


class UserSchema(BaseModel):
    id: UUID = Field(..., examples=["3082242e-15e3-4e18-aad0-e3bf182b8550"])
    name: Optional[str] = Field(None, examples=["user_login"])


class ExpandedManualAnnotationTaskSchema(TaskStatusSchema):
    pages: Annotated[
        Set[Annotated[int, Field(ge=1)]],
        Field(min_length=1, examples=[{1, 2, 3}]),
    ]
    user: UserSchema
    is_validation: bool = Field(default=False, examples=[False])
    deadline: Optional[datetime] = Field(
        None, examples=["2021-10-19 01:01:01"]
    )
    file: NameSchema
    job: NameSchema


class PreviousAndNextTasksSchema(BaseModel):
    previous_task: Optional[ManualAnnotationTaskSchema] = None
    next_task: Optional[ManualAnnotationTaskSchema] = None


class TaskInfoSchema(BaseModel):
    user_ids: Set[UUID] = Field(
        ...,
        min_length=1,
        examples=[
            {
                "f0474853-f733-41c0-b897-90b788b822e3",
                "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
            }
        ],
    )
    files: Set[int] = Field(..., examples=[{1, 2, 3}])
    datasets: Set[int] = Field(..., examples=[{1, 2, 3}])
    job_id: int = Field(..., examples=[3])
    deadline: Optional[datetime] = Field(
        None, examples=["2021-10-19 01:01:01"]
    )

    @model_validator(mode="after")
    def both_fields_not_empty_check(self) -> Self:
        """
        Fields files and datasets should not be empty at the same time.
        """
        if not self.files and not self.datasets:
            raise ValueError(
                "Fields files and datasets should not "
                "be empty at the same time."
            )
        return self


class PagesInfoSchema(BaseModel):
    validated: Set[int] = Field(..., examples=[{1, 2, 3}])
    failed_validation_pages: Set[int] = Field(..., examples=[{4, 5}])
    annotated_pages: Set[int] = Field(..., examples=[{1, 2, 3, 4}])
    not_processed: Set[int] = Field(..., examples=[{6}])


class ValidationEndSchema(BaseModel):
    annotation_user_for_failed_pages: Optional[str] = Field(
        None, examples=[AnnotationAndValidationActionsSchema.initial]
    )
    validation_user_for_reannotated_pages: Optional[str] = Field(
        None, examples=[AnnotationAndValidationActionsSchema.auto]
    )


class TaskPatchSchema(BaseModel):
    file_id: Optional[int] = Field(None, examples=[2])
    pages: Optional[
        Annotated[
            Set[Annotated[int, Field(ge=1)]],
            Field(min_length=1, examples=[{1, 2, 3}]),
        ]
    ] = None
    job_id: Optional[int] = Field(None, examples=[3])
    user_id: Optional[UUID] = Field(
        None, examples=["4e9c5839-f63b-49c8-b918-614b87813e53"]
    )
    is_validation: Optional[bool] = Field(None, examples=[False])
    deadline: Optional[datetime] = Field(
        None, examples=["2021-10-19 01:01:01"]
    )


class AnnotationStatisticsInputSchema(BaseModel):
    event_type: AnnotationStatisticsEventEnumSchema = Field(
        ..., examples=[AnnotationStatisticsEventEnumSchema.opened]
    )
    additional_data: Optional[dict] = Field(
        None, examples=[{"attr1": "value1"}]
    )


class AnnotationStatisticsResponseSchema(AnnotationStatisticsInputSchema):
    task_id: int = Field(..., examples=[1])
    created: datetime = Field(..., examples=["2022-12-20 01:01:01"])
    updated: Optional[datetime] = Field(None, examples=["2022-12-20 01:01:01"])
    model_config = ConfigDict(from_attributes=True)


class AgreementScoreServiceInput(BaseModel):
    annotator_id: UUID = Field(
        ..., examples=["f0474853-f733-41c0-b897-90b788b822e3"]
    )
    job_id: int = Field(..., examples=[1])
    task_id: int = Field(..., examples=[1])
    s3_file_path: str = Field(..., examples=["files/1/1.pdf"])
    s3_file_bucket: str = Field(..., examples=["test"])
    s3_tokens_path: str = Field(..., examples=["files/1/ocr"])
    manifest_url: str = Field(..., examples=["annotation/2/1"])


class ExportTaskStatsInput(BaseModel):
    user_ids: List[UUID] = Field(
        ..., examples=[["e20af190-0f05-4cd8-ad51-811bfb19ad71"]]
    )
    date_from: datetime = Field(..., examples=["2020-12-20 01:01:01"])
    date_to: Optional[datetime] = Field(None, examples=["2025-12-20 01:01:01"])


class ResponseScore(BaseModel):
    task_id: int = Field(..., examples=[1])
    agreement_score: float = Field(..., examples=[0.89])


class AgreementScoreServiceResponse(BaseModel):
    annotator_id: UUID = Field(
        ..., examples=["f0474853-f733-41c0-b897-90b788b822e3"]
    )
    job_id: int = Field(..., examples=[1])
    task_id: int = Field(..., examples=[1])
    agreement_score: List[ResponseScore] = Field(...)


class TaskMetric(BaseModel):
    task_from_id: int = Field(..., examples=[1])
    task_to_id: int = Field(..., examples=[1])
    metric_score: float = Field(..., examples=[0.78])


class AgreementScoreComparingResult(BaseModel):
    agreement_score_reached: bool = Field(..., examples=[True])
    task_metrics: List[TaskMetric] = Field(...)
