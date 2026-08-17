import hashlib
import json
import logging
import time
from typing import Any, Optional
import uuid

from app.core.config import settings

logger = logging.getLogger("otoichi.cache")


class MemoryCache:
    """Thread-safe in-memory fallback cache with TTL expiration."""

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}

    async def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if not entry:
            return None
        raw_val, expire_at = entry
        if time.time() > expire_at:
            self._store.pop(key, None)
            return None
        return raw_val

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        expire_at = time.time() + ttl
        self._store[key] = (value, expire_at)
        return True

    async def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    async def delete_pattern(self, pattern: str) -> int:
        prefix = pattern.rstrip("*")
        keys_to_del = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_del:
            self._store.pop(k, None)
        return len(keys_to_del)

    async def flush(self) -> None:
        self._store.clear()


class CacheService:
    """
    Resilient Cache Service supporting Redis (Upstash / Redis Cloud)
    with automatic in-memory fallback, deterministic versioned keys,
    and granular invalidation.
    """

    def __init__(self):
        self._redis = None
        self._memory = MemoryCache()
        self._hits = 0
        self._misses = 0
        self._errors = 0
        self._redis_initialized = False

    def _get_redis_client(self):
        if not settings.CACHE_ENABLED or not settings.REDIS_URL:
            return None

        if not self._redis_initialized:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=1.5,
                    socket_connect_timeout=2.0,
                    retry_on_timeout=True,
                )
                self._redis_initialized = True
                logger.info("Connected to Redis cache at %s", settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "configured host")
            except Exception as e:
                logger.warning("Failed to initialize Redis client, using in-memory cache fallback: %s", e)
                self._redis = None
                self._redis_initialized = True
        return self._redis

    @staticmethod
    def make_key(prefix: str, **kwargs) -> str:
        """
        Create a deterministic, collision-free, versioned cache key.
        Example: make_key('products:v1', page=1, limit=20, genre='Jazz')
        """
        filtered = {k: str(v) for k, v in sorted(kwargs.items()) if v is not None and v != ""}
        if not filtered:
            return prefix
        param_str = "&".join(f"{k}={v}" for k, v in filtered.items())
        param_hash = hashlib.md5(param_str.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}:{param_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize value from cache."""
        if not settings.CACHE_ENABLED:
            return None

        redis_client = self._get_redis_client()
        raw_val = None

        if redis_client:
            try:
                raw_val = await redis_client.get(key)
            except Exception as e:
                self._errors += 1
                logger.warning("Redis GET error on key '%s', falling back to memory: %s", key, e)
                raw_val = await self._memory.get(key)
        else:
            raw_val = await self._memory.get(key)

        if raw_val is not None:
            self._hits += 1
            try:
                return json.loads(raw_val)
            except Exception:
                return raw_val

        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Serialize and store value with specified TTL (in seconds)."""
        if not settings.CACHE_ENABLED:
            return False

        def _json_serial(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            if hasattr(obj, "model_dump"):
                return obj.model_dump(mode="json")
            if hasattr(obj, "dict"):
                return obj.dict()
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            if isinstance(value, str):
                serialized = value
            else:
                serialized = json.dumps(value, default=_json_serial)
        except Exception as e:
            logger.warning("Failed to serialize cache value for key '%s': %s", key, e)
            return False

        redis_client = self._get_redis_client()
        if redis_client:
            try:
                await redis_client.set(key, serialized, ex=ttl)
                # Also mirror in memory for rapid local reads
                await self._memory.set(key, serialized, ttl=ttl)
                return True
            except Exception as e:
                self._errors += 1
                logger.warning("Redis SET error on key '%s', using memory cache: %s", key, e)
                return await self._memory.set(key, serialized, ttl=ttl)
        else:
            return await self._memory.set(key, serialized, ttl=ttl)

    async def delete(self, key: str) -> bool:
        """Delete specific key from Redis and memory."""
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as e:
                self._errors += 1
                logger.warning("Redis DELETE error on key '%s': %s", key, e)
        return await self._memory.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a wildcard pattern (e.g. 'products:v1:*')."""
        deleted_count = 0
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                if keys:
                    deleted_count = await redis_client.delete(*keys)
            except Exception as e:
                self._errors += 1
                logger.warning("Redis SCAN/DELETE error on pattern '%s': %s", pattern, e)

        mem_deleted = await self._memory.delete_pattern(pattern)
        return max(deleted_count, mem_deleted)

    async def invalidate_product(self, product_id: Optional[uuid.UUID] = None) -> None:
        """Targeted invalidation for catalog listings and single product details."""
        if product_id:
            await self.delete(f"product:v1:{product_id}")
        await self.delete_pattern("products:v1:*")
        await self.delete_pattern("homepage:v1:*")

    async def invalidate_album(self, album_id: Optional[uuid.UUID] = None) -> None:
        """Targeted invalidation for album listings and single album details."""
        if album_id:
            await self.delete(f"album:v1:{album_id}")
        await self.delete_pattern("albums:v1:*")
        await self.delete_pattern("homepage:v1:*")

    def get_metrics(self) -> dict:
        """Observability telemetry for cache performance."""
        total = self._hits + self._misses
        hit_ratio = round((self._hits / total * 100), 2) if total > 0 else 0.0
        return {
            "backend": "redis" if self._get_redis_client() else "memory",
            "enabled": settings.CACHE_ENABLED,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "hit_ratio_percent": hit_ratio,
        }


# Global singleton instance
cache_service = CacheService()
