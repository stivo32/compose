import json
import os
from dataclasses import dataclass
from typing import Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

DYNAMODB_ENDPOINT_ENV = "DYNAMODB_ENDPOINT"
SQS_TOPIC_ENV = "SQS_TOPIC"
SIMULATED_ENV = "SIMULATED"
AWS_REGION_ENV = "AWS_DEFAULT_REGION"
SQS_ENDPOINT_ENV = "SQS_ENDPOINT"

TABLE_NAME = "newsletter"


@dataclass
class Subscribe:
    email: str
    topic: str


def is_simulated() -> bool:
    value = os.getenv(SIMULATED_ENV, "").lower()
    return value == "true"


def dynamo_db_session():
    if is_simulated():
        return boto3.resource(
            "dynamodb",
            endpoint_url=os.getenv(DYNAMODB_ENDPOINT_ENV),
            region_name=os.getenv(AWS_REGION_ENV),
        )
    return boto3.resource("dynamodb")


def sqs_session():
    return boto3.client(
        "sqs",
        endpoint_url=os.getenv(SQS_ENDPOINT_ENV),
        region_name=os.getenv(AWS_REGION_ENV),
    )


def send_to_sqs(subscribe: Subscribe):
    if not is_simulated():
        return

    sqs = sqs_session()
    try:
        message_body = json.dumps(subscribe.__dict__)
        sqs.send_message(
            QueueUrl=os.getenv(SQS_TOPIC_ENV),
            MessageBody=message_body,
        )
    except (BotoCoreError, ClientError) as e:
        print(f"Error sending to SQS: {str(e)}")


def handle_request(event: Dict, context):
    subscribe = Subscribe(email=event["email"], topic=event["topic"])
    try:
        dynamodb = dynamo_db_session()
        table = dynamodb.Table(TABLE_NAME)

        table.put_item(Item=subscribe.__dict__)
        send_to_sqs(subscribe)

        return {
            "statusCode": 200,
            "body": f"You have been subscribed to the {subscribe.topic} newsletter",
        }
    except (BotoCoreError, ClientError) as e:
        return {
            "statusCode": 500,
            "body": f"Could not process request: {str(e)}",
        }


if __name__ == "__main__":
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.logging.logger import Logger
    from aws_lambda_powertools import Tracer

    logger = Logger()
    tracer = Tracer()

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event: Dict, context: LambdaContext):
        return handle_request(event, context)
