import asyncio
import uuid
from typing import Any

import aiokafka
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from pipelines import execution, schemas
from pipelines.log import get_logger

logger = get_logger(__file__)

runner_id: str = str(uuid.uuid4())


class ResponseMessage:
    def __init__(self, message: Any) -> None:
        try:
            self.step_id = int(message.key)
            self.result_status = message.value["status"]
            if self.result_status == schemas.Status.FAIL:
                self.result = {"error": message.value["result"]}
            else:
                self.result = message.value["result"]
        except (AttributeError, KeyError):
            logger.error(
                "incorrect message for step %s. Message value: %s",
                message.key,
                message.value,
            )


async def process_message(
    producer: aiokafka.AIOKafkaProducer, message: ResponseMessage
) -> None:
    """
    Process received messages.

    Args:
        producer: Kafka producer
        message: ResponseMessage object
    """
    received_step = execution.ExecutionStep.get_by_id(message.step_id)
    received_step.update(status=message.result_status, result=message.result)

    task = execution.PipelineTask.get_by_id(received_step.task_id)
    if received_step.status == schemas.Status.FAIL:
        error = received_step.result["error"]  # type: ignore
        logger.error(
            f"Received failed step with id = {received_step.id}, "
            f"Error: {error}"
        )
        failed = True
    elif task.is_completed():
        failed = False
    else:
        asyncio.create_task(received_step.process_next_steps(producer))
        return None

    asyncio.create_task(task.finish(failed=failed))


async def run_pipeline(
    consumer: AIOKafkaConsumer, producer: AIOKafkaProducer
) -> None:
    """
    Launch Kafka consumer and process received pipeline steps
    """
    async for message in consumer:
        logger.info(f"Step with id = {message.key} received.")
        msg = ResponseMessage(message)
        await consumer.commit()
        asyncio.create_task(process_message(producer=producer, message=msg))
