from __future__ import annotations

import urllib.parse
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, PrivateAttr, root_validator, validator

import pipelines.db.models as dbm
from pipelines import log

logger = log.get_logger(__file__)


class PipelineOutId(BaseModel):
    id: int


class PipelineExecutionTaskIdOut(BaseModel):
    id: Union[str, int]


class _PipelineStep(BaseModel):
    id: str
    model: str
    model_url: str
    categories: Optional[List[str]] = None
    args: Optional[Dict[str, Any]] = None
    steps: Optional[List[_PipelineStep]]


_PipelineStep.update_forward_refs()


class PipelineOut(PipelineOutId):
    """Model for FastAPI responses representing DB Pipeline model."""

    name: str
    version: int
    original_pipeline_id: Optional[int]
    is_latest: bool
    type: str
    description: Optional[str]
    summary: Optional[str]
    date: datetime
    meta: Dict[str, Any]
    steps: List[_PipelineStep]

    class Config:
        orm_mode = True


class PipelineExecutionTaskOut(PipelineExecutionTaskIdOut):
    """Model for FastAPI responses representing DB
    PipelineExecutionTask model."""

    name: str
    date: datetime
    pipeline_id: int
    job_id: Optional[int]
    runner_id: Optional[str]
    status: str
    webhook: Optional[str]


class ExecutionStepOut(BaseModel):
    """Model for FastAPI responses representing DB ExecutionStep model."""

    id: int
    task_id: int
    name: str
    step_id: Optional[str]
    date: datetime
    init_args: Optional[Dict[str, Any]]
    status: str
    result: Optional[Dict[str, Any]]
    args: Optional[Dict[str, Any]] = None


class InputArguments(BaseModel):
    """Input arguments for any execution step."""

    _current_step_id: str = PrivateAttr()
    _path: str = PrivateAttr()
    _labels: Optional[List[str]] = PrivateAttr()
    _is_init: bool = PrivateAttr()
    input_path: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    file: str
    bucket: str
    pages: Optional[List[int]] = None
    output_path: str
    output_bucket: Optional[str] = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._path = self.get_path()
        self._is_init = kwargs.get("_is_init", True)
        self._current_step_id = self.get_step_id_from_path(self.output_path)
        self._labels = list(self.input.keys()) if self.input else []

    # pylint: disable=E0213
    @root_validator
    def output_bucket_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not values.get("output_bucket"):
            values["output_bucket"] = values["bucket"]
        return values

    @validator("input_path", "output_path")
    def path_validator(  # pylint: disable=E0213
        cls, v: Optional[str]
    ) -> Optional[str]:
        """Path validator."""
        if v is None:
            return v
        mod_v = v.strip().rstrip("/")
        if not 2 <= mod_v.count("/") <= 4:
            raise ValueError(
                "Path should be like 'runs/jobId/fileId/StepId' "
                "or 'runs/jobId/fileId/batchId/stepId'"
            )
        return mod_v

    @validator("file")
    def file_path_validator(cls, v: str) -> str:  # pylint: disable=E0213
        """File path validator."""
        mod_v = v.strip().rstrip("/")
        if mod_v.count("/") != 2:
            raise ValueError(
                "File path should be like 'files/fileId/fileId.fileExt'"
            )
        return mod_v

    def next_step_args(
        self,
        pipeline_type: PipelineTypes,
        curr_step_id: str,
        input_: Optional[Dict[str, Any]],
    ) -> InputArguments:
        """Return next step args based on the current step args."""
        input_path = self.append_path(self._current_step_id)
        file = self.file
        bucket = self.bucket
        pages = self.pages
        if pipeline_type == PipelineTypes.INFERENCE:
            output_path = self.append_path(curr_step_id, ext=".json")
        elif pipeline_type == PipelineTypes.PREPROCESSING:
            output_path = self.output_path
        output_bucket = self.output_bucket
        return InputArguments(
            input_path=input_path,
            input=input_,
            file=file,
            bucket=bucket,
            pages=pages,
            output_path=output_path,
            output_bucket=output_bucket,
            _is_init=False,
        )

    def prepare_for_init(
        self, pipeline_type: PipelineTypes, curr_step_id: str
    ) -> InputArguments:
        """Prepare args as init by creating copy with modified output path."""
        if pipeline_type == PipelineTypes.INFERENCE:
            output_path = self.append_path(
                curr_step_id, self.output_path, ext=".json"
            )
        elif pipeline_type == PipelineTypes.PREPROCESSING:
            output_path = self.output_path
        return InputArguments(
            input_path=self.input_path
            if self.input_path
            else self.output_path,
            input=self.input if self.input else {},
            file=self.file,
            bucket=self.bucket,
            pages=self.pages,
            output_path=output_path,
            output_bucket=self.output_bucket,
        )

    def append_path(
        self, stem: str, path_: Optional[str] = None, ext: str = ""
    ) -> str:
        """Join path_ and stem. Takes self._path if not provided"""
        return urllib.parse.urljoin((path_ or self._path) + "/", stem) + ext

    @staticmethod
    def get_step_id_from_path(path: str) -> str:
        """Get step id from path.
        E.g.: 'runs/jobId/fileId/StepId' -> 'StepId'."""
        return path.rstrip("/").rsplit("/", 1)[-1]

    def get_path(self, trim: bool = True) -> str:
        """Get path without the final component. If trim is False, dont remove
        last component.
        E.g.: 'runs/jobId/fileId/StepId' -> 'runs/jobId/fileId'"""
        path_ = self.output_path.rstrip("/")
        return path_.rsplit("/", 1)[0] if trim else path_

    def get_output_bucket(self) -> str:
        """Get output bucket if presented, else bucket."""
        return self.output_bucket if self.output_bucket else self.bucket

    def get_filename(self) -> str:
        """Get filename without extension."""
        return self.file.strip("/").rsplit("/", 1)[-1].split(".", 1)[0]

    def create_input_by_label(
        self, label: Optional[List[str]]
    ) -> InputArguments:
        """Return copy of the instance with changed input."""
        if not self.input or self._is_init or not label:
            return self.copy(deep=True)
        input_ = self.filter_dict_by_categories(self.input, label)
        if not input_:
            return self.copy(update={"input": {}}, deep=True)
        return self.copy(update={"input": input_}, deep=True)

    @staticmethod
    def filter_dict_by_categories(
        dct: Dict[str, Any], categories: List[str]
    ) -> Dict[str, Any]:
        res = {k: v for k, v in dct.items() if k in categories}
        return res


class PipelineTypes(str, Enum):
    PREPROCESSING = "preprocessing"
    INFERENCE = "inference"


class ModelTypes(str, Enum):
    PREPROCESSING = "preprocessing"


class Status(str, Enum):
    # General status for tasks and steps
    PEND = "Pending"
    RUN = "Running"
    DONE = "Finished"
    FAIL = "Failed"


class JobStatus(str, Enum):
    """Job status."""

    PEND = "Pending"
    RUN = "In Progress"
    DONE = "Finished"
    FAIL = "Failed"


class PreprocessingStatus(str, Enum):
    IN_PROGRESS = "preprocessing in progress"
    PREPROCESSED = "preprocessed"
    FAILED = "failed"
    UPLOADED = "uploaded"


class Event(str, Enum):
    """Event type for Log."""

    INS = "INSERT"
    UPD = "UPDATE"
    DEL = "DELETE"


class Entity(str, Enum):
    """Entity type for Log."""

    PIPE = dbm.Pipeline.__name__
    TASK = dbm.PipelineExecutionTask.__name__
    STEP = dbm.ExecutionStep.__name__
    HEART = dbm.ExecutorHeartbeat.__name__

    @classmethod
    def entity_type(cls, entity: dbm.Table) -> str:
        """Return entity type."""
        return Entity(entity.__class__.__name__).value  # type: ignore


class Log(BaseModel):
    """Model for main log."""

    entity: Entity
    event_type: Event
    data: Dict[str, Any]


class JobProgress(BaseModel):
    finished: int = Field(..., example=1)
    total: int = Field(..., example=1)


class SearchFilters(BaseModel):
    limit: int = 100
    offset: int = 0
    order_by: str = None
    tags: List[str] = None
    only_active: bool = None
    paused: bool = None
    name_pattern: str = None
