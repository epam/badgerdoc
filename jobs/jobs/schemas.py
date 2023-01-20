from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField


class JobType(str, Enum):
    ExtractionJob = "ExtractionJob"
    ExtractionWithAnnotationJob = "ExtractionWithAnnotationJob"
    AnnotationJob = "AnnotationJob"
    ImportJob = "ImportJob"


class JobMode(str, Enum):
    Automatic = "Automatic"
    Manual = "Manual"


class Status(str, Enum):
    pending = "Pending"
    in_progress = "In Progress"
    failed = "Failed"
    finished = "Finished"
    ready_for_annotation = "Ready For Annotation"
    draft = "Draft"


class ValidationType(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"
    validation_only = "validation only"
    extensive_coverage = "extensive_coverage"


class ExtractionJobParams(BaseModel):
    name: str
    type: JobType = JobType.ExtractionJob
    mode: JobMode = JobMode.Automatic
    files: List[int]
    datasets: List[int]
    pipeline_name: str
    pipeline_version: Optional[str]
    is_draft: bool = False


class AnnotationJobParams(BaseModel):
    name: str
    type: JobType = JobType.AnnotationJob
    mode: JobMode = JobMode.Manual
    datasets: Optional[List[int]]
    files: Optional[List[int]]
    annotators: List[str]
    validators: List[str]
    owners: List[str]
    categories: List[str]
    is_auto_distribution: bool = False
    deadline: datetime
    validation_type: ValidationType
    is_draft: bool = False
    extensive_coverage: int = 1


class ExtractionWithAnnotationJobParams(
    ExtractionJobParams, AnnotationJobParams
):
    start_manual_job_automatically: Optional[bool] = True


class ImportJobParams(BaseModel):
    name: str
    type: JobType = JobType.ImportJob
    import_source: Optional[str]
    import_format: Optional[str]
    files: Optional[List[int]]


class CategoryLinkInput(BaseModel):
    category_id: str = Field(..., example="123abc")
    taxonomy_id: str = Field(..., example="my_taxonomy_id")
    taxonomy_version: Optional[int] = Field(..., example=1)


class CategoryLinkParams(CategoryLinkInput):
    job_id: str = Field(..., example="123abc")


class JobParams(BaseModel):
    # ---- common attributes ---- #
    name: str
    type: JobType
    files: Optional[List[int]]
    datasets: Optional[List[int]]
    is_draft: bool = False
    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    is_auto_distribution: Optional[bool] = False
    validation_type: Optional[ValidationType]
    annotators: Optional[List[str]]
    owners: Optional[List[str]]
    categories: Optional[List[Union[str, CategoryLinkInput]]]
    deadline: Optional[datetime]
    validators: Optional[List[str]]
    extensive_coverage: Optional[int]
    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    pipeline_name: Optional[str]
    pipeline_version: Optional[str] = None
    # ---- ExtractionWithAnnotationJob attributes ---- #
    start_manual_job_automatically: Optional[bool] = True
    # ----- ImportJob attributes ---- #
    import_source: Optional[str]
    import_format: Optional[str]

    # ---- common attributes ---- #
    @validator("datasets", always=True)
    def check_files_and_datasets_are_not_empty(  # pylint: disable=no-self-argument  # noqa: E501
        cls, v: List[int], values: Dict[str, Any]
    ) -> List[int]:
        if not values.get("type") == JobType.ImportJob:
            if not v and not values.get("files"):
                raise ValueError(
                    "files and datasets cannot be empty at the same time"
                )
        return v

    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    @validator("is_auto_distribution", always=True)
    def check_is_auto_distribution(  # pylint: disable=no-self-argument
        cls, v: bool, values: Dict[str, Any]
    ) -> bool:
        if values.get("type") == JobType.ExtractionJob and v:
            raise ValueError(
                "is_auto_distribution cannot be assigned to ExtractionJob"
            )
        return v

    @validator(
        "validation_type",
        "owners",
        "categories",
        always=True,
    )  # pylint: disable=no-self-argument
    def check_annotationjob_attributes(
        cls,
        v: Union[List[str], List[Union[str, CategoryLinkInput]]],
        values: Dict[str, Any],
        field: ModelField,
    ) -> Union[List[int], List[str]]:
        job_type = values.get("type")
        if v:
            if job_type == JobType.ExtractionJob:
                raise ValueError(
                    f"{field.name} cannot be assigned to ExtractionJob"
                )
        elif job_type == JobType.AnnotationJob:
            raise ValueError(f"{field.name} cannot be empty for {job_type}")

        return v

    @validator("annotators")
    def check_annotators(  # pylint: disable=no-self-argument
        cls, v: List[str], values: Dict[str, Any], field: ModelField
    ) -> List[str]:
        job_type = values.get("type")
        validation_type = values.get("validation_type")
        if job_type == JobType.ExtractionJob:
            raise ValueError(
                f"{field.name} cannot be assigned to ExtractionJob"
            )

        require_annotators = {
            ValidationType.hierarchical,
            ValidationType.cross,
        }
        if v and validation_type == ValidationType.validation_only:
            raise ValueError(
                f"{field.name} should be empty with {validation_type=}"
            )

        elif not v and validation_type in require_annotators:
            raise ValueError(
                f"{field.name} cannot be empty with {validation_type=}"
            )

        elif len(v) < 2 and validation_type == ValidationType.cross:
            raise ValueError(
                f"{field.name} should include at least 2 annotators "
                f"with {validation_type=}"
            )

        return v

    @validator("validators")
    def check_validators(  # pylint: disable=no-self-argument
        cls, v: List[str], values: Dict[str, Any], field: ModelField
    ) -> List[str]:
        job_type = values.get("type")
        validation_type = values.get("validation_type")

        if job_type == JobType.ExtractionJob:
            raise ValueError(
                f"{field.name} cannot be assigned to ExtractionJob"
            )

        if (
            validation_type
            in [ValidationType.hierarchical, ValidationType.validation_only]
            and not v
        ):
            raise ValueError(
                f"{field.name} cannot be empty with {validation_type=}"
            )

        if validation_type == ValidationType.cross and v:
            raise ValueError(
                f"{field.name} should be empty with {validation_type=}"
            )

        return v

    @validator("import_source", "import_format", always=True)
    def check_import_job_attributes(  # pylint: disable=no-self-argument
        cls, v: str, values: Dict[str, Any], field: ModelField
    ) -> str:
        job_type = values.get("type")
        if job_type != JobType.ImportJob and v:
            raise ValueError(f"{field.name} cannot be assigned to {job_type}")
        if job_type == JobType.ImportJob and not v:
            raise ValueError(
                f"{field.name} cannot be empty in {JobType.ImportJob}"
            )
        return v

    @validator("extensive_coverage")
    def check_extensive_coverage(
        cls, v: int, values: Dict[str, Any], field: ModelField
    ):
        validation_type = values.get("validation_type")
        if validation_type != ValidationType.extensive_coverage and v:
            raise ValueError(
                f"{field.name} cannot be assigned to {validation_type}."
            )
        if validation_type != ValidationType.extensive_coverage and not v:
            raise ValueError(
                f"{field.name} cannot be empty with {validation_type=}."
            )
        annotators = values.get("annotators")
        if v > len(annotators):
            raise ValueError(
                f"{field.name} cannot be less then number of annotators."
            )
        return v

    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    @validator("pipeline_name", always=True)
    def check_pipeline_name(  # pylint: disable=no-self-argument
        cls, v: str, values: Dict[str, Any]
    ) -> str:
        if values.get("type") == JobType.AnnotationJob and v:
            raise ValueError(
                "pipeline_name cannot be assigned to AnnotationJob"
            )
        if (
            values.get("type") == JobType.ExtractionJob
            or values.get("type") == JobType.ExtractionWithAnnotationJob
        ) and not v:
            raise ValueError(
                f'pipeline cannot be empty for {values.get("type")}'
            )
        return v


class JobParamsToChange(BaseModel):
    name: Optional[str]
    type: Optional[JobType]
    files: Optional[List[int]]
    datasets: Optional[List[int]]
    status: Optional[Status]
    is_draft: Optional[bool]
    mode: Optional[JobMode]
    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    is_auto_distribution: Optional[bool]
    annotators: Optional[List[str]]
    validators: Optional[List[str]]
    owners: Optional[List[str]]
    categories: Optional[List[Union[str, CategoryLinkInput]]]
    deadline: Optional[datetime]
    validation_type: Optional[ValidationType]
    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    pipeline_id: Optional[int]
    # ----- ImportJob attributes ---- #
    import_source: Optional[str]
    import_format: Optional[str]


class AnnotationJobUpdateParamsInAnnotation(BaseModel):
    datasets: Optional[List[int]]
    files: Optional[List[int]]
    annotators: Optional[List[str]]
    validators: Optional[List[str]]
    owners: Optional[List[str]]
    categories: Optional[List[str]]
    deadline: Optional[datetime]


class JobProgress(BaseModel):
    finished: int = Field(..., example=1)
    total: int = Field(..., example=1)
    mode: str = Field(..., example="Automatic")
