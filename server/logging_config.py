"""Logging Configuration, Request Logging Middleware, and Per-IP Rate Limiting.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Any, Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from server.report import numfmt as _nf

logger = logging.getLogger("sectors.api")


def setup_logging(level: int = logging.INFO) -> None:
    """Setup structured console logging for production."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


# ── Per-IP Sliding-Window Rate Limiter (60 req/min) ──────────────────────────

class RateLimiter:
    """Thread-safe and async-safe in-memory sliding-window rate limiter per client IP."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._history: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> tuple[bool, int, int]:
        """Check if client_ip is within rate limit.
        Returns: (allowed: bool, remaining: int, retry_after_s: int)
        """
        now = time.time()
        window_start = now - 60.0
        async with self._lock:
            # Clean up old timestamps for this IP
            timestamps = self._history.get(client_ip, [])
            valid_timestamps = [t for t in timestamps if t > window_start]

            if len(valid_timestamps) >= self.rpm:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(60.0 - (now - oldest)))
                self._history[client_ip] = valid_timestamps
                return False, 0, retry_after

            valid_timestamps.append(now)
            self._history[client_ip] = valid_timestamps
            remaining = self.rpm - len(valid_timestamps)

            # Periodic cleanup of stale IPs if store grows large
            if len(self._history) > 5000:
                for ip in list(self._history.keys()):
                    if ip != client_ip and (not self._history[ip] or self._history[ip][-1] <= window_start):
                        del self._history[ip]

            return True, remaining, 0

    async def reset(self) -> None:
        """Reset rate limiter history."""
        async with self._lock:
            self._history.clear()


rate_limiter = RateLimiter(requests_per_minute=60)


def get_client_ip(request: Request) -> str:
    """Extract client IP from Cloudflare tunnel headers or client connection."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    x_fwd = request.headers.get("x-forwarded-for")
    if x_fwd:
        return x_fwd.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


# ── Middleware: Request Logging & Rate Limiting ──────────────────────────────

class ProductionHardeningMiddleware(BaseHTTPMiddleware):
    """Middleware for request latency logging and 60 req/min per-IP rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        client_ip = get_client_ip(request)
        path = request.url.path
        method = request.method

        # 1. Rate Limiting Check (applies to /api/* requests)
        allowed, remaining, retry_after = True, 60, 0
        if path.startswith("/api/"):
            allowed, remaining, retry_after = await rate_limiter.is_allowed(client_ip)
            if not allowed:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                logger.warning(
                    f"[RATE_LIMIT_EXCEEDED] {method} {path} ip={client_ip} status=429 latency_ms={_nf.dec(latency_ms, digits=2)}ms"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded: 60 requests per minute per IP",
                        "error": "rate_limit_exceeded",
                        "retry_after_seconds": retry_after,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": "60",
                        "X-RateLimit-Remaining": "0",
                        "Cache-Control": "no-store",
                    },
                )

        # 2. Forward request
        response: Response = await call_next(request)

        # 3. Add Rate Limit & Cache Headers
        response.headers["X-RateLimit-Limit"] = "60"
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 4. Request Logging
        query_params = request.query_params
        ticker = query_params.get("symbol") or query_params.get("symbols") or query_params.get("ticker") or "-"

        if path.startswith("/api/mock"):
            logger.info(
                f"[MOCK_API] {method} {path} ticker={ticker} status={response.status_code} latency_ms={_nf.dec(latency_ms, digits=2)}ms ip={client_ip}"
            )
        elif path.startswith("/api/"):
            logger.info(
                f"[API] {method} {path} status={response.status_code} latency_ms={_nf.dec(latency_ms, digits=2)}ms ip={client_ip}"
            )

        return response
