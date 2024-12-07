import os


def get_env(var_name: str, default: str) -> str:
    return os.getenv(var_name, default)


def get_int_env(var_name: str, default: int) -> int:
    return int(get_env(var_name, str(default)))


def decode_redis_data(data: dict) -> dict:
    return {key.decode(): value.decode() if isinstance(value, bytes) else value for key, value in data.items()}
