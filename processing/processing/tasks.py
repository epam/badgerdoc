import asyncio
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Generic, Iterator, List, Optional, TypeVar
from urllib.parse import urljoin
from uuid import uuid4

from cache import AsyncTTL
from fastapi import HTTPException, status
from processing.config import settings
from processing.schema import PreprocessingStatus, Status
from processing.utils.aiohttp_utils import send_request
from processing.utils.logger import get_log_exception_msg, get_logger
from processing.utils.utils import (
    execute_pipeline,
    get_files_data,
    get_model_url,
    split_iterable,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)

T = TypeVar("T", List[str], None)
FilesData = Dict[str, Any]


class BaseTask(Generic[T], metaclass=ABCMeta):
    """
    Template for `task`.
    Implemented tasks can be executed by `execute` method.
    """

    semaphore = asyncio.Semaphore(value=settings.max_tasks)

    def __init__(self) -> None:
        logger.info("Creating %s", self.__class__.__name__)
        self.id = uuid4().hex
        self.status: Status = Status.PEND

    def set_status(self, status_: Status) -> None:
        logger.info("%s change status to %s", self, status_)
        self.status = status_

    async def execute(self) -> T:
        logger.info("Executing %s", self)
        if self.semaphore.locked():
            logger.info("%s waits while semaphore released", self)
        await self.semaphore.acquire()
        try:
            self.set_status(Status.RUN)
            return await self._execute()
        except Exception as err:
            self.set_status(Status.FAIL)
            logger.error(get_log_exception_msg(err))
            raise err
        finally:
            self.set_status(Status.DONE)
            self.semaphore.release()

    @abstractmethod
    async def _execute(self) -> T:
        """
        This method contains everything that the task should do.
        This method executed by self.execute.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}#{self.id}>"


class PreprocessingTask(BaseTask[None]):
    """
    Run preprocessing service.
    """

    def __init__(
        self,
        pipeline_id: int,
        file_ids: List[int],
        languages: Optional[List[str]],
        tenant: str,
        jw_token: str,
        session: Session,
    ) -> None:
        super().__init__()
        self.pipeline_id = pipeline_id
        self.file_ids = file_ids
        self.languages = languages
        self.tenant = tenant
        self.jw_token = jw_token
        self.session = session

    async def _execute(self) -> None:
        logger.info("Fetch data from assets %s", self)
        files_data, _ = await get_files_data(self.file_ids, self.tenant, self.jw_token)
        logger.debug(files_data)
        logger.info("Execute pipeline %s", self)
        await execute_pipeline(
            pipeline_id=self.pipeline_id,
            files_data=self.prepare_data_for_pipelines(files_data),
            current_tenant=self.tenant,
            jw_token=self.jw_token,
            args={"languages": self.languages},
            session=self.session,
            batch_id=self.id,
        )

    @staticmethod
    async def update_file_statuses(
        ids: List[int],
        task_status: PreprocessingStatus,
        tenant: str,
        token: str,
    ) -> None:
        tasks = []
        headers = {
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {token}",
        }
        for id_ in ids:
            body = {"file": id_, "status": task_status}
            task = asyncio.create_task(
                send_request("PUT", url=settings.assets_url, json=body, headers=headers)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

    @staticmethod
    def prepare_data_for_pipelines(
        files_data: List[FilesData],
    ) -> Iterator[FilesData]:

        for file_data in files_data:
            file_data["output_path"] = str(Path(file_data["path"]).parent / "ocr")

            if file_data["pages"] <= settings.pages_per_batch:
                file_data["pages"] = list(range(1, file_data["pages"] + 1))
                yield file_data
                continue

            split_file_data = deepcopy(file_data)
            for pages in split_iterable(
                list(range(1, file_data["pages"] + 1)),
                settings.pages_per_batch,
            ):
                split_file_data["pages"] = pages
                yield split_file_data


class GetLanguagesTask(BaseTask[List[str]]):
    """The task that gets a list of available languages."""

    def __init__(
        self,
        model_id: str,
    ) -> None:
        super().__init__()
        self.model_id = model_id

    @AsyncTTL(time_to_live=60 * 5, maxsize=8)
    async def _execute(self) -> List[str]:
        target_url = urljoin(await get_model_url(self.model_id), "lang")
        logger.info("%s model url=`%s`", self, target_url)
        response = await send_request("GET", url=target_url)
        if response.status_code == 200:
            return response.json  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.json,
        )
