from typing import Any
from app.application.common.cache import CacheService

class MemoryCacheService(CacheService):
    def __init__(self):
        self._cache: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    async def clear_prefix(self, prefix: str) -> None:
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._cache[k]
