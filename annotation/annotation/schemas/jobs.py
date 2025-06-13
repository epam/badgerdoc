from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional, Self, Set
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

DEFAULT_LOAD = 100
CROSS_MIN_ANNOTATORS_NUMBER = 2


class JobTypeEnumSchema(str, Enum):
    ExtractionJob = "ExtractionJob"
    ExtractionWithAnnotationJob = "ExtractionWithAnnotationJob"
    AnnotationJob = "AnnotationJob"
    ImportJob = "ImportJob"


AUTOMATIC_JOBS = [JobTypeEnumSchema.ExtractionJob, JobTypeEnumSchema.ImportJob]


class JobStatusEnumSchema(str, Enum):
    pending = "Pending"
    in_progress = "In Progress"
    finished = "Finished"
    failed = "Failed"


class ValidationSchema(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"
    validation_only = "validation only"
    extensive_coverage = "extensive_coverage"


class PreviousJobInfoSchema(BaseModel):
    job_id: int
    files: Set[int]
    datasets: Set[int]


class JobInfoSchema(BaseModel):
    callback_url: str = Field(..., examples=["http://jobs/jobs/1"])
    name: str = Field(None, examples=["job_name"])
    annotators: Set[UUID] = Field(
        ...,
        examples=[
            {
                "f0474853-f733-41c0-b897-90b788b822e3",
                "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
            }
        ],
    )
    validators: Set[UUID] = Field(
        ...,
        examples=[
            {
                "f0474853-f733-41c0-b897-90b788b822e3",
                "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
            }
        ],
    )
    owners: Set[UUID] = Field(
        ...,
        examples=[
            {
                "f0474853-f733-41c0-b897-90b788b822e3",
                "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
            }
        ],
    )
    validation_type: ValidationSchema = Field(
        default=ValidationSchema.cross, examples=[ValidationSchema.cross]
    )
    files: Set[int] = Field(..., examples=[{1, 2, 3}])
    datasets: Set[int] = Field(..., examples=[{1, 2, 3}])
    revisions: Set[str] = Field(
        set(),
        examples=[
            {
                "35b7b50a056d00048b0977b195f7f8e9f9f7400f",
                "4dc503a9ade7d7cb55d6be671748a312d663bb0a",
            }
        ],
    )
    previous_jobs: List[PreviousJobInfoSchema] = Field(...)
    is_auto_distribution: bool = Field(default=False, examples=[False])
    categories: Optional[Set[str]] = Field(None, examples=[{"1", "2"}])
    deadline: Optional[datetime] = Field(
        None, examples=["2021-10-19 01:01:01"]
    )
    job_type: JobTypeEnumSchema = Field(
        ..., examples=[JobTypeEnumSchema.ExtractionJob]
    )
    extensive_coverage: int = Field(
        1,
        examples=[1],
    )

    @model_validator(mode="after")
    def check_files_datasets_previous_jobs(self) -> Self:
        """
        Ensure either previous_jobs or files/datasets/revisions is specified,
        but not both, except for specific job types.
        """
        if (
            not (
                bool(self.previous_jobs)
                ^ bool(self.files or self.datasets or self.revisions)
            )
            and self.job_type != "ImportJob"
            # Assuming JobTypeEnumSchema.ImportJob
            # resolves as a string "ImportJob"
        ):
            raise ValueError(
                "Only one field must be specified: "
                "either previous_jobs or files/datasets/revisions"
            )
        return self

    @model_validator(mode="after")
    def check_users_and_validation(self) -> Self:
        """
        Validate constraints on annotators and
        validators depending on validation_type.
        """
        if self.job_type in AUTOMATIC_JOBS:
            if self.annotators or self.validators:
                raise ValueError(
                    f"If the job type is {self.job_type}, annotators and "
                    "validators field should be empty."
                )
            return self
        if self.validation_type == ValidationSchema["cross"] and (
            len(self.annotators) < CROSS_MIN_ANNOTATORS_NUMBER
            or self.validators
        ):
            raise ValueError(
                "If the validation type is cross validation, annotators "
                "field should have min 2 annotators and the validators field "
                "should be empty."
            )
        if self.validation_type == ValidationSchema["hierarchical"] and (
            not self.annotators or not self.validators
        ):
            raise ValueError(
                "If the validation type is hierarchical, annotators field "
                "and validators field should not be empty at the same time."
            )
        if self.validation_type == ValidationSchema["validation_only"] and (
            self.annotators or not self.validators
        ):
            raise ValueError(
                "If the validation type is validation_only, annotators field "
                "should be empty and validators field should not be empty."
            )
        if (
            self.validation_type == ValidationSchema["extensive_coverage"]
            and not self.extensive_coverage
        ):
            raise ValueError(
                "If the validation type is extensive_coverage, "
                "a value for this parameter must be specified."
            )
        if self.validation_type == ValidationSchema["extensive_coverage"] and (
            len(self.annotators) < self.extensive_coverage
        ):
            raise ValueError(
                "If the validation type is extensive_coverage, the number of "
                "annotators must be equal to or greater than the provided "
                "extensive_coverage number."
            )
        return self


class JobPatchOutSchema(BaseModel):
    annotators: Set[UUID] = Field(
        None,
        examples=[{"f0474853-f733-41c0-b897-90b788b822e3"}],
    )
    validators: Set[UUID] = Field(
        None,
        examples=[{"b44156f8-e634-48a6-b5f3-c8b1462a2d67"}],
    )
    categories: Set[str] = Field(None, examples=[{"1", "2"}])


class JobPatchSchema(JobPatchOutSchema):
    callback_url: str = Field(None, examples=["http://jobs/jobs/1"])
    name: str = Field(None, examples=["job_name"])
    owners: Set[UUID] = Field(
        None,
        examples=[{"b44156f8-e634-48a6-b5f3-c8b1462a2d67"}],
    )
    files: Set[int] = Field(None, examples=[{1, 2, 3}])
    datasets: Set[int] = Field(None, examples=[{1, 2, 3}])
    deadline: datetime = Field(None, examples=["2021-10-19 01:01:01"])
    extensive_coverage: int = Field(None, examples=[1])


class JobOutSchema(BaseModel):
    job_id: int = Field(..., examples=[1])
    is_manual: bool = Field(..., examples=[True])


class FileStatusEnumSchema(str, Enum):
    pending = "Pending"
    annotated = "Annotated"
    validated = "Validated"


class FileInfoSchema(BaseModel):
    id: int = Field(..., examples=[1])
    status: FileStatusEnumSchema = Field(
        ..., examples=[FileStatusEnumSchema.pending]
    )


class JobFilesInfoSchema(BaseModel):
    tenant: str = Field(..., examples=["test"])
    job_id: int = Field(..., examples=[1])
    total_objects: int = Field(..., examples=[10])
    current_page: int = Field(..., examples=[1])
    page_size: int = Field(..., examples=[50])
    files: List[FileInfoSchema]


class UnassignedFileSchema(BaseModel):
    id: int = Field(..., examples=[1])
    pages_to_annotate: Annotated[
        Set[Annotated[int, Field(ge=1)]], Field(examples=[{1, 2, 3}])
    ]

    pages_to_validate: Annotated[
        Set[Annotated[int, Field(ge=1)]], Field(examples=[{1, 2, 3}])
    ]


class UnassignedFilesInfoSchema(BaseModel):
    tenant: str = Field(..., examples=["test"])
    job_id: int = Field(..., examples=[1])
    total_objects: int = Field(..., examples=[1])
    current_page: int = Field(..., examples=[1])
    page_size: int = Field(..., examples=[50])
    unassigned_files: List[UnassignedFileSchema]


class JobProgressSchema(BaseModel):
    finished: int = Field(..., examples=[1])
    total: int = Field(..., examples=[1])
