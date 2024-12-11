import os
import redis
import logging

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
)

STREAM = "task-stream"
CONSUMER_GROUP = "analytics-group"
CONSUMER = "analytics-consumer"


try:
    client.xgroup_create(name=STREAM, groupname=CONSUMER_GROUP, id='0', mkstream=True)
    logger.info(f"Consumer group '{CONSUMER_GROUP}' created for stream '{STREAM}'")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" in str(e):
        logger.info(f"Consumer group '{CONSUMER_GROUP}' already exists.")
    else:
        raise

while True:
    try:
        entries = client.xreadgroup(
            groupname=CONSUMER_GROUP,
            consumername=CONSUMER,
            streams={STREAM: '>'},
            count=1,
            block=0
        )

        for stream_name, messages in entries:
            for message_id, message in messages:
                task_id = message.get(b'task_id')
                timestamp = message.get(b'timestamp')
                location_id = message.get(b'location_id')

                logger.info(f"Received task_id={task_id}, timestamp={timestamp}, location_id={location_id}")

                client.xack(STREAM, CONSUMER_GROUP, message_id)
    except Exception as e:
        logger.error(f"Error processing stream: {e}")
