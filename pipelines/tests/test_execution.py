"""Testing src/execution.py."""
import logging
from itertools import cycle
from typing import Optional
from unittest.mock import PropertyMock, patch

import pytest
from aiokafka import AIOKafkaProducer
from fastapi import HTTPException
from pydantic import BaseModel

import src.db.models as dbm
import src.execution as execution
import src.schemas as schemas
import tests.testing_data as td

LOGGER = logging.getLogger(__name__)

pytest_plugins = ("pytest_asyncio",)

side_effect = ["a-s-d", "q-w-e", "q-a-z"]


class ExecStepPropertyMock(BaseModel):
    model_url: Optional[str] = None
    categories: Optional[str] = None
    args: Optional[str] = None


@pytest.fixture
def uuid_mock():
    with patch("uuid.UUID.__str__", side_effect=cycle(side_effect)):
        yield uuid_mock


@patch(
    "src.execution.ExecutionStep.get_pipeline_step", new_callable=PropertyMock
)
@patch("src.execution.ExecutionStep.step_execution")
@pytest.mark.asyncio
async def test_step_execution_with_logging(
    step_exec_mock, pipeline_step, run_in_session_mock, caplog
):
    """Testing step_execution_with_logging."""
    property_mock = ExecStepPropertyMock.parse_obj(
        {"model_url": "https://foo.com/bar", "categories": None}
    )
    step_exec_mock.return_value = None
    pipeline_step.return_value = property_mock
    exec_step = td.test_exec_step
    body = schemas.InputArguments.parse_obj(
        {**td.exec_input_args, "result": "foo"}
    )
    await exec_step.step_execution_with_logging(
        body=body, producer=AIOKafkaProducer
    )

    assert step_exec_mock.call_count == 1


@patch(
    "src.execution.ExecutionStep.get_pipeline_step", new_callable=PropertyMock
)
@patch("src.execution.ExecutionStep.send")
@pytest.mark.asyncio
async def test_step_execution(
    mock_send, model_url, caplog, run_in_session_mock
):
    """Testing step_execution."""
    property_mock = ExecStepPropertyMock.parse_obj(
        {"model_url": "https://foo.com/bar"}
    )
    model_url.return_value = property_mock
    mock_send.return_value = None
    exec_step = td.test_exec_step
    await exec_step.step_execution(
        producer=AIOKafkaProducer, body=td.input_args_1
    )
    assert mock_send.called
    assert caplog.messages[0] == "Step with id = 58 sent."


def test_steps_names():
    """Testing PipelineStep steps_names."""
    assert td.steps.steps_names() == ["bar", "baz", "mrt"]


def test_steps_identifiers(uuid_mock):
    """Testing PipelineStep steps_identifiers."""
    steps = execution.PipelineStep.parse_obj(td.steps_dict)
    expected = {"a-s-d": ["q-w-e", "q-a-z"], "q-a-z": [], "q-w-e": []}
    assert steps.steps_identifiers() == expected


def test_get_ids(uuid_mock):
    """Testing Pipeline get_ids."""
    pipeline = execution.Pipeline.parse_obj(td.pipeline_dict)
    expected = {"a-s-d": ["q-w-e", "q-a-z"], "q-a-z": [], "q-w-e": []}
    assert pipeline.get_ids() == expected


def test_get_names():
    """Testing Pipeline get_names."""
    assert td.pipeline.get_model_ids() == ["bar", "baz", "mrt"]


def test_from_orm(uuid_mock):
    """Testing Pipeline from_orm."""
    pipeline = execution.Pipeline.parse_obj(td.pipeline_dict)
    pipeline_ = execution.Pipeline.from_orm(td.pipeline_db)
    assert isinstance(pipeline_, execution.Pipeline)
    assert pipeline_ == pipeline


def test_to_orm():
    """Testing Pipeline to_orm."""
    pipeline_db = td.pipeline.to_orm()
    assert isinstance(pipeline_db, dbm.Pipeline)
    assert pipeline_db.name == "foo"


def test_to_orm_no_pipeline_name(uuid_mock):
    """Testing Pipeline to_orm when there's no name in meta."""
    pipeline_db = execution.Pipeline(
        meta=execution.PipelineMeta(type="inference"), steps=[]
    ).to_orm()
    assert isinstance(pipeline_db, dbm.Pipeline)
    assert pipeline_db.name == "a-s-d"


def test_check_valid_ids():
    with patch.object(
        execution.PipelineStep,
        "fetch",
        return_value=[{"name": "foo"}, {"name": "bar"}],
    ):
        res = execution.Pipeline.check_valid_ids(["foo", "bar"])
        assert res is None


def test_check_valid_ids_not_all():
    with patch.object(
        execution.PipelineStep,
        "fetch",
        return_value=[{"name": "foo"}, {"name": "bar"}],
    ):
        with pytest.raises(HTTPException):
            execution.Pipeline.check_valid_ids(["foo", "bar", "baz"])


def test_get_categories():
    with patch.object(
        execution.PipelineStep,
        "fetch",
        return_value={
            "data": [
                {"name": "foo", "categories": ["foo", "bar", "text"]},
                {"name": "bar", "categories": ["figure", "header", "text"]},
            ]
        },
    ):
        res = execution.Pipeline.get_categories(["z"])
        assert res == [["foo", "bar", "text"], ["figure", "header", "text"]]


def test_update_categories():
    categories = [["foo", "bar", "text"], ["figure", "header", "text"]]
    td.pipeline.update_categories(categories)
    assert (
        td.pipeline.meta.categories.sort()
        == ["foo", "bar", "figure", "header", "text"].sort()
    )


def test_update_categories_empty():
    categories = [[], []]
    td.pipeline.update_categories(categories)
    assert td.pipeline.meta.categories == []


@pytest.mark.skip(reason="We make request which is not mocked, fix needed")
def test_get_model_urls():
    with patch.object(
        execution.PipelineStep,
        "fetch",
        return_value=[
            {"name": "foo", "url": "http://foo.dev1.gcov.ru"},
            {"name": "bar", "url": "http://bar.dev1.gcov.ru"},
            {"name": "baz", "url": "http://baz.dev1.gcov.ru"},
        ],
    ):
        res = execution.Pipeline.get_model_urls(["foo", "bar"])
        assert res == {
            "foo": "http://foo.dev1/v1/models/foo:predict",
            "bar": "http://bar.dev1/v1/models/bar:predict",
        }


def test_update_model_field():
    url_map = {
        "foo": "http://foo.dev1/v1/models/foo:predict",
        "bar": "http://bar.dev1/v1/models/bar:predict",
    }
    td.pipeline.update_model_field(td.pipeline.steps, url_map)
    assert td.pipeline.dict()["steps"][0]["model_url"] == url_map["bar"]


def test__convert_uri():
    assert (
        execution.Pipeline._convert_uri("http://foo.dev1.gcov.ru")
        == "http://foo.dev1/v1/models/foo:predict"
    )
    assert (
        execution.Pipeline._convert_uri("http://bar.dev1.gcov.ru")
        == "http://bar.dev1/v1/models/bar:predict"
    )


def test_adjust_pipeline():
    with patch.object(
        execution.Pipeline, "get_categories", return_value=[["text", "chart"]]
    ):
        with patch.object(
            execution.Pipeline,
            "get_model_urls",
            return_value={"bar": "http://bar.dev1.gcov.ru"},
        ):
            td.pipeline.adjust_pipeline(td.pipeline.get_model_ids())
            assert (
                td.pipeline.meta.categories.sort() == ["text", "chart"].sort()
            )


@patch("src.execution.ExecutionStep.step_execution_with_logging")
@patch("src.execution.PipelineTask.send_status")
@pytest.mark.asyncio
async def test_start_task(
    webhook_mock,
    exec_mock,
    run_in_session_mock,
    mock_preprocessing_file_status,
    caplog,
):
    webhook_mock.return_value = None
    exec_mock.return_value = None
    step_with_args = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Pending",
            "init_args": {
                "input_path": "foo/bar/baz.gz",
                "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                "file": "foo/bar/baz.gz",
                "bucket": "test",
                "pages": [1, 2, 3],
                "output_path": "qwe/foo/bar/baz",
                "output_bucket": "output_bucket",
            },
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [step_with_args],
        }
    )

    # async def check_preprocessing_status_mock(x, y):
    #     return True

    with patch(
        "src.execution.PipelineTask.get_pipeline_type",
        lambda _: schemas.PipelineTypes.INFERENCE,
    ):
        # with patch(
        #     "src.execution.PipelineTask.check_preprocessing_status",
        #     check_preprocessing_status_mock,
        # ):
        await task.start(AIOKafkaProducer)

    assert caplog.messages[0] == "Start executing task with id = 20"
    assert exec_mock.called


@patch("src.execution.ExecutionStep.step_execution_with_logging")
@pytest.mark.asyncio
async def test_process_next_steps(exec_step, caplog):
    exec_step.return_value = None
    received_step = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Finished",
            "init_args": td.exec_input_args,
        }
    )
    child_step = execution.ExecutionStep.parse_obj(
        {
            "id": 59,
            "task_id": 20,
            "name": "bar",
            "step_id": "08c2c906-5e1b-409d-a88d-eda8c7gfg7ik",
            "status": "Pending",
            "parent_step": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [received_step, child_step],
        }
    )
    with patch("src.execution.PipelineTask.get_by_id", lambda id_: task):
        with patch(
            "src.execution.PipelineTask.get_pipeline_type",
            lambda _: schemas.PipelineTypes.INFERENCE,
        ):
            await received_step.process_next_steps(AIOKafkaProducer)
    assert caplog.messages[0].startswith("Process next steps: [59]")
    assert exec_step.called


@patch("src.execution.ExecutionStep.step_execution_with_logging")
@pytest.mark.asyncio
async def test_process_next_staps_without_child_steps(exec_step, caplog):
    received_step = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Finished",
            "init_args": td.exec_input_args,
        }
    )
    some_step = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "08c2c906-5e1b-409d-a88d-eda8c7gfg7ik",
            "status": "Pending",
            "parent_step": "98c2c926-5e1b-409d-a88d-eda8c75df3u6",
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [received_step, some_step],
        }
    )

    with patch("src.execution.PipelineTask.get_by_id", lambda id_: task):
        await received_step.process_next_steps(AIOKafkaProducer)

    assert caplog.messages[0].startswith("Step with id = 58 from task = 20")
    exec_step.assert_not_called()
