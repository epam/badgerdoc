"""Testing pipelines/db/logger.py."""
import uuid

import sqlalchemy.event

import pipelines.db.logger as logger
import pipelines.db.models as models
import pipelines.schemas as schemas
import pipelines.pipeline_runner as runner


def test_create_log(testing_session):
    """Testing create_log."""
    pipeline = models.Pipeline(
        name="foo",
        version=1,
        type="inference",
        steps={"bar": 1},
    )
    testing_session.add(pipeline)
    testing_session.commit()
    result = logger.create_log(schemas.Event.INS, pipeline)
    assert result.entity == "Pipeline"
    assert result.event_type == schemas.Event.INS
    assert result.data == pipeline.as_dict(True)


def test_log_after_insert(testing_session):
    """Testing log_after_insert."""
    generated_random_runner_uuid = str(uuid.uuid4())
    runner.runner_id = generated_random_runner_uuid
    pipeline = models.Pipeline(
        name="foo",
        version=1,
        type="inference",
        steps={"bar": 1},
    )
    testing_session.add(pipeline)
    testing_session.commit()
    log = schemas.Log(
        entity="Pipeline",
        event_type=schemas.Event.INS,
        data=pipeline.as_dict(True),
    )
    result = testing_session.query(models.MainEventLog).all()
    assert len(result) == 1
    assert result[0].runner_id == generated_random_runner_uuid
    assert result[0].event == log.dict()


def test_log_after_delete(testing_session):
    """Testing log_after_delete."""
    generated_random_runner_uuid = str(uuid.uuid4())
    runner.runner_id = generated_random_runner_uuid
    pipeline = models.Pipeline(
        name="foo",
        version=1,
        type="inference",
        steps={"bar": 1},
    )
    testing_session.add(pipeline)
    testing_session.flush()
    testing_session.delete(pipeline)
    testing_session.commit()
    log = schemas.Log(
        entity="Pipeline",
        event_type=schemas.Event.DEL,
        data=pipeline.as_dict(True),
    )
    result = testing_session.query(models.MainEventLog).all()
    assert len(result) == 2
    assert result[1].runner_id == generated_random_runner_uuid
    assert result[1].event == log.dict()


def test_log_after_update(testing_session):
    """Testing log_after_update."""
    generated_random_runner_uuid = str(uuid.uuid4())
    sqlalchemy.event.listen(
        testing_session, "after_bulk_update", logger.log_after_update
    )
    runner.runner_id = generated_random_runner_uuid
    pipeline = models.Pipeline(
        name="foo",
        version=1,
        type="inference",
        steps={"bar": 1},
    )
    testing_session.add(pipeline)
    testing_session.commit()
    testing_session.query(models.Pipeline).filter(models.Pipeline.id == 1).update(
        {models.Pipeline.version: 2}
    )
    testing_session.commit()
    log = schemas.Log(
        entity="Pipeline", event_type=schemas.Event.UPD, data={"version": 2}
    )
    result = testing_session.query(models.MainEventLog).all()
    assert len(result) == 2
    assert result[1].runner_id == generated_random_runner_uuid
    assert result[1].event == log.dict()
