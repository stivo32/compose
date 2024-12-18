import boto3
import os

os.environ['AWS_ACCESS_KEY_ID'] = 'fakeMyKeyId'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fakeSecretAccessKey'


dynamodb = boto3.resource(
    'dynamodb',
    region_name='eu-west-2',
    endpoint_url='http://localhost:8000'
)

table_name = 'newsletter'


def insert_item():
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            'email': 'test@example.com',
        }
    )
    print('Item added')


def get_items():
    table = dynamodb.Table(table_name)
    response = table.get_item(
        Key={
            'email': 'test@example.com'
        }
    )

    print(f'Item received, {response.get("Item")}')


def main():
    insert_item()
    get_items()


if __name__ == '__main__':
    main()