"""KV cache 4h - in-memory TTL + Cloudflare KV placeholder (P2)
and TTLCache (5m) for /api/mock/* endpoints with X-Cache HIT/MISS headers.

Cache versioning: gateway keys go through cache_key(), which prefixes
CACHE_VERSION - bump the version to instantly invalidate stale (e.g. pre-key)
entries. Flush procedure: restart the worker (in-memory store, nothing to purge).
"""
from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional
from fastapi import Response


# ── Cache versioning (stale-cache poisoning guard) ───────────────────────────
# Bump to instantly invalidate all gateway keys cached under an older version
# (e.g. payloads cached before SECTORS_API_KEY was configured).
CACHE_VERSION = "v2-sectors"


def cache_key(base: str) -> str:
    """Prefix a raw gateway cache key with CACHE_VERSION."""
    return f"{CACHE_VERSION}:{base}"


# ── Legacy KV Cache (for report / stockdata) ─────────────────────────────────

class KVCache:
    def __init__(self, ttl: int = 14400):
        self.ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        now = time.time()
        async with self._lock:
            hit = self._store.get(key)
            if not hit:
                return None
            exp, val = hit
            if now > exp:
                self._store.pop(key, None)
                return None
            return val

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        exp = time.time() + (ttl if ttl is not None else self.ttl)
        async with self._lock:
            self._store[key] = (exp, value)

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)

    async def stats(self) -> dict[str, Any]:
        now = time.time()
        async with self._lock:
            active = sum(1 for exp, _ in self._store.values() if exp > now)
            return {"entries": active, "ttl": self.ttl, "backend": "memory (KV P2 -> cloudflare)"}


_kv: Optional[KVCache] = None


def get_cache(ttl: int = 14400) -> KVCache:
    global _kv
    if _kv is None:
        _kv = KVCache(ttl=ttl)
    return _kv


# ── Mock Sectors TTL Cache (5 min / 300s) ────────────────────────────────────

def compute_cache_key(endpoint: str, ticker: str, params: dict[str, Any]) -> str:
    """Compute deterministic cache key in format '{endpoint}:{ticker}:{params_hash}'."""
    clean_ep = endpoint.strip("/")
    if "/" in clean_ep:
        clean_ep = clean_ep.split("/")[-1]
    clean_ticker = (ticker or "ALL").upper().strip().replace(".JK", "")

    # Filter out response/request objects and None values
    filtered: dict[str, Any] = {}
    for k, v in sorted(params.items()):
        if k in ("response", "request", "self") or v is None:
            continue
        if isinstance(v, (str, int, float, bool, list, dict)):
            filtered[k] = v
        else:
            filtered[k] = str(v)

    p_str = json.dumps(filtered, sort_keys=True)
    p_hash = hashlib.sha256(p_str.encode("utf-8")).hexdigest()[:16]
    return f"{clean_ep}:{clean_ticker}:{p_hash}"


class TTLCache:
    """Thread-safe and async-safe in-memory TTL cache with FIFO eviction."""

    def __init__(self, default_ttl: int = 300, maxsize: int = 2000):
        self.default_ttl = default_ttl
        self.maxsize = maxsize
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> tuple[bool, Optional[Any]]:
        """Retrieve key. Returns (hit: bool, value: Any)."""
        now = time.time()
        async with self._lock:
            if key not in self._store:
                return False, None
            exp, val = self._store[key]
            if now > exp:
                del self._store[key]
                return False, None
            return True, val

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value with expiration timestamp."""
        now = time.time()
        exp = now + (ttl if ttl is not None else self.default_ttl)
        async with self._lock:
            if len(self._store) >= self.maxsize:
                expired = [k for k, (e, _) in self._store.items() if e <= now]
                for k in expired:
                    del self._store[k]
                if len(self._store) >= self.maxsize:
                    first_k = next(iter(self._store))
                    del self._store[first_k]
            self._store[key] = (exp, value)

    async def delete(self, key: str) -> None:
        """Delete specific key."""
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._store.clear()

    async def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        now = time.time()
        async with self._lock:
            active = sum(1 for exp, _ in self._store.values() if exp > now)
            return {"entries": active, "ttl": self.default_ttl, "maxsize": self.maxsize}


_mock_cache = TTLCache(default_ttl=300)


def get_mock_cache(ttl: int = 300) -> TTLCache:
    global _mock_cache
    if _mock_cache is None:
        _mock_cache = TTLCache(default_ttl=ttl)
    return _mock_cache


def cached_endpoint(ttl: int = 300, endpoint_name: Optional[str] = None) -> Callable:
    """FastAPI endpoint decorator providing 5m TTL cache + X-Cache header."""
    def decorator(fn: Callable) -> Callable:
        ep_name = endpoint_name or fn.__name__.replace("get_", "")

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            response: Optional[Response] = kwargs.get("response")

            # Resolve ticker / symbols from kwargs
            ticker_val = kwargs.get("symbol") or kwargs.get("symbols") or kwargs.get("ticker") or "ALL"
            key = compute_cache_key(ep_name, str(ticker_val), kwargs)
            cache = get_mock_cache(ttl)

            # 1. Check cache hit
            hit, cached_val = await cache.get(key)
            if hit:
                if response is not None:
                    response.headers["X-Cache"] = "HIT"
                    response.headers["Cache-Control"] = "no-store"
                try:
                    from .routers.mock_sectors import record_successful_call
                    record_successful_call(endpoint_name or f"/api/mock/{ep_name}")
                except Exception:
                    pass
                return cached_val

            # 2. Cache miss: execute underlying endpoint handler
            result = await fn(*args, **kwargs)

            # Store result
            await cache.set(key, result, ttl=ttl)
            if response is not None:
                response.headers["X-Cache"] = "MISS"
                response.headers["Cache-Control"] = "no-store"

            try:
                from .routers.mock_sectors import record_successful_call
                record_successful_call(endpoint_name or f"/api/mock/{ep_name}")
            except Exception:
                pass
            return result

        return wrapper

    return decorator
