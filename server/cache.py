"""KV cache 4h — in-memory TTL + Cloudflare KV placeholder (P2).
Spec 4 + T04 task 1: cache KV 4h, stockdata pool reuse.
P0-P1: pure in-memory. P2: swap backend to Cloudflare KV via REST without changing call sites.
"""
import time
import asyncio
from typing import Any, Optional


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

    async def stats(self) -> dict:
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
