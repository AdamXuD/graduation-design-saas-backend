from redis.asyncio import ConnectionPool, Redis

# TODO 待反常量化
pool = ConnectionPool(host='localhost', port=6379, db=0)


def SessionRedis() -> Redis:
    return Redis(connection_pool=pool)
