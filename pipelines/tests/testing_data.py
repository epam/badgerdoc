import json

import src.db.models as dbm
import src.execution as execution
import src.schemas as schemas

steps_dict = {
    "model": "bar",
    "model_url": "https://foo.com/bar",
    "steps": [
        {"model": "baz", "model_url": "https://foo.com/baz"},
        {
            "model": "mrt",
            "model_url": "https://foo.com/mrt",
            "categories": ["mrt"],
        },
    ],
}
meta_dict = {
    "name": "foo",
    "version": 1,
    "type": "inference",
    "description": "some pipeline to execute",
    "summary": "some pipeline",
}
meta_dict_2 = {
    "name": "bar",
    "version": 2,
    "type": "inference",
    "description": "some pipeline to execute2",
    "summary": "some pipeline2",
}
pipeline_dict = {
    "meta": meta_dict,
    "steps": [steps_dict],
}
pipeline_dict_2 = {**pipeline_dict, "meta": meta_dict_2}

pipeline_json = json.dumps(pipeline_dict)
steps_json = json.dumps(steps_dict)

pipeline = execution.Pipeline.parse_raw(pipeline_json)
steps = execution.PipelineStep.parse_raw(steps_json)


pipeline_db = dbm.Pipeline(
    name="foo",
    version=1,
    original_pipeline_id=1,
    is_latest=True,
    type="inference",
    description="some pipeline to execute",
    summary="some pipeline",
    meta=meta_dict,
    steps=[steps_dict],
)
task_db = dbm.PipelineExecutionTask(
    name="foo", pipeline=pipeline_db, status="Pending", job_id=1
)
step_db = dbm.ExecutionStep(task=task_db, name="bar", status="Pending")

test_exec_step = execution.ExecutionStep.parse_obj(
    {
        "id": 58,
        "task_id": 20,
        "name": "bar",
        "step_id": "05c2c926-5e1b-409d-a88d-eda8c75df3c7",
        "status": "Pending",
    }
)

exec_task = execution.PipelineTask.parse_obj(
    {
        "id": 20,
        "task_name": "dc83271e-ce3e-464c-97ff-6adb4b12dc9d",
        "pipeline_id": 2,
        "status": "Pending",
        "job_id": 2,
        "steps": [test_exec_step],
    }
)

heartbeat_db = dbm.ExecutorHeartbeat()

pipeline_db_repr = (
    "<Pipeline(id=None, name='foo', version=1, "
    "type='inference', date=None)>"
)
task_db_repr = (
    "<PipelineExecutionTask(id=None, name='foo', pipeline_id=None, job_id=1, "
    "runner_id=None, status='Pending')>"
)
step_db_repr = (
    "<ExecutionStep(id=None, task_id=None, name='bar', "
    "step_id=None, status='Pending')>"
)
heartbeat_db_repr = "<ExecutorHeartbeat(id=None, last_heartbeat=None)>"

pipeline_db_dict = {
    "id": None,
    "name": "foo",
    "version": 1,
    "original_pipeline_id": 1,
    "is_latest": True,
    "type": "inference",
    "description": "some pipeline to execute",
    "summary": "some pipeline",
    "date": None,
    "meta": meta_dict,
    "steps": [steps_dict],
}
task_db_dict = {
    "id": None,
    "name": "foo",
    "date": None,
    "pipeline_id": None,
    "job_id": 1,
    "runner_id": None,
    "status": "Pending",
    "webhook": None,
}
step_db_dict = {
    "id": None,
    "task_id": None,
    "name": "bar",
    "parent_step": None,
    "step_id": None,
    "date": None,
    "init_args": None,
    "status": "Pending",
    "result": None,
    "tenant": None,
}
heartbeat_db_dict = {
    "id": None,
    "last_heartbeat": None,
}

exec_input_args = {
    "file": "foo/bar/baz.gz",
    "bucket": "buck-et",
    "pages": [1, 2, 3],
    "output_path": "qwe/foo/foo/bar/",
}

input_args_1 = schemas.InputArguments(
    input={"a": {"aa": 1}, "b": {"bb": 2}},
    file="files/fileId/fileId.fileExt",
    bucket="",
    pages=[],
    output_path="qwe/foo/bar/baz",
)

input_args_2 = schemas.InputArguments(
    file="files/fileId/fileId.fileExt",
    bucket="bucket",
    pages=[],
    output_bucket="output_bucket",
    output_path="qwe/foo/bar/baz",
)
