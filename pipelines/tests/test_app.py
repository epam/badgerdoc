"""Testing src/app.py."""

from copy import deepcopy
from typing import Dict

import pytest

import src.app as app
import src.db.models as dbm
import src.db.service as service
import src.execution as execution
import src.schemas as schemas
import tests.testing_data as td


def test_add_pipeline(testing_app, adjust_mock):
    """Testing add_pipeline."""
    response = testing_app.post("/pipeline", json=td.pipeline_dict)
    assert response.status_code == 201
    assert response.json() == {"id": 1}


def test_add_pipeline_with_same_name(testing_app, adjust_mock):
    """Testing add_pipeline."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.post("/pipeline", json=td.pipeline_dict)
    assert response.status_code == 409
    assert response.json() == {"detail": execution.PIPELINE_EXISTS}


def test_add_pipeline_no_such_original_pipeline(testing_app, adjust_mock):
    """Testing add_pipeline."""
    pipeline_dict = deepcopy(td.pipeline_dict)
    pipeline_dict["meta"]["original_pipeline_id"] = 0
    response = testing_app.post("/pipeline", json=pipeline_dict)
    assert response.status_code == 404
    assert response.json() == {"detail": execution.NO_ORIGINAL_PIPELINE}


def test_add_pipeline_next_version_with_another_name(testing_app, adjust_mock):
    pipeline_dict_1 = deepcopy(td.pipeline_dict)
    testing_app.post("/pipeline", json=pipeline_dict_1)
    pipeline_dict_2 = deepcopy(td.pipeline_dict_2)
    pipeline_dict_2["meta"]["original_pipeline_id"] = 1
    response = testing_app.post("/pipeline", json=pipeline_dict_2)
    assert response.status_code == 400
    assert response.json() == {"detail": execution.BAD_PIPELINE_NAME}


def test_add_pipeline_autogen_ids(testing_app, adjust_mock):
    """Testing add_pipeline for creating ids of every step"""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.get("/pipeline", params={"name": "foo"})
    assert response.status_code == 200
    assert response.json()["steps"][0]["id"]
    assert response.json()["steps"][0]["steps"][0]["id"]


@pytest.mark.parametrize(
    ["q_params", "pipeline"],
    [
        ({"name": "foo"}, td.pipeline_dict),
        ({"name": "bar", "version": 2}, td.pipeline_dict_2),
    ],
)
def test_get_pipeline(
    q_params: Dict[str, str], testing_app, adjust_mock, pipeline
):
    """Testing get_pipeline."""
    testing_app.post("/pipeline", json=pipeline)
    response = testing_app.get("/pipeline", params=q_params)
    assert response.status_code == 200
    assert response.json()["meta"] == pipeline.get("meta")


def test_get_pipeline_not_found(testing_app, adjust_mock):
    """Testing get_pipeline when there's no such pipeline."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    q_params = {"name": "foo", "version": 2}
    response = testing_app.get("/pipeline", params=q_params)
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_get_pipelines(testing_app, adjust_mock):
    """Testing get_pipelines."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    testing_app.post("/pipeline", json=td.pipeline_dict_2)
    response = testing_app.get("/pipelines")
    ids = [res_["id"] for res_ in response.json()]
    assert response.status_code == 200
    assert len(ids) == 2


@pytest.mark.parametrize(
    ["q_params", "pipeline"],
    [
        ({"name": "foo"}, td.pipeline_dict),
        ({"name": "bar", "version": 2}, td.pipeline_dict_2),
    ],
)
def test_delete_pipelines(
    q_params: Dict[str, str], pipeline, testing_app, adjust_mock
):
    """Testing delete_pipelines."""
    testing_app.post("/pipeline", json=pipeline)
    response = testing_app.delete("/pipelines", params=q_params)
    assert response.status_code == 200
    assert response.json() == {"result": "Pipelines has been deleted."}
    response = testing_app.get("/pipelines")
    assert response.json() == []


@pytest.mark.parametrize(
    "q_params",
    [
        {"name": "not_exist"},
        {"name": "not_exist", "version": 1},
    ],
)
def test_delete_pipelines_not_found(q_params: Dict[str, str], testing_app):
    """Testing delete_pipelines."""
    response = testing_app.delete("/pipelines", params=q_params)
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_delete_pipeline_by_id(testing_app, adjust_mock):
    """Testing delete_pipeline_by_id."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.delete("/pipelines/1")
    assert response.status_code == 200
    assert response.json() == {"result": "Pipeline has been deleted."}
    response = testing_app.get("/pipelines")
    assert response.json() == []


def test_delete_pipeline_by_id_not_found(testing_app, adjust_mock):
    """Testing delete_pipeline_by_id when there's no such pipeline."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.delete("/pipelines/2")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_get_pipeline_by_id(testing_app, adjust_mock):
    """Testing get_pipeline_by_id."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.get("/pipelines/1")
    assert response.status_code == 200
    assert response.json()["name"] == "foo"


def test_get_pipeline_by_id_not_found(testing_app, adjust_mock):
    """Testing get_pipeline_by id when there's no such pipeline."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.get("/pipelines/2")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_get_task_by_id(testing_task, testing_app, testing_session):
    """Testing get_task_by_id."""
    service.add_task(testing_session, testing_task)
    response = testing_app.get("/pipelines/tasks/1")
    assert response.status_code == 200
    assert response.json()["name"] == "foo"
    assert response.json()["id"] == 1


def test_get_task_by_id_not_found(testing_task, testing_app, testing_session):
    """Testing get_task_by_id."""
    service.add_task(testing_session, testing_task)
    response = testing_app.get("/pipelines/tasks/2")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_TASK}


def test_get_task_by_pipeline_id(
    testing_pipeline, testing_task, testing_app, testing_session
):
    """Testing get_task_by_pipeline_id."""
    service.add_task(testing_session, testing_task)
    run = dbm.PipelineExecutionTask(
        name="bar", pipeline=testing_pipeline, status="running"
    )
    service.add_task(testing_session, run)
    response = testing_app.get("/pipelines/1/task")
    assert response.status_code == 200
    assert response.json()["name"] == "bar"


def test_get_task_by_pipeline_id_pipeline_not_found(
    testing_task, testing_app, testing_session
):
    """Testing get_task_by_pipeline_id when there's no such pipeline."""
    service.add_task(testing_session, testing_task)
    response = testing_app.get("/pipelines/2/task")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_get_task_by_pipeline_id_task_not_found(
    testing_app, testing_session, adjust_mock
):
    """Testing get_task_by_pipeline_id when there's no tasks."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.get("/pipelines/1/task")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_LATEST_TASK}


def test_get_tasks_by_pipeline_id(
    testing_pipeline, testing_task, testing_app, testing_session
):
    """Testing get_tasks_by_pipeline_id."""
    service.add_task(testing_session, testing_task)
    run = dbm.PipelineExecutionTask(
        name="bar", pipeline=testing_pipeline, status="running"
    )
    service.add_task(testing_session, run)
    response = testing_app.get("/pipelines/1/tasks")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "foo"
    assert response.json()[1]["name"] == "bar"


def test_get_tasks_by_pipeline_id_pipeline_not_found(
    testing_task, testing_app, testing_session
):
    """Testing get_tasks_by_pipeline_id when there's no such pipeline."""
    service.add_task(testing_session, testing_task)
    response = testing_app.get("/pipelines/2/tasks")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_delete_task(testing_task, testing_app, testing_session):
    """Testing delete_task."""
    service.add_task(testing_session, testing_task)
    response = testing_app.delete("/pipelines/tasks/1")
    assert response.status_code == 200
    assert response.json() == {"result": "Task has been deleted."}
    response = testing_app.get("/pipelines/1/task")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_LATEST_TASK}


def test_delete_task_not_found(testing_task, testing_app, testing_session):
    """Testing delete_task when there's no such task."""
    service.add_task(testing_session, testing_task)
    response = testing_app.delete("/pipelines/tasks/2")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_TASK}


def test_get_task_steps_by_id(testing_task, testing_app, testing_session):
    """Testing get_task_steps_by_id."""
    step = dbm.ExecutionStep(task=testing_task, name="bar", status="pending")
    service.add_step(testing_session, step)
    response = testing_app.get("/pipelines/tasks/1/steps")
    assert response.status_code == 200
    assert response.json()[0]["status"] == "pending"


def test_get_task_steps_by_id_not_found(
    testing_task, testing_app, testing_session
):
    """Testing get_task_steps_by_id when there's no such task."""
    step = dbm.ExecutionStep(task=testing_task, name="bar", status="pending")
    service.add_step(testing_session, step)
    response = testing_app.get("/pipelines/tasks/2/steps")
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_TASK}


# Pipeline execution #


def test_response__execute_pipeline_by_id(
    testing_app, adjust_mock, mock_preprocessing_file_status
):
    """Testing execute_pipeline_by_id response."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.post(
        "/pipelines/1/execute",
        json=[td.exec_input_args],
        params={"job_id": 1},
    )

    assert response.status_code == 200
    assert response.json() == [{"id": 1}]


def test_response__execute_pipeline_by_id_not_found(testing_app, adjust_mock):
    """When there's no such pipeline."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    response = testing_app.post(
        "/pipelines/2/execute",
        json=[td.exec_input_args],
        params={"job_id": 1},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_PIPELINE}


def test_task__execute_pipeline_by_id(
    testing_app, adjust_mock, mock_preprocessing_file_status
):
    """Testing execute_pipeline_by_id created task."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    id_ = testing_app.post(
        "/pipelines/1/execute",
        json=[td.exec_input_args],
        params={"job_id": 1},
    ).json()[0]["id"]
    response = testing_app.get("/pipelines/1/task")
    assert response.status_code == 200
    assert response.json()["status"] == schemas.Status.RUN
    assert id_ == response.json()["id"]


def test_step_args__execute_pipeline_by_id(
    testing_app, adjust_mock, mock_preprocessing_file_status
):
    """Testing execute_pipeline_by_id created steps init args and results."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    testing_app.post(
        "/pipelines/1/execute",
        json=[td.exec_input_args],
        params={"job_id": 1},
    )
    response = testing_app.get("/pipelines/tasks/1/steps")
    assert response.status_code == 200
    assert len(response.json()) == 3
    first_step = response.json()[0]
    second_step = response.json()[1]
    assert first_step["status"] == schemas.Status.RUN
    assert second_step["status"] == schemas.Status.PEND


def test_steps_ids__execute_pipeline_by_id(
    testing_app, adjust_mock, mock_preprocessing_file_status
):
    """Steps ids equals to pipeline steps ids."""
    testing_app.post("/pipeline", json=td.pipeline_dict)
    testing_app.post(
        "/pipelines/1/execute",
        json=[td.exec_input_args],
        params={"job_id": 1},
    )
    pipeline_steps = testing_app.get("/pipelines/1").json()["steps"]
    exec_steps = testing_app.get("/pipelines/tasks/1/steps").json()
    p_steps_ids = [
        pipeline_steps[0]["id"],
        pipeline_steps[0]["steps"][0]["id"],
        pipeline_steps[0]["steps"][1]["id"],
    ]
    e_steps_ids = [step["step_id"] for step in exec_steps]
    assert p_steps_ids == e_steps_ids
