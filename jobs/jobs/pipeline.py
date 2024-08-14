from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, TypedDict


@dataclass
class PipelineFileInput:
    job_id: int


class PipelineFile(TypedDict, total=False):
    bucket: str
    input: PipelineFileInput
    input_path: str
    pages: List[int]
    revision: Optional[str]
    output_path: Optional[str]
    signed_url: Optional[str]
    file_id: Optional[str]


@dataclass
class PipelineRunArgs:
    job_id: int
    tenant: str
    files_data: List[PipelineFile]


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
    ) -> None:
        raise NotImplementedError()
