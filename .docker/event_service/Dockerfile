FROM python:3.12-alpine

WORKDIR /app

RUN pip install redis

COPY ./event_service/*.py /app

CMD ["python", "main.py"]