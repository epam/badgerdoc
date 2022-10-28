# """Testing src/pipeline_runner.py."""
import logging
from unittest.mock import patch

import pytest
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

import src.execution as execution
import src.pipeline_runner as runner

LOGGER = logging.getLogger(__name__)

pytest_plugins = ("pytest_asyncio",)


class KafkaMessage(BaseModel):
    key: str
    value: dict


class MockConsumer:
    def __init__(self, messages):
        self.messages = messages

    async def __aiter__(self):
        for message in self.messages:
            yield message

    async def commit(self):
        return None


def test_response_message_correct():
    message = KafkaMessage.parse_obj(
        {
            "key": "10",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Finished",
            },
        }
    )
    msg = runner.ResponseMessage(message)
    assert msg.step_id == 10
    assert msg.result["output_bucket"] == "output_bucket"
    assert msg.result_status == "Finished"


def test_response_message_incorrect(caplog):
    message = KafkaMessage.parse_obj(
        {
            "key": "11",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
            },
        }
    )

    runner.ResponseMessage(message)
    assert (
        f"incorrect message for step {message.key}. Message value: {message.value}"
        == caplog.messages[0]
    )


@patch("src.execution.PipelineTask.get_by_id")
@patch("src.execution.ExecutionStep.get_by_id")
@patch("src.execution.ExecutionStep.process_next_steps")
@pytest.mark.asyncio
async def test_process_message_task_not_finished(
    process_next_steps, get_step, get_task, testing_app
):
    exec_step_running = execution.ExecutionStep.parse_obj(
        {
            "id": 57,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Running",
        }
    )
    exec_step_completed = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Running",
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [exec_step_completed, exec_step_running],
        }
    )
    get_task.return_value = task
    get_step.return_value = exec_step_running
    message = KafkaMessage.parse_obj(
        {
            "key": "57",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Finished",
            },
        }
    )
    msg = runner.ResponseMessage(message)

    await runner.process_message(producer=AIOKafkaProducer, message=msg)

    assert process_next_steps.called


@patch("src.execution.PipelineTask.get_by_id")
@patch("src.execution.ExecutionStep.get_by_id")
@patch("src.execution.PipelineTask.finish")
@pytest.mark.asyncio
async def test_process_message_task_finished(
    finish_task, get_step, get_task, testing_app
):
    exec_step_completed2 = execution.ExecutionStep.parse_obj(
        {
            "id": 57,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Finished",
        }
    )
    exec_step_completed = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Finished",
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [exec_step_completed, exec_step_completed2],
        }
    )
    get_task.return_value = task
    get_step.return_value = exec_step_completed
    message = KafkaMessage.parse_obj(
        {
            "key": "58",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Finished",
            },
        }
    )
    msg = runner.ResponseMessage(message)

    await runner.process_message(producer=AIOKafkaProducer, message=msg)

    assert finish_task.called


@patch("src.execution.PipelineTask.get_by_id")
@patch("src.execution.ExecutionStep.get_by_id")
@patch("src.execution.PipelineTask.finish")
@pytest.mark.asyncio
async def test_process_message_task_failed(
    finish_task, get_step, get_task, testing_app, caplog
):
    exec_step_completed = execution.ExecutionStep.parse_obj(
        {
            "id": 58,
            "task_id": 20,
            "name": "bar",
            "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
            "status": "Running",
        }
    )
    task = execution.PipelineTask.parse_obj(
        {
            "id": 20,
            "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
            "pipeline_id": 2,
            "status": "Pending",
            "job_id": 2,
            "steps": [exec_step_completed],
        }
    )
    get_task.return_value = task
    get_step.return_value = exec_step_completed
    message = KafkaMessage.parse_obj(
        {
            "key": "58",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Failed",
            },
        }
    )
    msg = runner.ResponseMessage(message)

    await runner.process_message(producer=AIOKafkaProducer, message=msg)

    assert caplog.messages[0].startswith("Received failed step with id = 58")
    assert finish_task.called


@patch("src.pipeline_runner.process_message")
@pytest.mark.asyncio
async def test_run_pipeline(process_message, caplog):
    message_1 = KafkaMessage.parse_obj(
        {
            "key": "58",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Finished",
            },
        }
    )
    message_2 = KafkaMessage.parse_obj(
        {
            "key": "59",
            "value": {
                "result": {
                    "input_path": "foo/bar/baz.gz",
                    "input": {"a": {"aa": 1}, "b": {"bb": 2}},
                    "file": "foo/bar/baz.gz",
                    "bucket": "test",
                    "pages": [1, 2, 3],
                    "output_path": "qwe/foo/bar/baz",
                    "output_bucket": "output_bucket",
                },
                "status": "Finished",
            },
        }
    )

    mock_consumer = MockConsumer([message_1, message_2])

    await runner.run_pipeline(mock_consumer, AIOKafkaProducer)

    assert caplog.messages[0] == "Step with id = 58 received."
    assert caplog.messages[1] == "Step with id = 59 received."
    assert process_message.called
