from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo


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


# Other states exist but can be added if needed.
class AirflowPipelineStatus(str, Enum):
    running = "running"
    queued = "queued"
    success = "success"
    failed = "failed"


class ValidationType(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"
    validation_only = "validation only"
    extensive_coverage = "extensive_coverage"


class CategoryLinkInput(BaseModel):
    category_id: str = Field(..., examples=["123abc"])
    taxonomy_id: str = Field(..., examples=["my_taxonomy_id"])
    taxonomy_version: Optional[int] = Field(..., examples=[1])


class CategoryLinkParams(CategoryLinkInput):
    job_id: str = Field(..., examples=["123abc"])


class ExtractionJobParams(BaseModel):
    name: str
    type: JobType = JobType.ExtractionJob
    mode: JobMode = JobMode.Automatic
    files: List[int] = []
    datasets: List[int] = []
    previous_jobs: Optional[List[int]] = []
    revisions: Set[str] = set()
    pipeline_name: str
    pipeline_version: Optional[str] = None
    pipeline_engine: Optional[str] = None
    is_draft: bool = False
    categories: Optional[List[str]] = None


class AvailableAnnotationTypes(str, Enum):
    box = "box"
    text = "text"
    free_box = "free-box"
    table = "table"


class AvailableLinkTypes(str, Enum):
    chain = "chain"
    all_to_all = "all to all"


class AnnotationJobParams(BaseModel):
    name: str
    type: JobType = JobType.AnnotationJob
    mode: JobMode = JobMode.Manual
    files: Optional[List[int]] = []
    datasets: Optional[List[int]] = []
    previous_jobs: Optional[List[int]] = []
    revisions: Set[str] = set()
    annotators: List[str]
    validators: List[str]
    owners: List[str]
    categories: List[str]
    available_annotation_types: List[AvailableAnnotationTypes] = []
    available_link_types: List[AvailableLinkTypes] = []
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
    import_source: Optional[str] = None
    import_format: Optional[str] = None


class JobParams(BaseModel):
    # ---- common attributes ---- #
    name: str
    type: JobType
    files: Optional[List[int]] = []
    datasets: Optional[List[int]] = []
    revisions: Set[str] = set()
    previous_jobs: Optional[List[int]] = []
    is_draft: bool = False
    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    is_auto_distribution: Optional[bool] = False
    validation_type: Optional[ValidationType] = None
    annotators: Optional[List[str]] = None
    owners: Optional[List[str]] = None
    categories: Optional[List[Union[str, CategoryLinkInput]]] = None
    available_annotation_types: List[AvailableAnnotationTypes] = []
    available_link_types: List[AvailableLinkTypes] = []
    deadline: Optional[datetime] = None
    validators: Optional[List[str]] = None
    extensive_coverage: Optional[int] = None
    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    pipeline_name: Optional[str] = None
    pipeline_id: Optional[str] = None
    pipeline_engine: Optional[str] = Field(default="airflow")
    pipeline_version: Optional[str] = None
    # ---- ExtractionWithAnnotationJob attributes ---- #
    start_manual_job_automatically: Optional[bool] = True
    # ----- ImportJob attributes ---- #
    import_source: Optional[str] = None
    import_format: Optional[str] = None

    # ---- common attributes ---- #
    @field_validator("previous_jobs", mode="before")
    @classmethod
    def check_files_datasets_previous_jobs(  # pylint: disable=no-self-argument  # noqa: E501
        cls, v: List[int], info: FieldValidationInfo
    ) -> List[int]:
        if info.data.get("type") != JobType.ImportJob:
            files = info.data.get("files")
            datasets = info.data.get("datasets")
            revisions = info.data.get("revisions")
            assert bool(v) ^ bool(files or datasets or revisions), (
                "Only one field must be specified: "
                "either previous_jobs or files/datasets/revisions"
            )

        return v

    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    @field_validator("is_auto_distribution", mode="before")
    @classmethod
    def check_is_auto_distribution(  # pylint: disable=no-self-argument
        cls, v: bool, info: FieldValidationInfo
    ) -> bool:
        if info.data.get("type") == JobType.ExtractionJob and v:
            raise ValueError(
                "is_auto_distribution cannot be assigned to ExtractionJob"
            )
        return v

    @field_validator(
        "validation_type",
        "owners",
        mode="before",
    )  # pylint: disable=no-self-argument
    def check_annotationjob_attributes(
        cls,
        v: Union[List[str], List[Union[str, CategoryLinkInput]]],
        info: FieldValidationInfo,
    ) -> Union[List[int], List[str]]:
        job_type = info.data.get("type")
        if not v and job_type == JobType.AnnotationJob:
            raise ValueError(f"{info.name} cannot be empty for {job_type}")

        return v

    # @validator(
    #     "categories",
    #     always=True,
    # )  # pylint: disable=no-self-argument
    # def check_categories_for_annotationjob_attributes(
    #     cls,
    #     v: Union[List[str], List[Union[str, CategoryLinkInput]]],
    #     values: Dict[str, Any],
    #     field: ModelField,
    # ) -> Union[List[int], List[str]]:
    #     job_type = values.get("type")
    #     if v:
    #         if job_type == JobType.ExtractionJob:
    #             raise ValueError(
    #                 f"{field.name} cannot be assigned to ExtractionJob"
    #             )
    #     elif job_type == JobType.AnnotationJob:
    #         raise ValueError(f"{field.name} should be passed for {job_type}")

    #     return v

    @field_validator("annotators", mode="before")
    @classmethod
    def check_annotators(  # pylint: disable=no-self-argument
        cls, v: List[str], info: FieldValidationInfo
    ) -> List[str]:
        job_type = info.data.get("type")
        validation_type = info.data.get("validation_type")
        if job_type == JobType.ExtractionJob and v:
            raise ValueError(
                f"{info.name} cannot be assigned to ExtractionJob"
            )

        require_annotators = {
            ValidationType.hierarchical,
            ValidationType.cross,
        }
        if v and validation_type == ValidationType.validation_only:
            raise ValueError(
                f"{info.name} should be empty with {validation_type=}"
            )

        elif not v and validation_type in require_annotators:
            raise ValueError(
                f"{info.name} cannot be empty with {validation_type=}"
            )

        elif len(v) < 2 and validation_type == ValidationType.cross:
            raise ValueError(
                f"{info.name} should include at least 2 annotators "
                f"with {validation_type=}"
            )

        return v

    @field_validator("validators", mode="before")
    @classmethod
    def check_validators(  # pylint: disable=no-self-argument
        cls, v: List[str], info: FieldValidationInfo
    ) -> List[str]:
        job_type = info.data.get("type")
        validation_type = info.data.get("validation_type")

        if job_type == JobType.ExtractionJob and v:
            raise ValueError(
                f"{info.name} cannot be assigned to ExtractionJob"
            )

        if (
            validation_type
            in [
                ValidationType.hierarchical,
                ValidationType.validation_only,
                ValidationType.extensive_coverage,
            ]
            and not v
        ):
            raise ValueError(
                f"{info.name} cannot be empty with {validation_type=}"
            )

        if validation_type == ValidationType.cross and v:
            raise ValueError(
                f"{info.name} should be empty with {validation_type=}"
            )

        return v

    @field_validator("import_source", "import_format", mode="before")
    @classmethod
    def check_import_job_attributes(  # pylint: disable=no-self-argument
        cls, v: str, info: FieldValidationInfo
    ) -> str:
        job_type = info.data.get("type")
        if job_type != JobType.ImportJob and v:
            raise ValueError(f"{info.name} cannot be assigned to {job_type}")
        if job_type == JobType.ImportJob and not v:
            raise ValueError(
                f"{info.name} cannot be empty in {JobType.ImportJob}"
            )
        return v

    @field_validator("extensive_coverage", mode="before")
    @classmethod
    def check_extensive_coverage(cls, v: int, info: FieldValidationInfo):
        validation_type = info.data.get("validation_type")
        if validation_type != ValidationType.extensive_coverage and v:
            raise ValueError(
                f"{info.name} cannot be assigned to {validation_type}."
            )
        if validation_type != ValidationType.extensive_coverage and not v:
            raise ValueError(
                f"{info.name} cannot be empty with {validation_type=}."
            )
        annotators = info.data.get("annotators")
        if v > len(annotators):
            raise ValueError(
                f"{info.name} cannot be less then number of annotators."
            )
        return v

    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    @field_validator("pipeline_name", mode="before")
    @classmethod
    def check_pipeline_name(  # pylint: disable=no-self-argument
        cls, v: str, info: FieldValidationInfo
    ) -> str:
        if info.data.get("type") == JobType.AnnotationJob and v:
            raise ValueError(
                "pipeline_name cannot be assigned to AnnotationJob"
            )
        if (
            info.data.get("type") == JobType.ExtractionJob
            or info.data.get("type") == JobType.ExtractionWithAnnotationJob
        ) and not v:
            raise ValueError(
                f'pipeline cannot be empty for {info.data.get("type")}'
            )
        return v


class JobParamsToChange(BaseModel):
    name: Optional[str] = None
    type: Optional[JobType] = None
    files: Optional[List[int]] = []
    datasets: Optional[List[int]] = []
    previous_jobs: Optional[List[int]] = []
    status: Optional[Status] = None
    is_draft: Optional[bool] = None
    mode: Optional[JobMode] = None
    # ---- AnnotationJob and ExtractionWithAnnotationJob attributes ---- #
    is_auto_distribution: Optional[bool] = None
    annotators: Optional[List[str]] = None
    validators: Optional[List[str]] = None
    owners: Optional[List[str]] = None
    categories: Optional[List[Union[str, CategoryLinkInput]]] = None
    categories_append: Optional[List[Union[str, CategoryLinkInput]]] = None
    deadline: Optional[datetime] = None
    validation_type: Optional[ValidationType] = None
    extensive_coverage: Optional[int] = None
    # ---- ExtractionJob and ExtractionWithAnnotationJob attributes ---- #
    pipeline_id: Optional[int] = None
    # ----- ImportJob attributes ---- #
    import_source: Optional[str] = None
    import_format: Optional[str] = None


class AnnotationJobUpdateParamsInAnnotation(BaseModel):
    files: Optional[List[int]] = []
    datasets: Optional[List[int]] = []
    previous_jobs: Optional[List[int]] = []
    annotators: Optional[List[str]] = None
    validators: Optional[List[str]] = None
    owners: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    extensive_coverage: Optional[int] = None


class JobProgress(BaseModel):
    finished: int = Field(..., examples=[1])
    total: int = Field(..., examples=[1])
    mode: str = Field(..., examples=["Automatic"])


class PipelineEngine(BaseModel):
    name: str
    resource: str
    enabled: bool


class PipelineEngineSupport(BaseModel):
    data: List[PipelineEngine]


class Pipeline(BaseModel):
    id: str
    name: str
    version: int = Field(default=0)
    type: str = Field(default="airflow")
    date: datetime
    meta: Dict[str, Any]
    steps: List[Any] = Field(default_factory=list)


class Pipelines(BaseModel):
    data: List[Pipeline]
