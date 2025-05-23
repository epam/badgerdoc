from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional, Set
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
    def check_files_datasets_previous_jobs(cls, values):
        """
        Files and datasets and revisions should not be empty at the same time.
        """
        files = getattr(values, "files", None)
        datasets = getattr(values, "datasets", None)
        revisions = getattr(values, "revisions", None)
        previous_jobs = getattr(values, "previous_jobs", None)
        job_type = getattr(values, "job_type", None)

        if (
            not (bool(previous_jobs) ^ bool(files or datasets or revisions))
            and job_type != JobTypeEnumSchema.ImportJob
        ):
            raise ValueError(
                "Only one field must be specified: "
                "either previous_jobs or files/datasets/revisions"
            )
        return values

    @model_validator(mode="after")
    def check_users_and_validation(cls, values):
        """
        If the validation type is cross validation, annotators field should
        have min 2 annotators and validators field should be empty. If the
        validation type is hierarchical, annotators and validators should not
        be empty at the same time. If the validation type is validation_only,
        annotators field should be empty and validators field should not be
        empty.
        """
        validation_type, validators, annotators, extensive_coverage = (
            getattr(values, "validation_type", None),
            getattr(values, "validators", None),
            getattr(values, "annotators", None),
            getattr(values, "extensive_coverage", None),
        )
        job_type = getattr(values, "job_type", None)
        if job_type in AUTOMATIC_JOBS:
            if annotators or validators:
                raise ValueError(
                    f"If the job type is {job_type}, annotators and "
                    "validators field should be empty."
                )
            return values
        if validation_type == ValidationSchema.cross and (
            len(annotators) < CROSS_MIN_ANNOTATORS_NUMBER or validators
        ):
            raise ValueError(
                "If the validation type is cross validation, annotators "
                "field should have min 2 annotators and the validators field "
                "should be empty."
            )
        if validation_type == ValidationSchema.hierarchical and (
            not annotators or not validators
        ):
            raise ValueError(
                "If the validation type is hierarchical, annotators field "
                "and validators field should not be empty at the same time."
            )
        if validation_type == ValidationSchema.validation_only and (
            annotators or not validators
        ):
            raise ValueError(
                "If the validation type is validation_only, annotators field "
                "should be empty and validators field should not be empty."
            )
        if (
            validation_type == ValidationSchema.extensive_coverage
            and not extensive_coverage
        ):
            raise ValueError(
                "If the validation type is extensive_coverage value "
                "configuring this field should be provided to "
                "extensive_coverage parameter."
            )
        if validation_type == ValidationSchema.extensive_coverage and (
            len(annotators) < extensive_coverage
        ):
            raise ValueError(
                "If the validation type is extensive_coverage number of "
                "annotators should equal or less then provided "
                "extensive_coverage number."
            )
        return values


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
