import boto3
import os

os.environ['AWS_ACCESS_KEY_ID'] = 'fakeMyKeyId'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fakeSecretAccessKey'


sqs = boto3.resource(
    'sqs',
    region_name='eu-west-2',
    endpoint_url='http://localhost:9324'
)

queue = sqs.create_queue(
    QueueName='MyQueue',
    Attributes={
        'DelaySeconds': '5',
        'VisibilityTimeout': '30'
    }
)
print(f"Очередь создана: {queue.url}")

# === Отправка Сообщения ===
response = queue.send_message(
    MessageBody='Привет из SQS!',
    MessageAttributes={
        'Sender': {
            'StringValue': 'MyApp',
            'DataType': 'String'
        }
    }
)
print(f"Сообщение отправлено! MessageId: {response.get('MessageId')}")

# === Получение Сообщений ===
for message in queue.receive_messages(
    MessageAttributeNames=['All'],    # Получить все атрибуты
    MaxNumberOfMessages=1,            # Получить максимум 1 сообщение
    WaitTimeSeconds=10                # Ожидание новых сообщений
):
    print(f"Получено сообщение: {message.body}")
    print(f"Атрибуты сообщения: {message.message_attributes}")

    # === Удаление Сообщения ===
    message.delete()
    print("Сообщение удалено.")

# === Удаление Очереди ===
queue.delete()
print("Очередь удалена.")