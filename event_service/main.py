import os
import time

import redis
import logging

from prometheus_client import Gauge, Counter, push_to_gateway, CollectorRegistry

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
PROMETHEUS_HOST = os.getenv("PUSH_GATEWAY_HOST", "push-gateway")
PROMETHEUS_PORT = os.getenv("PUSH_GATEWAY_PORT", "9091")

registry = CollectorRegistry()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
)


STREAM = "task-stream"
CONSUMER_GROUP = "analytics-group"
CONSUMER = "analytics-consumer"

TASK_COUNT = Counter(
    'task_event_processing_total',
    'Number of processed tasks',
    registry=registry
)

TASK_LATENCY = Gauge(
    'task_event_processing_duration',
    'Time it took to complete the task',
    registry=registry
)


def push_to_prometheus():
    url = f'http://{PROMETHEUS_HOST}:{PROMETHEUS_PORT}'
    logger.error(url)
    push_to_gateway(gateway=url, job='events_metrics', registry=registry)


def main():
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
                    with TASK_LATENCY.time():
                        task_id = message.get(b'task_id')
                        timestamp = message.get(b'timestamp')
                        location_id = message.get(b'location_id')

                        logger.info(f"Received task_id={task_id}, timestamp={timestamp}, location_id={location_id}")
                        logger.info('ACK')
                        client.xack(STREAM, CONSUMER_GROUP, message_id)
                    TASK_COUNT.inc()
            logger.error('HERE')
            push_to_prometheus()
        except Exception as e:
            logger.error(f"Error processing stream: {e}")


if __name__ == '__main__':
    main()