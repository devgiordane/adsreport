"""Simple SQLite-backed cache with TTL + in-memory LRU for hot paths."""

from __future__ import annotations

import functools
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, TypeVar

from adsreport.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")

_memory_cache: dict[str, tuple[Any, datetime]] = {}


def get_or_compute(key: str, fn: Callable[[], T], ttl_seconds: int = 300) -> T:
    now = datetime.now(tz=timezone.utc)
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if expires_at > now:
            return value  # type: ignore[return-value]

    value = fn()
    _memory_cache[key] = (value, now + timedelta(seconds=ttl_seconds))
    logger.debug("cache_miss", key=key, ttl=ttl_seconds)
    return value  # type: ignore[return-value]


def invalidate(key: str) -> None:
    _memory_cache.pop(key, None)


def invalidate_prefix(prefix: str) -> None:
    for k in list(_memory_cache.keys()):
        if k.startswith(prefix):
            del _memory_cache[k]


def clear_all() -> None:
    _memory_cache.clear()
