import os

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

os.environ['AWS_ACCESS_KEY_ID'] = 'fakeMyKeyId'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fakeSecretAccessKey'


def list_s3_buckets():
    try:
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9090'
        )

        response = s3.list_buckets()

        print("Available buckets:")
        for bucket in response['Buckets']:
            print(f"- {bucket['Name']}")
    except NoCredentialsError:
        print("Error: No AWS credentials provided.")
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    list_s3_buckets()