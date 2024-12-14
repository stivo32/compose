FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

# poetry default path
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry export -f requirements.txt --without-hashes -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl && apt-get clean

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./task_manager /app/task_manager

EXPOSE 8000

CMD ["uvicorn", "task_manager.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
