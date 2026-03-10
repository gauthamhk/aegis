import hashlib
import json
from typing import Any

import redis.asyncio as redis

from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    global _pool
    if not settings.redis_enabled:
        return None
    if _pool is None:
        try:
            _pool = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await _pool.ping()
            logger.info("redis.connected", url=settings.redis_url)
        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            logger.warning("redis.unavailable", error=str(e))
            _pool = None
            return None
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def _cache_key(prefix: str, text: str) -> str:
    h = hashlib.sha256(text.encode()).hexdigest()[:16]
    return f"aegis:{prefix}:{h}"


async def cache_get(prefix: str, text: str) -> dict | None:
    r = await get_redis()
    if r is None:
        return None
    try:
        key = _cache_key(prefix, text)
        data = await r.get(key)
        if data:
            logger.debug("cache.hit", prefix=prefix)
            return json.loads(data)
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.warning("cache.get_error", error=str(e))
    return None


async def cache_set(prefix: str, text: str, value: Any, ttl: int = 3600) -> None:
    r = await get_redis()
    if r is None:
        return
    try:
        key = _cache_key(prefix, text)
        await r.set(key, json.dumps(value, default=str), ex=ttl)
        logger.debug("cache.set", prefix=prefix, ttl=ttl)
    except redis.RedisError as e:
        logger.warning("cache.set_error", error=str(e))


async def cache_invalidate(prefix: str, text: str) -> None:
    r = await get_redis()
    if r is None:
        return
    try:
        key = _cache_key(prefix, text)
        await r.delete(key)
    except redis.RedisError as e:
        logger.warning("cache.invalidate_error", error=str(e))
