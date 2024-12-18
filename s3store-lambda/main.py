import os
import json
import hashlib
import time
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Dict
from aws_lambda_powertools.utilities.typing import LambdaContext


SUBSCRIPTION_BUCKET_ENV = "SUBSCRIPTION_BUCKET"
SIMULATED_ENV = "SIMULATED"
S3_ENDPOINT_ENV = "S3_ENDPOINT"
AWS_REGION_ENV = "AWS_DEFAULT_REGION"


def hash_email(email: str) -> str:
    return hashlib.md5(email.encode('utf-8')).hexdigest()


def is_simulated() -> bool:
    return os.getenv(SIMULATED_ENV, "").lower() == "true"


def s3_session():
    if is_simulated():
        return boto3.client(
            "s3",
            endpoint_url=os.getenv(S3_ENDPOINT_ENV),
            region_name=os.getenv(AWS_REGION_ENV),
        )
    return boto3.client("s3", region_name=os.getenv(AWS_REGION_ENV))


def handle_request(event: Dict, context: LambdaContext):
    s3 = s3_session()

    for record in event["Records"]:
        try:
            message_body = record["Body"]
            subscribe = json.loads(message_body)

            key = f"{hash_email(subscribe['email'])}.{int(time.time() * 1000)}"

            s3.put_object(
                Bucket=os.getenv(SUBSCRIPTION_BUCKET_ENV),
                Key=key,
                Body=json.dumps(subscribe),
            )

            print("Stored SQS event")
        except (BotoCoreError, ClientError) as e:
            print(f"Error storing SQS event: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    return {"statusCode": 200, "body": "Processed successfully"}


if __name__ == "__main__":
    from aws_lambda_powertools.logging.logger import Logger
    from aws_lambda_powertools.tracing import Tracer

    logger = Logger()
    tracer = Tracer()

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event: Dict, context: LambdaContext):
        return handle_request(event, context)
