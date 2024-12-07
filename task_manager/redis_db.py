import redis.asyncio as redis

from task_manager.utils import get_env, get_int_env

async_redis = redis.Redis(
    connection_pool=redis.BlockingConnectionPool(
        host=get_env("REDIS_HOST", "redis"),
        port=get_int_env("REDIS_PORT", 6379),
        db=get_int_env("REDIS_DB", 0),
    ),
)