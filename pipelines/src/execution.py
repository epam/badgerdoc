from __future__ import annotations

import asyncio
import urllib.parse
from collections import defaultdict
from datetime import datetime
from itertools import chain
from typing import Any, DefaultDict, Dict, List, Optional, Union
from uuid import uuid4

import requests
from aiokafka import AIOKafkaProducer
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import orm

import src.db.models as dbm
import src.db.service as service
import src.result_processing as postprocessing
from src import config, http_utils, log, s3, schemas, service_token, webhooks

logger = log.get_logger(__file__)
minio_client = s3.get_minio_client()

# Exception messages
PIPELINE_EXISTS = (
    "Pipeline with such name already exists. "
    "You should base on it via 'original_pipeline_id' "
    "if you want to create the next version."
    "Otherwise pick another name."
)
NO_ORIGINAL_PIPELINE = "No such original pipeline to base on."
BAD_PIPELINE_NAME = (
    "If you create the next verion of pipeline via "
    "'original_pipeline_id', the name must be the same."
)


class ExecutionStep(BaseModel):
    """
    Class for execution steps
    """

    id: int
    task_id: int
    name: str
    step_id: str
    parent_step: Optional[str]
    date: Optional[datetime]
    init_args: Optional[Dict[str, Any]]
    status: str
    tenant: Optional[str]
    result: Optional[Dict[str, Any]]

    @classmethod
    def from_orm(cls, obj: dbm.ExecutionStep) -> "ExecutionStep":
        """Create step instance from ORM model.

        :param obj: ExecutionStep ORM model instance.
        :return: ExecutionStep instance.
        """
        return cls.parse_obj(obj.as_dict())

    @classmethod
    def get_by_id(cls, id_: int) -> "ExecutionStep":
        db_step = service.run_in_session(
            service.get_table_instance_by_id,
            dbm.ExecutionStep,
            id_,
        )
        return cls.from_orm(db_step)

    async def step_execution_with_logging(
        self,
        producer: AIOKafkaProducer,
        body: Optional[schemas.InputArguments] = None,
    ) -> None:
        """
        Perform step execution along with logging

        :param producer: Kafka producer.
        :param body: Step execution data.
        :return: None.
        """
        logger.info(f"Executing step with id = {self.id} and body = {body}")
        step_args = step_categories = None
        body_ = {}
        if (pipeline_step := self.get_pipeline_step) is not None:
            step_args = pipeline_step.args
            step_categories = pipeline_step.categories

        if body is not None:
            body_ = body.create_input_by_label(step_categories).dict(
                exclude_unset=True, exclude_none=True
            )
            if step_args is not None:
                body_.update({"args": step_args})

        service.run_in_session(service.process_step_startup, self.id, body_)
        asyncio.create_task(self.step_execution(producer, body_))

    async def step_execution(
        self, producer: AIOKafkaProducer, body: Dict[str, Any]
    ) -> None:
        if (
            body
            and (pipeline_step := self.get_pipeline_step) is not None
            and pipeline_step.model_url is not None
        ):
            await self.send(producer, body, pipeline_step.model_url)
            logger.info(f"Step with id = {self.id} sent.")
            return
        logger.info(
            f"Step with id = {self.id} wasn't send to scheduler. "
            "There is no step body"
        )
        self.update(status=schemas.Status.DONE, result=None)
        task = PipelineTask.get_by_id(self.task_id)
        if task.is_completed():
            await task.finish(failed=False)

    async def send(
        self,
        producer: AIOKafkaProducer,
        body: Dict[str, Any],
        url: str,
    ) -> None:
        """Sends messages to Kafka"""
        await producer.send(
            topic=config.KAFKA_PRODUCE_TOPIC,
            key=str(self.id),
            value={
                "body": body,
                "url": url,
                "response_topic": config.KAFKA_CONSUME_TOPIC,
                "tenant": self.tenant,
            },
        )

    async def process_next_steps(self, producer: AIOKafkaProducer) -> None:
        """
        Processes received steps result and launch next pipeline steps
        """
        next_steps = self.get_next_steps()
        if not next_steps:
            logger.info(
                f"Step with id = {self.id} from task = {self.task_id} "
                "doesn't have child steps."
            )
            return

        body = None
        if self.result:
            body = schemas.InputArguments.parse_obj(self.init_args)
        next_steps_ids = [step.id for step in next_steps]
        logger.info(
            f"Process next steps: {next_steps_ids} "
            f"Parent step id: {self.id} "
            f"Task: {self.task_id}"
        )
        pipeline_type = self.get_pipeline_type()
        for next_step in next_steps:
            next_step_body = None
            if body is not None:
                next_step_body = body.next_step_args(
                    pipeline_type=pipeline_type,
                    curr_step_id=str(next_step.id),
                    input_=self.result,
                )
            asyncio.create_task(
                next_step.step_execution_with_logging(
                    producer=producer, body=next_step_body
                )
            )

    def update(
        self, status: schemas.Status, result: Optional[Dict[str, Any]]
    ) -> None:
        """Updates step status and result."""
        self.status = status
        self.result = result
        service.run_in_session(
            service.update_table_instance_fields,
            dbm.ExecutionStep,
            self.id,
            {
                dbm.ExecutionStep.status: status,
                dbm.ExecutionStep.result: result,
            },
        )

    @property
    def get_pipeline_step(self) -> Optional[PipelineStep]:
        pipeline_id = service.run_in_session(
            service.get_table_instance_by_id,
            dbm.PipelineExecutionTask,
            self.task_id,
        ).pipeline_id
        pipeline_orm = service.run_in_session(
            service.get_table_instance_by_id, dbm.Pipeline, pipeline_id
        )
        pipeline = Pipeline.from_orm(pipeline_orm)
        pipeline_steps_dict = pipeline.get_steps_dict()
        return pipeline_steps_dict.get(self.step_id)

    def get_next_steps(self) -> List[ExecutionStep]:
        task = PipelineTask.get_by_id(self.task_id)
        return [
            step for step in task.steps if step.parent_step == self.step_id
        ]

    def get_pipeline_type(self) -> schemas.PipelineTypes:
        task = PipelineTask.get_by_id(self.task_id)
        return task.get_pipeline_type()


class PipelineTask(BaseModel):
    """
    Class to store pipeline task
    """

    id: int
    task_name: str
    pipeline_id: int
    status: schemas.Status
    job_id: Optional[int]
    steps: List[ExecutionStep]
    webhook: Optional[str]

    @classmethod
    def from_orm(cls, obj: dbm.PipelineExecutionTask) -> "PipelineTask":
        """Create Task instance from ORM model.

        :param obj: PipelineExecutionTask ORM model instance.
        :return: PipelineExecutionTask instance.
        """
        return cls.parse_obj(
            {
                "id": obj.id,
                "task_name": obj.name,
                "pipeline_id": obj.pipeline_id,
                "status": obj.status,
                "job_id": obj.job_id,
                "webhook": obj.webhook,
                "steps": [step.as_dict() for step in obj.steps],
            }
        )

    @classmethod
    def get_by_id(cls, task_id: int) -> "PipelineTask":
        orm_task = service.run_in_session(
            service.get_table_instance_by_id,
            dbm.PipelineExecutionTask,
            task_id,
        )
        return cls.from_orm(orm_task)

    def is_completed(self) -> bool:
        """Check if task is failed by its steps."""
        return all([step.status == schemas.Status.DONE for step in self.steps])

    async def start(self, producer: AIOKafkaProducer) -> None:
        """
        Sends first step to Kafka and launch pipeline running
        """
        pipeline_type = self.get_pipeline_type()
        initial_step = [step for step in self.steps if step.init_args][0]
        args = schemas.InputArguments.parse_obj(initial_step.init_args)
        tenant = s3.tenant_from_bucket(args.get_output_bucket())
        if pipeline_type == schemas.PipelineTypes.INFERENCE:
            preprecessing_passed = await self.check_preprocessing_status(
                bucket
            )
            if not preprecessing_passed:
                return
        logger.info(f"Start executing task with id = {self.id}")
        self.change_status(schemas.Status.RUN)
        self.send_status(pipeline_type=pipeline_type, tenant=tenant)
        init_body = args.prepare_for_init(
            pipeline_type=pipeline_type, curr_step_id=str(initial_step.id)
        )
        asyncio.create_task(
            initial_step.step_execution_with_logging(
                producer=producer, body=init_body
            )
        )

    async def finish(self, failed: bool) -> None:
        """
        Updates task status and starts merge when task completed.

        Args:
            failed: whether the task have failed steps.
        """
        initial_step = [
            step for step in self.steps if step.parent_step is None
        ][0]
        token = service_token.get_service_token()
        args = schemas.InputArguments.parse_obj(initial_step.init_args)
        bucket = args.get_output_bucket()

        pipeline_type = self.get_pipeline_type()
        if not failed and pipeline_type == schemas.PipelineTypes.INFERENCE:
            logger.info(
                "preparing to merge results and send it to postprocessing/annotation"
            )
            path_ = args.get_path()
            filename = args.get_filename()
            file_bucket = args.bucket
            filepath = args.file
            postprocessing_status = postprocessing.manage_result_for_annotator(
                bucket=bucket,
                tenant=s3.tenant_from_bucket(bucket),
                path_=path_,
                job_id=self.job_id,  # type: ignore
                file_bucket=file_bucket,
                filepath=filepath,
                file_id=filename,
                pipeline_id=self.pipeline_id,
                client=minio_client,
                token=token,
            )
            failed = not postprocessing_status

        task_status = schemas.Status.FAIL if failed else schemas.Status.DONE
        self.change_status(task_status)
        logger.info(f"Task with id = {self.id} finished with status = {task_status}")
        tenant = s3.tenant_from_bucket(bucket)
        self.send_status(pipeline_type=pipeline_type, tenant=tenant, token=token)

    def change_status(self, status: schemas.Status) -> None:
        """Changes status of the task in the db and in the instance."""
        self.status = status
        service.run_in_session(
            service.update_status, dbm.PipelineExecutionTask, self.id, status
        )
        logger.info(f"Status of task with id = {self.id} changed to {status}")

    def send_status(
        self,
        pipeline_type: schemas.PipelineTypes,
        tenant: Optional[str],
        token: Optional[str] = None,
    ) -> None:
        if self.webhook is None:
            return
        if pipeline_type == schemas.PipelineTypes.INFERENCE:
            url, body = webhooks.create_inference_url_and_body(
                webhook=self.webhook,
                job_id=self.job_id,  # type: ignore
                task_status=self.status,
            )
        elif pipeline_type == schemas.PipelineTypes.PREPROCESSING:
            url, body = webhooks.create_preprocessing_url_and_body(
                webhook=self.webhook, task_id=self.id, task_status=self.status
            )
        if url and body:
            webhooks.send_webhook(url, body, token, tenant)

    def get_pipeline_type(self) -> schemas.PipelineTypes:
        pipeline = service.run_in_session(
            service.get_table_instance_by_id, dbm.Pipeline, self.pipeline_id
        )
        return pipeline.type  # type: ignore

    def get_file_id(self) -> int:
        step = self.steps[0]
        file_path = step.init_args["file"]  # type: ignore
        file_id = file_path.split("/")[1]
        return int(file_id)

    async def check_preprocessing_status(self, tenant: str) -> bool:
        """Checks preprocessing status of task file.
        If the status is 'preprocessing in progress', waits and tries again.
        If the status is "failed" or the number of retries is exceeded,
        changes task and its steps statuses to 'Failed' and returns False.
        If the status is 'preprocessed', returns True.

        Returns:
            Whether or not preprocessing is passed.
        """
        file_id = self.get_file_id()
        logger.info(
            f"Checking preprocessing status of file with id = {file_id} "
            f"for task with id = {self.id}"
        )
        max_retries = config.MAX_FILE_STATUS_RETRIES
        timeout = config.FILE_STATUS_TIMEOUT
        for retry in range(1, int(max_retries) + 1):
            file_status = http_utils.get_file_status(file_id=file_id, tenant=tenant)
            if file_status == schemas.PreprocessingStatus.PREPROCESSED:
                return True
            elif file_status is None:
                error = "Error while getting file status from assets service."
                break
            elif file_status == schemas.PreprocessingStatus.FAILED:
                error = f"Preprocessing status of file {file_id} is 'failed'"
                break
            elif file_status in [
                schemas.PreprocessingStatus.IN_PROGRESS,
                schemas.PreprocessingStatus.UPLOADED,
            ]:
                await asyncio.sleep(float(timeout))
                continue

        if retry == max_retries:
            error = (
                f"'preprocessing in progress' status for "
                f"file with id = {file_id} did not changed after "
                f"{max_retries} retries every {timeout} seconds."
            )
        self.update_steps(
            status=schemas.Status.FAIL,
            result={"error": error},
        )
        logger.info(
            f"Finish task with id = {self.id} with 'Failed' status "
            f"due to error: {error}"
        )
        await self.finish(failed=True)
        return False

    def update_steps(
        self, status: schemas.Status, result: Dict[str, Any]
    ) -> None:
        """Updates all steps in case of they all have one result.
        For instance, it occurs when preprocessing is failed for
        steps file."""
        for step in self.steps:
            step.update(status=status, result=result)

    class Config:
        orm_mode = True


class PipelineStep(BaseModel):
    """Class to store pipeline steps as a graph."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    model: str
    model_url: Optional[str]
    categories: Optional[List[str]]
    args: Optional[Dict[str, Any]] = None
    steps: Optional[List[PipelineStep]]

    def steps_identifiers(
        self, id_map: Optional[DefaultDict[str, List[str]]] = None
    ) -> Dict[str, List[str]]:
        """Get mapping step id to its steps ids.

        :param id_map: Dict to write identifiers to. <id>: [steps[0].id, ...]
        :return: Dictionary of identifiers.
        """
        id_map = id_map or defaultdict(list)
        _ = id_map[self.id]
        if self.steps:
            for step in self.steps:
                id_map[self.id].append(step.id)
                step.steps_identifiers(id_map)
        return id_map

    def steps_names(self, lst: Optional[List[str]] = None) -> List[str]:
        """Get steps names recursively."""
        lst = lst or []
        lst.append(self.model)
        if self.steps:
            for step in self.steps:
                step.steps_names(lst)
        return lst

    def get_step_dict(self) -> Dict[str, PipelineStep]:
        """
        Returns dict with all steps
        """
        steps_dict: Dict[str, PipelineStep] = {}
        if self.steps:
            for step in self.steps:
                if step.id not in steps_dict.keys():
                    steps_dict[step.id] = step
                steps_dict.update(step.get_step_dict())
        return steps_dict

    @staticmethod
    def fetch(body: Dict[str, Any], url: str, method: str = "POST") -> Any:
        """Perform request to the model.

        :param body: Request body. JSON-like dict.
        :param url: model uri.
        :param method: HTTP method.
        :return: JSON response.
        """
        r = requests.request(method=method, url=url, json=body)
        logger.info("fetching url %s, body %s", url, body)
        return r.json()


PipelineStep.update_forward_refs()


class PipelineMeta(BaseModel):
    name: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    original_pipeline_id: Optional[int] = None
    type: schemas.PipelineTypes = schemas.PipelineTypes.INFERENCE
    description: Optional[str] = None
    summary: Optional[str] = None
    categories: Optional[List[str]] = None

    class Config:
        use_enum_values = True


class Pipeline(BaseModel):
    """Class to store and execute pipeline."""

    meta: PipelineMeta
    steps: List[PipelineStep]

    def get_ids(self) -> Dict[str, List[str]]:
        """Return ids of all steps."""
        return {
            k: v
            for step in self.steps
            for k, v in step.steps_identifiers().items()
        }

    def get_steps_dict(self) -> Dict[str, PipelineStep]:
        """
        Collects pipeline steps and returns them as "plain" dict(not graph).
        ex. {step_id: PipelineStep}

        """
        steps_dict = {
            k: v
            for step in self.steps
            for k, v in step.get_step_dict().items()
        }
        if self.steps:
            for step in self.steps:
                if step.id not in steps_dict.keys():
                    steps_dict[step.id] = step
        return steps_dict

    def get_model_ids(self) -> List[str]:
        """Return names of all steps."""
        return [name for step in self.steps for name in step.steps_names()]

    @classmethod
    def from_orm(cls, obj: dbm.Pipeline) -> Pipeline:
        """Create Pipeline instance from ORM model.

        :param obj: Pipeline ORM model instance.
        :return: Pipeline instance.
        """
        return Pipeline.parse_obj({"meta": obj.meta, "steps": obj.steps})

    def to_orm(self) -> dbm.Pipeline:
        """Create Pipeline ORM instance from Pipeline.

        :return: Pipeline ORM instance.
        """
        meta, steps = self.dict(exclude_none=True).values()
        return dbm.Pipeline(
            name=self.meta.name,
            version=self.meta.version,
            original_pipeline_id=self.meta.original_pipeline_id,
            type=self.meta.type,
            description=self.meta.description,
            summary=self.meta.summary,
            meta=meta,
            steps=steps,
        )

    @staticmethod
    def check_valid_ids(model_ids: List[str]) -> None:
        url = config.MODELS_URI + config.MODELS_DEPLOYMENT_ENDPOINT
        res = PipelineStep.fetch(body={}, url=url, method="GET")
        deployed_names = [el.get("name") for el in res]
        check_ids = {id_: id_ in deployed_names for id_ in model_ids}
        if not all(check_ids.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=check_ids
            )

    @staticmethod
    def get_categories(model_ids: List[str]) -> List[List[str]]:
        body = {
            "pagination": {"page_num": 1, "page_size": 15},
            "filters": [{"field": "id", "operator": "in", "value": model_ids}],
        }
        model_search = config.MODELS_URI + config.MODELS_SEARCH_ENDPOINT
        result = PipelineStep.fetch(body=body, url=model_search)
        items = result.get("data")
        return [item.get("categories") for item in items]

    def update_categories(self, category_arrays: List[List[str]]) -> None:
        categories = chain.from_iterable(category_arrays)
        self.meta.categories = list(set(categories))

    @staticmethod
    def get_model_urls(model_ids: List[str]) -> Dict[str, str]:
        model_deployed = config.MODELS_URI + config.MODELS_DEPLOYMENT_ENDPOINT
        result = PipelineStep.fetch(body={}, url=model_deployed, method="GET")
        url_map = {}
        if config.DIFFERENT_PREPROCESSING_URLS:
            model_types = http_utils.get_model_types(model_ids)
        for id_ in model_ids:
            for mod in result:
                if mod.get("name") == id_:
                    if (
                        config.DIFFERENT_PREPROCESSING_URLS
                        and model_types[id_]
                        == schemas.ModelTypes.PREPROCESSING
                    ):
                        url_map[id_] = Pipeline._convert_preprocessing_uri(
                            mod.get("url")
                        )
                    else:
                        url_map[id_] = Pipeline._convert_uri(mod.get("url"))
        return url_map

    def update_model_field(
        self, steps: List[PipelineStep], url_map: Dict[str, str]
    ) -> None:
        for step in steps:
            step.model_url = url_map.get(step.model)
            if steps_ := step.steps:
                self.update_model_field(steps_, url_map)
        return

    @staticmethod
    def _convert_uri(uri: str) -> str:
        """http://dod.dev1.gcov.ru -> http://dod.dev1/v1/models/dod:predict"""
        base = urllib.parse.urlsplit(uri)
        netloc = urllib.parse.urlsplit(uri).netloc  # dod.dev1.gcov.ru
        model = netloc.split(".")[0]  # dod
        dev = netloc.split(".")[1]  # dev
        suffix = "/v1/models/"
        model_method = ":predict"
        return f"{base.scheme}://{model}.{dev}{suffix}{model}{model_method}"

    @staticmethod
    def _convert_preprocessing_uri(uri: str) -> str:
        """Temporary ad hoc feature for easy_ocr.
        http://easy-ocr.dev2.badgerdoc.com -> http://easy-ocr.dev2/"""
        base = urllib.parse.urlsplit(uri)
        netloc = urllib.parse.urlsplit(uri).netloc
        model = netloc.split(".")[0]  # easy-ocr
        dev = netloc.split(".")[1]  # dev
        return f"{base.scheme}://{model}.{dev}/"

    def adjust_pipeline(self, model_ids: List[str]) -> None:
        categories = self.get_categories(model_ids)
        url_map = self.get_model_urls(model_ids)
        self.update_model_field(self.steps, url_map)
        self.update_categories(categories)

    def check_name(self, session: orm.Session) -> None:
        """Checks if a pipeline with the same name already
        exists in the DB."""
        pipelines_with_such_name = service.get_pipelines(
            session, name=self.meta.name
        )
        if pipelines_with_such_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=PIPELINE_EXISTS
            )

    def update_version(self, session: orm.Session) -> None:
        """Updates version of pipeline. Also changes previous
        pipeline 'is_latest' flag to False."""
        pipelines_with_such_base = service.get_pipelines(
            session, original_pipeline_id=self.meta.original_pipeline_id
        )
        if not pipelines_with_such_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_ORIGINAL_PIPELINE,
            )
        last_version_pipeline = sorted(
            pipelines_with_such_base, key=lambda p: p.version  # type:ignore
        )[-1]
        if last_version_pipeline.name != self.meta.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BAD_PIPELINE_NAME,
            )
        self.meta.version = last_version_pipeline.version + 1
        service.update_table_instance_fields(
            session,
            dbm.Pipeline,
            last_version_pipeline.id,
            {dbm.Pipeline.is_latest: False},
        )

    def update_original_pipeline_id(
        self, session: orm.Session, id_: Union[str, int]
    ) -> None:
        """Updates 'original_pipeline_id' field."""
        service.update_table_instance_fields(
            session,
            dbm.Pipeline,
            id_,
            {dbm.Pipeline.original_pipeline_id: id_},
        )

    class Config:
        orm_mode = True
