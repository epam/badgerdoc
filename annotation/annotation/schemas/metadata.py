from typing import List

from pydantic import BaseModel

from annotation.schemas.tasks import TaskStatusEnumSchema


class EntitiesStatusesSchema(BaseModel):
    task_statuses: List[TaskStatusEnumSchema] = [
        status for status in TaskStatusEnumSchema
    ]
