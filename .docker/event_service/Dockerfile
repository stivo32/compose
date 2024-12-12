FROM python:3.12-alpine

WORKDIR /app

RUN pip install redis prometheus-client

COPY ./event_service/*.py /app

CMD ["python", "main.py"]