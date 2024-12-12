from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter, Histogram
from starlette.requests import Request

from task_manager.task.task import router as task_router

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)


metrics_app = make_asgi_app()
app = FastAPI()
app.mount('/metrics', metrics_app)

app.include_router(task_router)


@app.middleware('http')
async def collect_metrics(request: Request, call_next):
    with REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).time():
        response = await call_next(request)

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response
