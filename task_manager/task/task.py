import asyncio
import logging
import time
from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Summary
from pydantic import BaseModel

from task_manager.location import Location, LocationService, get_location_service
from task_manager.redis_db import async_redis
from task_manager.stream import create_task_message, publish_task_message
from task_manager.utils import decode_redis_data

logger = logging.getLogger()
router = APIRouter()


class TaskInput(BaseModel):
    name: str
    description: str
    location: Location


class Task(TaskInput):
    id: str
    timestamp: int


PING_SUMMARY = Summary('ping_processing_time', 'ping time')


@PING_SUMMARY.time()
@router.get("/ping")
async def health_check():
    await asyncio.sleep(3)
    return {"message": "pong"}


@router.get("/task")
async def get_tasks():
    tasks = await fetch_tasks()
    return {"tasks": tasks}


@router.get("/task/{task_id}")
async def get_task(task_id: str, location_service: LocationService = Depends(get_location_service)):
    task = await fetch_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    response = {"task": task}
    logger.warning({"task": task})
    if task.location is not None:
        locations_near_me = await location_service.find_location_near_me(longitude=task.location.longitude,
                                                                         latitude=task.location.latitude, unit="km",
                                                                         distance=1.0)
        logger.warning(locations_near_me)
        locations_near_me = exclude_self(location_id=task.location.id, locations_near_me=locations_near_me)
        response.update({"locationsNearMe": locations_near_me})
    return response


@router.post("/task")
async def create_task(task: TaskInput, location_service: LocationService = Depends(get_location_service)):
    task_id = str(uuid4())
    task_to_insert = Task(id=task_id, timestamp=int(time.time()), **task.dict())
    try:
        await persist_task(task_to_insert, location_service)
        return {"task": task_to_insert, "created": True, "message": "Task Created Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def remove_task(task_id: str):
    try:
        await delete_task(task_id)
        return {"id": task_id, "message": "Task deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def persist_task(task: Task, location_service: LocationService) -> None:
    task_key = f"task:{task.id}"
    if task.location is not None:
        location = await location_service.add_location(task.location)
        task.location = location
    mapping = {
        **task.dict(),
    }
    del mapping['location']
    if task.location is not None:
        mapping.update({
            'location_id': task.location.id,
            'location_name': task.location.name,
            'location_description': task.location.description,
            'location_longitude': task.location.longitude,
            'location_latitude': task.location.latitude,
        })

    await async_redis.hset(
        task_key,
        mapping=mapping,
    )
    await async_redis.zadd("tasks", {str(task.id): task.timestamp})
    task_message = create_task_message(task_id=task.id, timestamp=task.timestamp, location=task.location or None)
    await publish_task_message(task_message)


async def fetch_task(task_id: str) -> Optional[Task]:
    task_data = await async_redis.hgetall(f"task:{task_id}")
    if not task_data:
        return None
    task_data = decode_redis_data(task_data)
    task = Task(
        id=task_data["id"],
        name=task_data["name"],
        description=task_data["description"],
        timestamp=int(task_data["timestamp"]),
        location=Location(
            id=task_data["location_id"],
            name=task_data["location_name"],
            description=task_data["location_description"],
            longitude=task_data["location_longitude"],
            latitude=task_data["location_latitude"],

        ) if task_data.get("location_id") else None
    )
    return task


async def delete_task(task_id: str) -> None:
    await async_redis.delete(f"task:{task_id}")
    await async_redis.zrem("tasks", task_id)


async def fetch_tasks() -> List[Task]:
    task_ids: list[bytes] = await async_redis.zrange("tasks", 0, -1)
    tasks = []
    for task_id in task_ids:
        task = await fetch_task(task_id.decode())
        tasks.append(task)
    return tasks


def exclude_self(location_id: str, locations_near_me: List[Location]) -> List[Location]:
    return list(filter(lambda location: location.id != location_id, locations_near_me))
