from redis.asyncio import ConnectionPool, Redis

from core.config import settings


pool = ConnectionPool.from_url(
    settings.REDIS_URI,
)


def SessionRedis() -> Redis:
    return Redis(connection_pool=pool)
