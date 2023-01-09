import asyncio
import datetime
import random

from aiokafka import AIOKafkaProducer
from sqlalchemy import orm

from scheduler import config, log, runner
from scheduler.db import models, service

logger = log.get_logger(__name__)


def expire_date() -> datetime.datetime:
    """Return date by which heartbeats are considered expired."""
    heartbeat_threshold = datetime.timedelta(
        seconds=config.HEARTBEAT_TIMEOUT * config.THRESHOLD_MUL
    )
    return datetime.datetime.utcnow() - heartbeat_threshold


def manage_expired_runners(
    session: orm.Session, producer: AIOKafkaProducer
) -> None:
    """Get expired heartbeats, remove runner_id and change status to
    'RECEIVED' from corresponding units. Remove expired heartbeats from db.
    Runs unfinished units if there are any.
    """
    expired_heartbeats = service.get_expired_heartbeats(session, expire_date())
    for expired_heartbeat in expired_heartbeats:
        runner_id_ = expired_heartbeat.id
        not_finished_units = service.get_not_finished_units(
            session, runner_id_
        )
        for not_finished_unit in not_finished_units:
            service.change_unit_runner_id_in_lock(
                session, not_finished_unit.id
            )
            runner.run_orm_unit(producer, not_finished_unit)
    service.delete_instances(session, expired_heartbeats)


async def heartbeat(producer: AIOKafkaProducer) -> None:
    """Background heartbeat checker. Add new record to the db with
    current runner_id and update its last_heartbeat datetime every
    HEARTBEAT_TIMEOUT seconds. If difference between current time and
    last_heartbeat more than HEARTBEAT_THRESHOLD then runner is
    considered as dead. Statuses of related not finished units
    are changed to 'RECEIVED' and their runner_id is removed.
    These units will then restart in the runner that found their
    corresponding runner to be dead.
    """
    with service.Session.begin() as session:
        service.add_into_db(session, models.Heartbeat(id=runner.runner_id))
    time_to_sleep = config.HEARTBEAT_TIMEOUT
    while True:
        sleep_time_before_heartbeat = random.randint(1, time_to_sleep)
        await asyncio.sleep(sleep_time_before_heartbeat)
        with service.Session.begin() as session:
            service.update_heartbeat_timestamp(session, runner.runner_id)
            manage_expired_runners(session, producer)
        sleep_time_after_heartbeat = (
            time_to_sleep - sleep_time_before_heartbeat
        )
        await asyncio.sleep(sleep_time_after_heartbeat)
