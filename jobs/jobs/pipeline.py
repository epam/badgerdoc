from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TypedDict

import jobs.schemas as schemas


@dataclass
class PipelineFileInput:
    job_id: int


class Dataset(TypedDict, total=False):
    id: int
    name: str


class PipelineFile(TypedDict, total=False):
    bucket: str
    input: PipelineFileInput
    input_path: str
    pages: List[int]
    datasets: List[Dataset]
    revision: Optional[str]
    output_path: Optional[str]
    signed_url: Optional[str]
    file_id: Optional[str]


@dataclass
class PipelineRunArgs:
    job_id: int
    tenant: str
    files_data: List[PipelineFile]
    datasets: List[Dataset]
    revisions: List[str]


@dataclass
class AnyPipeline:
    pass


class BasePipeline(metaclass=ABCMeta):
    @abstractmethod
    async def list(self) -> List[AnyPipeline]:
        raise NotImplementedError()

    @abstractmethod
    async def run(
        self,
        pipeline_id: str,
        job_id: str,
        files: List[PipelineFile],
        current_tenant: str,
        datasets: List[Dataset],
    ) -> None:
        raise NotImplementedError()


AI_PIPELINE = {"name": "AI by MCP", "id": "ai_by_mcp"}


class OtherPipeline(BasePipeline):
    async def list(self) -> List[AnyPipeline]:
        return schemas.Pipelines(
            data=[
                schemas.Pipeline(
                    name=AI_PIPELINE["name"],
                    id=AI_PIPELINE["id"],
                    version=0,
                    type="other",
                    date=datetime.today(),
                    meta={},
                    steps=[],
                )
            ]
        )

    async def run(
        self,
        pipeline_id: str,
        job_id: str,
        files: List[PipelineFile],
        current_tenant: str,
        datasets: List[Dataset],
        **kwargs: dict,
    ) -> None:
        if pipeline_id == AI_PIPELINE["id"]:
            return None
        raise ValueError(f"Pipeline {pipeline_id} not found")
