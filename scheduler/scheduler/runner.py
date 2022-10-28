import asyncio
import uuid

import aiokafka
from scheduler import exceptions, log, unit
from scheduler.db import models

logger = log.get_logger(__name__)
runner_id: str = str(uuid.uuid4())


async def fetch_and_send(
    producer: aiokafka.AIOKafkaProducer, unit_: unit.Unit
) -> None:
    """Perform request to the url and send the result to the response
    topic if the response topic is specified.

    Args:
        producer: producer instance to send result.
        unit: Unit object.
    """
    try:
        args = {"status": unit.UnitStatus.IN_PROGRESS, "runner_id": runner_id}
        unit_.update(args)
        try:
            status, result = unit.UnitStatus.DONE, await unit_.fetch_result()
        except Exception as err:
            # in case of error inside model request
            # send exception as a result with 'FAILED' status.
            logger.exception(f"Error occured on model side: {unit_.url}")
            status, result = unit.UnitStatus.FAILED, str(err)
        unit_.update({"status": status, "result": result})
        logger.info(f"Status of unit with id '{unit_.id}' is '{status}'")
        if unit_.response_topic:
            await unit_.send(producer, {"status": status, "result": result})
    except Exception:
        logger.exception(
            f"Error occured during proccesing the unit with id '{unit_.id}'."
            "Other tasks continue to run."
        )


def run_orm_unit(
    producer: aiokafka.AIOKafkaProducer, orm_unit: models.Unit
) -> None:
    unit_ = unit.Unit.from_orm(orm_unit)
    asyncio.create_task(fetch_and_send(producer, unit_))


async def run_scheduler(
    consumer: aiokafka.AIOKafkaConsumer, producer: aiokafka.AIOKafkaProducer
) -> None:
    logger.info("Start receiving messages.")
    async for message in consumer:
        logger.info(f"Message with key '{message.key}' received.")
        try:
            unit_ = unit.Unit.from_message(message)
        except exceptions.WrongSignature:
            # do not process the message if it cannot be parsed.
            logger.exception(
                f"Message with the key '{message.key}' was skipped "
                "due to a WrongSignature error."
            )
            continue
        try:
            unit_.into_db()
        except exceptions.DuplicateUnit:
            # do not process the message if the correspond
            # unit is already in the database.
            logger.exception(
                f"Process of the unit with id '{unit_.id}' was skipped "
                "due to a DuplicateUnit error."
            )
            continue
        unit_.update({"status": unit.UnitStatus.RECEIVED})
        await consumer.commit()
        asyncio.create_task(fetch_and_send(producer, unit_))


async def start_runner(
    consumer: aiokafka.AIOKafkaConsumer, producer: aiokafka.AIOKafkaProducer
) -> None:
    """Starts consumer and producer and runs Scheduler."""
    await consumer.start()
    await producer.start()
    try:
        await run_scheduler(consumer, producer)
    except Exception:
        logger.exception("An unexpected exception occured. Runner stopped.")
    finally:
        logger.info("Closing.\n")
        await consumer.stop()
        await producer.stop()
