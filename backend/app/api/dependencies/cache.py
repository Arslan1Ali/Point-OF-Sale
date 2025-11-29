from fastapi import Depends
from redis.asyncio import Redis
from app.core.settings import get_settings
from app.infrastructure.cache.redis_cache import RedisCacheService
from app.infrastructure.cache.memory_cache import MemoryCacheService
from app.application.common.cache import CacheService

# Global memory cache instance to share across requests when Redis is unavailable
_memory_cache = MemoryCacheService()

async def get_redis() -> Redis | None:
    settings = get_settings()
    try:
        # decode_responses=True ensures we get strings back, not bytes
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return None

async def get_cache_service(redis: Redis | None = Depends(get_redis)) -> CacheService:
    if redis:
        return RedisCacheService(redis)
    return _memory_cache
