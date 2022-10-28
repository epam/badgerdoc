from datetime import datetime
from enum import Enum
from typing import List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field, root_validator

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


class JobInfoSchema(BaseModel):
    callback_url: str = Field(..., example="http://jobs/jobs/1")
    name: str = Field(None, example="job_name")
    annotators: Set[UUID] = Field(
        ...,
        example={
            "f0474853-f733-41c0-b897-90b788b822e3",
            "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
        },
    )
    validators: Set[UUID] = Field(
        ...,
        example={
            "f0474853-f733-41c0-b897-90b788b822e3",
            "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
        },
    )
    owners: Set[UUID] = Field(
        ...,
        example={
            "f0474853-f733-41c0-b897-90b788b822e3",
            "b44156f8-e634-48a6-b5f3-c8b1462a2d67",
        },
    )
    validation_type: ValidationSchema = Field(
        default=ValidationSchema.cross, example=ValidationSchema.cross
    )
    files: Set[int] = Field(..., example={1, 2, 3})
    datasets: Set[int] = Field(..., example={1, 2, 3})
    is_auto_distribution: bool = Field(default=False, example=False)
    categories: Set[str] = Field(..., example={"1", "2"})
    deadline: Optional[datetime] = Field(None, example="2021-10-19 01:01:01")
    job_type: JobTypeEnumSchema = Field(
        ..., example=JobTypeEnumSchema.ExtractionJob
    )

    @root_validator
    def check_files_and_datasets(cls, values):
        """
        Files and datasets should not be empty at the same time.
        """
        files, datasets = values.get("files"), values.get("datasets")
        job_type = values.get("job_type")
        if (
            not files and not datasets
        ) and job_type != JobTypeEnumSchema.ImportJob:
            raise ValueError(
                "Fields files and datasets should "
                "not be empty at the same time."
            )
        return values

    @root_validator
    def check_users_and_validation(cls, values):
        """
        If the validation type is cross validation, annotators field should
        have min 2 annotators and validators field should be empty. If the
        validation type is hierarchical, annotators and validators should not
        be empty at the same time. If the validation type is validation_only,
        annotators field should be empty and validators field should not be
        empty.
        """
        validation_type, validators, annotators = (
            values.get("validation_type"),
            values.get("validators"),
            values.get("annotators"),
        )
        job_type = values.get("job_type")
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
        return values

    @root_validator
    def check_categories(cls, values):
        """
        If job type is ImportJob categories may not be provided.
        In other cases there should be not less than one category provided
        """
        job_type = values.get("job_type")
        categories = values.get("categories")
        if job_type != JobTypeEnumSchema.ImportJob and not categories:
            raise ValueError(
                "There should be not less than one category provided"
            )
        return values


class JobPatchSchema(BaseModel):
    callback_url: str = Field(None, example="http://jobs/jobs/1")
    name: str = Field(None, example="job_name")
    annotators: Set[UUID] = Field(
        None,
        example={"f0474853-f733-41c0-b897-90b788b822e3"},
    )
    validators: Set[UUID] = Field(
        None,
        example={"b44156f8-e634-48a6-b5f3-c8b1462a2d67"},
    )
    owners: Set[UUID] = Field(
        None,
        example={"b44156f8-e634-48a6-b5f3-c8b1462a2d67"},
    )
    files: Set[int] = Field(None, example={1, 2, 3})
    datasets: Set[int] = Field(None, example={1, 2, 3})
    categories: Set[str] = Field(None, example={"1", "2"})
    deadline: datetime = Field(None, example="2021-10-19 01:01:01")


class JobOutSchema(BaseModel):
    job_id: int = Field(..., example=1)
    is_manual: bool = Field(..., example=True)


class FileStatusEnumSchema(str, Enum):
    pending = "Pending"
    annotated = "Annotated"
    validated = "Validated"


class FileInfoSchema(BaseModel):
    id: int = Field(..., example=1)
    status: FileStatusEnumSchema = Field(
        ..., example=FileStatusEnumSchema.pending
    )


class JobFilesInfoSchema(BaseModel):
    tenant: str = Field(..., example="test")
    job_id: int = Field(..., example=1)
    total_objects: int = Field(..., example=10)
    current_page: int = Field(..., example=1)
    page_size: int = Field(..., example=50)
    files: List[FileInfoSchema]


class UnassignedFileSchema(BaseModel):
    id: int = Field(..., example=1)
    pages_to_annotate: Set[int] = Field(..., ge=1, example={1, 2, 3})
    pages_to_validate: Set[int] = Field(..., ge=1, example={1, 2, 3})


class UnassignedFilesInfoSchema(BaseModel):
    tenant: str = Field(..., example="test")
    job_id: int = Field(..., example=1)
    total_objects: int = Field(..., example=1)
    current_page: int = Field(..., example=1)
    page_size: int = Field(..., example=50)
    unassigned_files: List[UnassignedFileSchema]


class JobProgressSchema(BaseModel):
    finished: int = Field(..., example=1)
    total: int = Field(..., example=1)
