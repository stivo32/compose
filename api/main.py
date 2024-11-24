from typing import List, Dict

from fastapi import FastAPI
from pydantic import BaseModel


class Task(BaseModel):
    name: str
    description: str
    timestamp: int


app = FastAPI()

tasks: Dict[str, Task] = {}


@app.get('/task')
def read_tasks() -> dict:
    return {'tasks': list(tasks.values())}


@app.get('/task/{task_id}')
def read_task(task_id: str) -> dict:
    if task_id in tasks:
        return {'task': tasks[task_id]}
    else:
        return {'task_id': task_id, 'message': 'Not found'}


@app.post('/task/{task_id}')
def create_tasks(task_id: str, task: Task) -> dict:
    if task_id in tasks:
        return {'task_id': task_id, 'task': task, 'message': 'Already created', 'created': False}
    else:
        tasks[task_id] = task
        print(tasks)
        return {'task_id': task_id, 'task': task, 'message': 'Created successfully', 'created': True}


@app.delete('/task/{task_id}')
def delete_tasks(task_id: str) -> dict:
    if task_id in tasks:
        del tasks[task_id]
    return {'task_id': task_id, 'message': 'Deleted'}
