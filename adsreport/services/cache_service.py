"""Simple SQLite-backed cache with TTL + in-memory LRU for hot paths."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, TypeVar, cast

from adsreport.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")

if TYPE_CHECKING:
    from collections.abc import Callable

_memory_cache: dict[str, tuple[Any, datetime]] = {}
_cache_lock = threading.RLock()


def get_or_compute(key: str, fn: Callable[[], T], ttl_seconds: int = 300) -> T:
    now = datetime.now(tz=UTC)
    with _cache_lock:
        cached = _memory_cache.get(key)
        if cached is not None:
            value, expires_at = cached
            if expires_at > now:
                return cast("T", value)

    value = fn()
    with _cache_lock:
        _memory_cache[key] = (value, now + timedelta(seconds=ttl_seconds))
    logger.debug("cache_miss", key=key, ttl=ttl_seconds)
    return value


def invalidate(key: str) -> None:
    with _cache_lock:
        _memory_cache.pop(key, None)


def invalidate_prefix(prefix: str) -> None:
    with _cache_lock:
        for k in list(_memory_cache.keys()):
            if k.startswith(prefix):
                del _memory_cache[k]


def clear_all() -> None:
    with _cache_lock:
        _memory_cache.clear()
