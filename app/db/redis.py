import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    _pool: redis.Redis | None = None

    @classmethod
    def get_pool(cls) -> redis.Redis:
        if cls._pool is None:
            cls._pool = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

async def get_redis() -> redis.Redis:
    return RedisClient.get_pool()
