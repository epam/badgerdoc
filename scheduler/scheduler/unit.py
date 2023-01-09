import asyncio
import dataclasses
import enum
import pathlib
from typing import Any, Dict

import aiohttp
import aiokafka
from sqlalchemy import exc

from scheduler import config, exceptions, log
from scheduler.db import models, service

logger = log.get_logger(__name__)


class UnitStatus(str, enum.Enum):
    RECEIVED = "Received"
    IN_PROGRESS = "In Progress"
    DONE = "Finished"
    FAILED = "Failed"


@dataclasses.dataclass
class Unit:
    id: str
    url: str
    body: Dict[Any, Any]
    tenant: str
    response_topic: str

    @classmethod
    def from_message(
        cls,
        message: aiokafka.structs.ConsumerRecord,
    ) -> "Unit":
        try:
            url = message.value["url"]
            body = message.value["body"]
            tenant = message.value["tenant"]
        except KeyError:
            raise exceptions.WrongSignature(
                (
                    "Wrong message value signature. "
                    "Must contain 'url', 'body', 'tenant'."
                )
            )
        response_topic = message.value.get("response_topic")
        id_ = message.key

        return cls(
            id=id_,
            url=url,
            body=body,
            tenant=tenant,
            response_topic=response_topic,
        )

    async def fetch_result(self) -> aiohttp.ClientResponse:
        """Fetches the result from 'self.url'. If env var 'TEST_MODE'
        is True, imitate fetching via sleeping."""
        if config.TEST_MODE:
            await asyncio.sleep(3)
            new_output_path = pathlib.Path(self.body["output_path"])
            self.body["output_path"] = str(new_output_path.with_suffix(""))
            return self.body
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT * 60)
        async with aiohttp.request(
            url=self.url,
            json=self.body,
            method="POST",
            timeout=timeout,
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    async def send(
        self, producer: aiokafka.AIOKafkaProducer, result: Dict[str, Any]
    ) -> None:
        """Sends instance into 'respone topic'."""
        await producer.send(self.response_topic, key=self.id, value=result)

    def to_orm(self) -> models.Unit:
        """Turn instance to the ORM object."""
        return models.Unit(
            id=self.id,
            url=self.url,
            body=self.body,
            tenant=self.tenant,
            response_topic=self.response_topic,
        )

    def into_db(self) -> None:
        """Adds instance to the database."""
        unit_orm = self.to_orm()
        try:
            with service.Session.begin() as session:
                service.add_into_db(session, unit_orm)
        except exc.IntegrityError:
            raise exceptions.DuplicateUnit(
                f"Unit with id {self.id} already exists in the database."
            )

    def update(self, args: Dict[str, Any]) -> None:
        """Update related database row with the kwargs."""
        with service.Session.begin() as session:
            service.update_instance_by_id(
                session, table=models.Unit, id_=self.id, args=args
            )

    @classmethod
    def from_orm(cls, orm_unit: models.Unit) -> "Unit":
        return cls(**orm_unit.as_dict())
