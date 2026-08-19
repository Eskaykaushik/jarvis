import json
import logging
import time

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_get_stale(key: str, max_age: int = 86400) -> dict | None:
    data = await cache_get(key)
    if data is None:
        return None
    age = time.time() - data.get("timestamp", 0)
    if age > max_age:
        return None
    return data


async def cache_set(key: str, value: str, ttl: int, model: str = "", provider: str = ""):
    r = await get_redis()
    payload = json.dumps({
        "response": value,
        "model": model,
        "provider": provider,
        "timestamp": time.time(),
    })
    await r.set(key, payload, ex=ttl)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


async def cache_health() -> bool:
    try:
        r = await get_redis()
        await r.ping()
        return True
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        return False


# --- Resilient variants: degrade gracefully when Redis is unavailable ---
# These never raise; callers use them to keep core flows (chat, summary,
# conversation lookup) working even when the cache layer is down.


class RedisUnavailableError(RuntimeError):
    """Raised when a caller needs a hard Redis guarantee (e.g. conversation
    lookup) and Redis is unreachable."""


async def cache_get_safe(key: str) -> dict | None:
    try:
        return await cache_get(key)
    except Exception as e:
        logger.warning("cache_get failed for %s: %s", key, e)
        return None


async def cache_get_stale_safe(key: str, max_age: int = 86400) -> dict | None:
    try:
        return await cache_get_stale(key, max_age)
    except Exception as e:
        logger.warning("cache_get_stale failed for %s: %s", key, e)
        return None


async def cache_set_safe(key: str, value: str, ttl: int, model: str = "", provider: str = ""):
    try:
        await cache_set(key, value, ttl, model=model, provider=provider)
    except Exception as e:
        logger.warning("cache_set failed for %s: %s", key, e)


async def cache_delete_safe(key: str):
    try:
        await cache_delete(key)
    except Exception as e:
        logger.warning("cache_delete failed for %s: %s", key, e)


async def get_redis_safe() -> aioredis.Redis | None:
    """Returns the Redis client, or None if it cannot be reached."""
    try:
        r = await get_redis()
        await r.ping()
        return r
    except Exception as e:
        logger.warning("Redis unavailable: %s", e)
        return None
