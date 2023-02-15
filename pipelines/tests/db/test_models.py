"""Testing users/db/models.py."""

import tests.testing_data as td


def test_pipeline_repr():
    """Testing Pipeline __repr__."""
    assert repr(td.pipeline_db) == td.pipeline_db_repr


def test_pipeline_as_dict():
    """Testing Pipeline as_dict."""
    assert td.pipeline_db.as_dict() == td.pipeline_db_dict


def test_task_repr():
    """Testing PipelineExecutionTask __repr__."""
    assert repr(td.task_db) == td.task_db_repr


def test_task_as_dict():
    """Testing PipelineExecutionTask as_dict."""
    assert td.task_db.as_dict() == td.task_db_dict


def test_step_repr():
    """Testing ExecutionStep __repr__."""
    assert repr(td.step_db) == td.step_db_repr


def test_step_as_dict():
    """Testing ExecutionStep as_dict."""
    assert td.step_db.as_dict() == td.step_db_dict


def test_heartbeat_repr():
    """Testing ExecutorHeartbeat __repr__."""
    assert repr(td.heartbeat_db) == td.heartbeat_db_repr


def test_heartbeat_as_dict():
    """Testing ExecutorHeartbeat as_dict."""
    assert td.heartbeat_db.as_dict() == td.heartbeat_db_dict
