import os
import time
from typing import Optional, List
from uuid import uuid4

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger()


class TaskInput(BaseModel):
    name: str
    description: str


class Task(TaskInput):
    id: str
    timestamp: int


def get_env(var_name: str, default: str) -> str:
    return os.getenv(var_name, default)


def get_int_env(var_name: str, default: int) -> int:
    return int(get_env(var_name, default))


async_redis = redis.Redis(
    connection_pool=redis.BlockingConnectionPool(
        host=get_env("REDIS_HOST", "redis"),
        port=get_int_env("REDIS_PORT", 6379),
        db=get_int_env("REDIS_DB", 0),
    ),
)
app = FastAPI()


def decode_redis_data(data: dict) -> dict:
    return {key.decode(): value.decode() if isinstance(value, bytes) else value for key, value in data.items()}


async def persist_task(task: Task) -> None:
    task_key = f"task:{task.id}"
    await async_redis.hset(
        task_key,
        mapping=task.dict(),
    )
    await async_redis.zadd("tasks", {str(task.id): task.timestamp})


async def fetch_task(task_id: str) -> Optional[Task]:
    task_data = await async_redis.hgetall(f"task:{task_id}")
    if not task_data:
        return None
    task_data = decode_redis_data(task_data)
    return Task(
        id=task_data["id"],
        name=task_data["name"],
        description=task_data["description"],
        timestamp=int(task_data["timestamp"]),
    )


async def delete_task(task_id: str) -> None:
    await async_redis.delete(f"task:{task_id}")
    await async_redis.zrem("tasks", task_id)


async def fetch_tasks() -> List[Task]:
    task_ids: list[bytes] = await async_redis.zrange("tasks", 0, -1)
    tasks = []
    for task_id in task_ids:
        task = await fetch_task(task_id.decode())
        if task is None:
            continue
        tasks.append(task)
    return tasks


@app.get("/ping")
async def health_check():
    return {"message": "pong"}


@app.get("/task")
async def get_tasks():
    tasks = await fetch_tasks()
    return {"tasks": tasks}


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    task = await fetch_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task}


@app.post("/task")
async def create_task(task: TaskInput):
    task_id = str(uuid4())
    task_to_insert = Task(id=task_id, timestamp=int(time.time()), **task.dict())
    try:
        await persist_task(task_to_insert)
        return {"task": task_to_insert, "created": True, "message": "Task Created Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/task/{task_id}")
async def remove_task(task_id: str):
    try:
        await delete_task(task_id)
        return {"id": task_id, "message": "Task deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
