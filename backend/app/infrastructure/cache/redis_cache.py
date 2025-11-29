import json
from typing import Any
from redis.asyncio import Redis
from app.application.common.cache import CacheService

class RedisCacheService(CacheService):
    def __init__(self, redis: Redis):
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        val = await self._redis.get(key)
        if val:
            return json.loads(val)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        # Use default serializer (json)
        # For complex objects, we might need Pydantic .model_dump_json() before calling this
        await self._redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def clear_prefix(self, prefix: str) -> None:
        keys = await self._redis.keys(f"{prefix}*")
        if keys:
            await self._redis.delete(*keys)
