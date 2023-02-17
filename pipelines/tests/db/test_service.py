"""Testing pipelines/db/service.py."""

import datetime
import uuid
from typing import List
from unittest.mock import patch

import pytest
from aiokafka import AIOKafkaProducer
from freezegun import freeze_time

import pipelines.db.models as dbm
import pipelines.db.service as service
import pipelines.execution as execution
import pipelines.schemas as schemas
import tests.testing_data as td

pytest_plugins = ("pytest_asyncio",)

PEND = schemas.Status.PEND
RUN = schemas.Status.RUN
DONE = schemas.Status.DONE
FAIL = schemas.Status.FAIL


def test_db_connection(testing_session):
    """Testing DB connection."""
    res = testing_session.execute("SELECT 1")
    assert res.scalar() == 1


def test_add_instances(testing_session):
    """Testing _add_instances."""
    # Two pipeline objs are the same.
    pipeline = dbm.Pipeline(type="inference")
    task = dbm.PipelineExecutionTask(pipeline=pipeline)
    objs = [pipeline, pipeline, task]
    ids = service._add_instances(testing_session, objs)
    assert ids == [1, 1, 1]
    assert testing_session.query(dbm.Pipeline).get(1)
    assert testing_session.query(dbm.PipelineExecutionTask).get(1)
    assert not testing_session.query(dbm.Pipeline).get(2)


def test_add_instance(testing_session):
    """Testing _add_instance."""
    pipeline = dbm.Pipeline(type="inference")
    id_ = service._add_instance(testing_session, pipeline)
    id_again = service._add_instance(testing_session, pipeline)
    assert id_ == 1 and id_again == 1
    assert testing_session.query(dbm.Pipeline).get(1)
    assert not testing_session.query(dbm.Pipeline).get(2)


def test_get_all_table_instances(testing_session):
    """Testing get_all_table_instances."""
    testing_session.add(dbm.Pipeline(type="inference"))
    obj = service.get_all_table_instances(testing_session, dbm.Pipeline)[0]
    assert isinstance(obj, dbm.Pipeline)
    assert obj.id == 1


def test_get_table_instance_by_id(testing_session):
    """Testing get_table_instance_by_id."""
    testing_session.add(dbm.Pipeline(type="inference"))
    obj = service.get_table_instance_by_id(testing_session, dbm.Pipeline, 1)
    none_obj = service.get_table_instance_by_id(
        testing_session, dbm.Pipeline, 2
    )
    assert obj
    assert none_obj is None


def test_get_table_instance_by_id_not_found(testing_session):
    """Testing get_table_instance_by_id when instance not found."""
    assert (
        service.get_table_instance_by_id(testing_session, dbm.Pipeline, 1)
        is None
    )


def test_get_pipelines(testing_session):
    """Testing get_pipelines."""
    pipeline_1 = dbm.Pipeline(name="foo", version="1", type="inference")
    pipeline_2 = dbm.Pipeline(name="foo", version="2", type="inference")
    testing_session.add_all([pipeline_1, pipeline_2])
    objs_by_name = service.get_pipelines(testing_session, "foo")
    objs_by_name_and_v = service.get_pipelines(testing_session, "foo", "1")
    assert len(objs_by_name) == 2
    assert len(objs_by_name_and_v) == 1


def test_get_pipelines_not_found(testing_session):
    """Testing get_pipelines when instances not found."""
    assert not service.get_pipelines(testing_session, "not found")


def test_get_task(testing_session):
    """Testing get_task."""
    pipeline = dbm.Pipeline(type="inference")
    task = dbm.PipelineExecutionTask(pipeline=pipeline, name="foo")
    testing_session.add_all([pipeline, task])
    assert isinstance(
        service.get_task(testing_session, "foo"), dbm.PipelineExecutionTask
    )


def test_get_task_not_found(testing_session):
    """Testing get_task when instance not found."""
    assert service.get_task(testing_session, "not found") is None


def test_get_task_job_id(testing_session):
    """Testing get_task_job_id."""
    task = dbm.PipelineExecutionTask(
        pipeline=dbm.Pipeline(type="inference"), job_id=42
    )
    testing_session.add(task)
    assert service.get_task_job_id(testing_session, 1) == 42


def test_get_task_job_id_no_task(testing_session):
    """Testing get_task_job_id when task not found."""
    assert service.get_task_job_id(testing_session, 1) is None


def test_get_step_by_step_and_task_id(testing_session):
    """Testing get_step_by_step_and_task_id."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step_uuid = str(uuid.uuid4())
    step = dbm.ExecutionStep(task=task, step_id=step_uuid, init_args={"foo": 1})
    testing_session.add(step)
    assert service.get_step_by_step_and_task_id(
        testing_session, 1, step_uuid
    ).init_args == {"foo": 1}


def test_get_step_by_step_and_task_id_not_found(testing_session):
    """Testing get_step_by_step_and_task_id when instance not found."""
    some_random_uuid = str(uuid.uuid4())
    assert (
        service.get_step_by_step_and_task_id(testing_session, 1, some_random_uuid)
        is None
    )


def test_delete_instances(testing_session):
    """Testing delete_instances."""
    pipeline = dbm.Pipeline(type="inference")
    testing_session.add(pipeline)
    assert testing_session.query(dbm.Pipeline).get(1)
    service.delete_instances(testing_session, [pipeline])
    assert not testing_session.query(dbm.Pipeline).get(1)


def test_update_table_instance_fields(testing_session):
    """Testing update_table_instance_fields."""
    task = dbm.PipelineExecutionTask(
        pipeline=dbm.Pipeline(type="inference"), name="foo"
    )
    testing_session.add(task)
    service.update_table_instance_fields(
        testing_session,
        dbm.PipelineExecutionTask,
        1,
        {dbm.PipelineExecutionTask.name: "bar"},
    )
    assert (
        testing_session.query(dbm.PipelineExecutionTask).get(1).name == "bar"
    )


def test_update_status(testing_session):
    """Testing update_status."""
    task = dbm.PipelineExecutionTask(
        pipeline=dbm.Pipeline(type="inference"), status=PEND
    )
    testing_session.add(task)
    service.update_status(testing_session, dbm.PipelineExecutionTask, 1, PEND)
    assert (
        testing_session.query(dbm.PipelineExecutionTask).get(1).status == PEND
    )


def test_update_statuses(testing_session):
    """Testing update_statuses."""
    pipeline = dbm.Pipeline(type="inference")
    task_1 = dbm.PipelineExecutionTask(pipeline=pipeline, status=PEND)
    task_2 = dbm.PipelineExecutionTask(pipeline=pipeline, status=RUN)
    testing_session.add_all([task_1, task_2])
    service.update_statuses(
        testing_session, dbm.PipelineExecutionTask, [1, 2], DONE
    )
    assert (
        testing_session.query(dbm.PipelineExecutionTask).get(1).status == DONE
    )
    assert (
        testing_session.query(dbm.PipelineExecutionTask).get(2).status == DONE
    )


def test_get_pending_tasks(testing_session):
    """Testing get_pending_tasks"""
    pipeline = dbm.Pipeline(type="inference")
    task_1 = dbm.PipelineExecutionTask(pipeline=pipeline, status=PEND)
    task_2 = dbm.PipelineExecutionTask(pipeline=pipeline, status=RUN)
    testing_session.add_all([task_1, task_2])
    result = service.get_pending_tasks(testing_session)
    assert len(result) == 1
    assert result[0].status == PEND


def test_update_task_in_lock(testing_session):
    """Testing update_task_in_lock."""
    runner1_uuid, runner2_uuid = [str(uuid.uuid4()) for _ in range(2)]
    task = dbm.PipelineExecutionTask(
        pipeline=dbm.Pipeline(type="inference"), status=PEND, runner_id=runner1_uuid
    )
    testing_session.add(task)
    assert task.runner_id == runner1_uuid
    service.update_task_in_lock(testing_session, 1, runner2_uuid)
    assert task.runner_id == runner2_uuid


def test_get_not_finished_tasks(testing_session):
    """Testing get_not_finished_tasks."""
    pipeline = dbm.Pipeline(type="inference")
    runner1_uuid, runner2_uuid = [str(uuid.uuid4()) for _ in range(2)]
    task_1 = dbm.PipelineExecutionTask(
        pipeline=pipeline, status=PEND, runner_id=runner1_uuid
    )
    task_2 = dbm.PipelineExecutionTask(
        pipeline=pipeline, status=RUN, runner_id=runner2_uuid
    )
    task_3 = dbm.PipelineExecutionTask(
        pipeline=pipeline, status=DONE, runner_id=runner2_uuid
    )
    testing_session.add_all([task_1, task_2, task_3])
    result = service.get_not_finished_tasks(testing_session, runner2_uuid)
    assert len(result) == 1
    assert result[0].id == 2
    assert result[0].status == RUN


def test_get_heartbeat(testing_session):
    """Testing get_heartbeat."""
    id_ = str(uuid.uuid4())
    testing_session.add(dbm.ExecutorHeartbeat(id=id_))
    assert service.get_heartbeat(testing_session, id_)


def test_get_heartbeat_not_found(testing_session):
    """Testing get_heartbeat when instance not found."""
    id_ = str(uuid.uuid4())
    assert service.get_heartbeat(testing_session, id_) is None


def test_get_expired_heartbeats(testing_session):
    """Testing get_expired_heartbeats."""
    eff_date = datetime.datetime.utcnow()
    last_heartbeat = eff_date - datetime.timedelta(minutes=1)
    testing_session.add(dbm.ExecutorHeartbeat(id=str(uuid.uuid4()), last_heartbeat=last_heartbeat))
    result = service.get_expired_heartbeats(testing_session, eff_date)
    assert result[0].last_heartbeat == last_heartbeat


@freeze_time("2020-01-01")
def test_update_heartbeat_timestamp(testing_session):
    """Testing update_heartbeat_timestamp."""
    time_freeze = datetime.datetime(2020, 1, 1)
    id_ = str(uuid.uuid4())
    heartbeat = dbm.ExecutorHeartbeat(id=id_)
    testing_session.add(heartbeat)
    service.update_heartbeat_timestamp(testing_session, id_)
    assert heartbeat.last_heartbeat == time_freeze


def test_task_runner_id_status_in_lock(testing_session):
    """Testing change_task_runner_id_and_status."""
    task = dbm.PipelineExecutionTask(
        pipeline=dbm.Pipeline(type="inference"), status=RUN, runner_id=str(uuid.uuid4())
    )
    testing_session.add(task)
    service.change_task_runner_id_status_in_lock(testing_session, 1)
    assert task.runner_id is None
    assert task.status == PEND


@pytest.mark.asyncio
async def test_initialize(testing_session):
    """Testing initialize_execution."""
    with patch.object(
        execution.Pipeline, "from_orm", return_value=td.pipeline
    ):
        pipeline_db_ = td.pipeline.to_orm()
        testing_session.add(pipeline_db_)
        result = await service.initialize_execution(
            session=testing_session,
            pipeline=pipeline_db_,
            arg={"a": 1},
            producer=AIOKafkaProducer,
            job_id=1,
            task_name="f",
            webhook="http://asd",
            tenant="tenant",
        )
        assert result == 1
        task = testing_session.query(dbm.PipelineExecutionTask).get(1)
        assert task.name == "f"
        assert task.job_id == 1
        assert testing_session.query(dbm.ExecutionStep).get(1).init_args == {
            "a": 1
        }
        assert (
            testing_session.query(dbm.ExecutionStep).get(2).init_args is None
        )


@pytest.mark.parametrize(
    ["current_task_status", "statuses", "expected_result"],
    [
        (DONE, [DONE, DONE], schemas.JobStatus.DONE),
        (RUN, [PEND, RUN], schemas.JobStatus.RUN),
        (FAIL, [DONE, FAIL], schemas.JobStatus.FAIL),
        (FAIL, [RUN, FAIL], schemas.JobStatus.FAIL),
        (FAIL, [RUN, FAIL, DONE], schemas.JobStatus.FAIL),
        (PEND, [PEND, PEND], None),
        (RUN, [RUN, FAIL], None),
        (DONE, [DONE, FAIL], None),
        (DONE, [DONE, PEND], None),
        (RUN, [RUN, RUN], None),
        (RUN, [RUN, FAIL, DONE], None),
        (RUN, [RUN, DONE, DONE], None),
    ],
)
def test_get_job_status_if_changed(
    current_task_status,
    statuses,
    expected_result,
    testing_session,
):
    """Testing job_status."""
    p = dbm.Pipeline(type="inference")
    testing_session.add_all(
        [
            dbm.PipelineExecutionTask(pipeline=p, status=status, job_id=1)
            for status in statuses
        ]
    )
    assert (
        service.get_job_status_if_changed(
            session=testing_session, job_id=1, task_status=current_task_status
        )
        == expected_result
    )


@pytest.mark.parametrize(
    ["status_1", "status_2", "expected"],
    [
        ("Failed", DONE, False),
        (DONE, DONE, True),
        ("Failed", "Failed", False),
    ],
)
def test_is_task_failed(status_1, status_2, expected, testing_session):
    """Testing is_task_failed."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step_1 = dbm.ExecutionStep(task=task, status=status_1)
    step_2 = dbm.ExecutionStep(task=task, status=status_2)
    testing_session.add_all([step_1, step_2])
    assert service.is_task_passed(testing_session, 1) == expected


def test_is_task_failed_no_task(testing_session):
    """Testing is_task_failed when there's no such task."""
    assert service.is_task_passed(testing_session, 1) is None


def test_get_step_result_by_step_and_task_id(testing_session):
    """Testing get_step_result_by_step_and_task_id."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step = dbm.ExecutionStep(task=task, result={"a": 42})
    testing_session.add(step)
    testing_session.commit()
    result = service.get_step_result_by_step_and_task_id(
        testing_session, task.id, step.step_id
    )
    assert result == {"a": 42}


def test_process_step_startup(testing_session):
    """Testing process_step_startup."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step = dbm.ExecutionStep(task=task, status=PEND)
    testing_session.add(step)
    service.process_step_startup(testing_session, 1, {"foo": 1})
    result = testing_session.query(dbm.ExecutionStep).get(1)
    assert result.status == RUN
    assert result.init_args == {"foo": 1}


@pytest.mark.parametrize(
    ["status", "result"],
    [
        (DONE, {"a": 1}),
        (FAIL, {"a": 1}),
        (FAIL, None),
    ],
)
def test_process_step_completion(status: str, result, testing_session):
    """Testing process_step_completion."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step = dbm.ExecutionStep(task=task, status=RUN)
    testing_session.add(step)
    service.process_step_completion(testing_session, 1, status, result)
    step = testing_session.query(dbm.ExecutionStep).get(1)
    assert step.status == status
    assert step.result == result


def test_process_step_completion_delete_step(testing_session):
    """Testing process_step_completion when result is None and status is DONE."""
    task = dbm.PipelineExecutionTask(pipeline=dbm.Pipeline(type="inference"))
    step = dbm.ExecutionStep(task=task, status=RUN)
    testing_session.add(step)
    service.process_step_completion(testing_session, 1, DONE, None)
    step = testing_session.query(dbm.ExecutionStep).get(1)
    assert step is None


def test_get_steps_number_by_job_id(testing_session, testing_task):
    service.add_task(testing_session, testing_task)
    steps = []
    random_uuids = [str(uuid.uuid4()) for _ in range(2)]
    statuses = (schemas.Status.PEND, schemas.Status.DONE)
    for _uuid, status in zip(random_uuids, statuses):
        steps.append(
            dbm.ExecutionStep(
                task=testing_task,
                step_id=_uuid,
                status=status,
            )
        )
    service.add_steps(testing_session, steps)
    total = service.get_steps_number_by_job_id(testing_session, 1)
    assert total == 2
    finished = service.get_steps_number_by_job_id(
        testing_session, 1, schemas.Status.DONE
    )
    assert finished == 1
