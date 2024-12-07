from fastapi import FastAPI

from task_manager.task.task import router as task_router

app = FastAPI()

app.include_router(task_router)
