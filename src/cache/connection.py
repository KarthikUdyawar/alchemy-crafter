"""
Redis connection — single shared client instance.
"""

import redis
from src.config import config

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Return the shared Redis client, creating it on first call."""
    global _client
    if _client is None:
        _client = redis.from_url(
            config.REDIS_URL,
            decode_responses=True,  # always return str, not bytes
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client
