from typing import Optional

from pydantic import BaseModel

from task_manager.location.location import Location
from task_manager.redis_db import async_redis


class TaskMessage(BaseModel):
    task_id: str
    location_id: str
    timestamp: int


def create_task_message(task_id: str, timestamp: int, location: Optional[Location] = None) -> TaskMessage:
    task_message = TaskMessage(
        task_id=task_id,
        timestamp=timestamp,
        location_id=location.id if location else None
    )
    return task_message


async def publish_task_message(message: TaskMessage):
    await async_redis.xadd(
        name='task-stream',
        fields=message.model_dump(),
        id='*'
    )
