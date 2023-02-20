import asyncio
import datetime
import uuid
from unittest import mock

import pytest
from freezegun import freeze_time
from scheduler.db import models

from scheduler import heartbeat, unit


@freeze_time("2020-01-01")
@mock.patch("scheduler.config.HEARTBEAT_TIMEOUT", 3)
@mock.patch("scheduler.config.THRESHOLD_MUL", 1)
def test_expire_date():
    """Testing expire_date."""
    expected = datetime.datetime(2019, 12, 31, 23, 59, 57)
    assert heartbeat.expire_date() == expected


def test_manage_expired_runners(testing_session):
    """Testing manage_expired_runners."""
    id_ = str(uuid.uuid4())
    unit_1 = models.Unit(
        id="unit_1_id", runner_id=id_, status=unit.UnitStatus.DONE
    )
    unit_2 = models.Unit(
        id="unit_2_id", runner_id=id_, status=unit.UnitStatus.IN_PROGRESS
    )
    heartbeat_ = models.Heartbeat(
        id=id_, last_heartbeat=datetime.datetime(2022, 1, 1)
    )

    testing_session.add_all([unit_1, unit_2, heartbeat_])
    with mock.patch("scheduler.runner.run_orm_unit"):
        heartbeat.manage_expired_runners(testing_session, mock.MagicMock())
    units = testing_session.query(models.Unit).all()
    assert not testing_session.query(models.Heartbeat).all()
    assert units[0].status == unit.UnitStatus.DONE
    assert units[1].runner_id is None
    assert units[1].status == unit.UnitStatus.RECEIVED


def test_heartbeat_adds_to_db(testing_session, testing_sessionmaker):
    """Testing heartbeat."""
    with mock.patch(
        "scheduler.heartbeat.service.Session",
        testing_sessionmaker,
    ):
        with mock.patch(
            "scheduler.heartbeat.asyncio.sleep", side_effect=RuntimeError()
        ):
            with pytest.raises(RuntimeError):
                asyncio.run(heartbeat.heartbeat(mock.MagicMock()))
    heartbeats = testing_session.query(models.Heartbeat).all()
    assert len(heartbeats) == 1
    assert heartbeats[0].id == heartbeat.runner.runner_id
