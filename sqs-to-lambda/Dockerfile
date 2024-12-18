FROM python:3.12-alpine

RUN pip install boto3 requests

WORKDIR /app

COPY ./sqs-to-lambda/main.py /app/main.py

CMD [ "python", "main.py" ]