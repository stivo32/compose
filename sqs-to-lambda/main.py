import os
import time
import json
import logging
import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError

SQS_TOPIC_ENV = "SQS_TOPIC"
AWS_REGION_ENV = "AWS_DEFAULT_REGION"
SQS_ENDPOINT_ENV = "SQS_ENDPOINT"
S3STORE_LAMBDA_ENDPOINT_ENV = "S3STORE_LAMBDA_ENDPOINT"

logging.basicConfig(level=logging.INFO)


def sqs_session():
    return boto3.client(
        "sqs",
        endpoint_url=os.getenv(SQS_ENDPOINT_ENV),
        region_name=os.getenv(AWS_REGION_ENV),
    )


def main():
    sqs = sqs_session()
    queue_url = os.getenv(SQS_TOPIC_ENV)

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5
            )

            messages = response.get("Messages", [])
            if messages:
                logging.info(f"Dispatching {len(messages)} received messages")

                sqs_event = {"Records": messages}

                s3store_lambda_endpoint = os.getenv(S3STORE_LAMBDA_ENDPOINT_ENV)
                requests.post(
                    s3store_lambda_endpoint,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(sqs_event),
                )

                for message in messages:
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
        except (BotoCoreError, ClientError) as e:
            logging.error(f"Error interacting with SQS: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
