import os
import pathlib
import re

# Inherit env vars from ~/.hermes/.env, ~/.config/sectors-be/env, or .env if not in current os.environ
for _p in (
    pathlib.Path.home() / ".config" / "sectors-be" / "env",
    pathlib.Path(__file__).resolve().parents[1] / ".env",
    pathlib.Path(".env"),
    pathlib.Path.home() / ".hermes" / ".env",
    pathlib.Path.home() / ".env",
):
    if _p.exists():
        try:
            for _line in _p.read_text().splitlines():
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    if _k and _v:
                        os.environ.setdefault(_k, _v)
        except Exception:
            pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging

from .config import get_settings
from .cache import get_cache
from .logging_config import setup_logging, ProductionHardeningMiddleware
from .routers.endpoints import router_health, router_report, router_outlook, router_news, router_sentiment, router_challenge, router_dcf, router_universe
from .routers.agent import router_agent
from .routers.memory import router_memory
from .routers.mock_sectors import get_mock_sectors_status
from .startup import startup_hook, router_diagnostic

try:
    from .routers.pdf import router_pdf  # type: ignore
except Exception:
    router_pdf = None  # type: ignore

# Initialize structured logging
setup_logging()
log = logging.getLogger(__name__)
_started = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_hook()
    settings = get_settings()
    # init cache (Sectors-only; IDX Postgres pool killed Sep 2026)
    get_cache(settings.cache_ttl)
    log.info(f"server up — cache ttl {settings.cache_ttl}s (Sectors-only, no external pools)")
    yield
    log.info("server received shutdown signal (SIGTERM/SIGINT) — initiating graceful shutdown")
    log.info("server down — cleanup complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Sectors Institutional Report — API",
        version="t04-0.1.0",
        description=(
            "Backend solid for Institutional-Grade Equity Report (T03 Market Intelligence). "
            "Sectors v2 is the single market-data gateway (keyless -> honest 503 sectors_missing_key, no fallback). "
            "Engines deterministic Python (DCF/DDM/SOTP/blended/bands/GGM). Cache KV 4h."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    # Production Hardening Middleware: 60 req/min rate limiter + request latency logging
    app.add_middleware(ProductionHardeningMiddleware)

    # CORS — allow Vite + Pages.dev (regex handles *.pages.dev preview deploys)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Type", "X-Cache", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Enhanced health endpoint exposing mock sectors status, upstream sources, and last call timestamps
    @app.get("/api/health", summary="Health + cache + mock_sectors status", tags=["health"])
    async def health():
        cache = get_cache(settings.cache_ttl)
        mock_status = get_mock_sectors_status()
        return {
            "status": "ok",
            "uptime_s": round(time.time() - _started, 1),
            "cache": await cache.stats(),
            "version": "t04-0.1.0",
            "env": settings.env,
            "sectors_gate": "keyless (sectors_missing_key)" if not settings.sectors_api_key else "enabled",
            "mock_sectors_router": mock_status.get("mock_sectors_router", True),
            "registered_endpoints": mock_status.get("registered_endpoints", []),
            "endpoints": mock_status.get("endpoints", []),
            "upstream_sources": mock_status.get("upstream_sources", {}),
            "last_successful_call": mock_status.get("last_successful_call", {}),
            "mock_sectors": mock_status,
        }

    # routers — 6 endpoints per T04 spec + ADK agent stream
    app.include_router(router_health, tags=["health"])
    app.include_router(router_report, tags=["report"])
    app.include_router(router_outlook, tags=["outlook"])
    app.include_router(router_news, tags=["news"])
    app.include_router(router_sentiment, tags=["sentiment"])
    app.include_router(router_challenge, tags=["challenge"])
    app.include_router(router_agent, tags=["agent"])
    app.include_router(router_diagnostic)
    if router_pdf is not None:
        app.include_router(router_pdf, tags=["pdf"])
    app.include_router(router_dcf, tags=["dcf"])
    app.include_router(router_universe, tags=["universe"])
    app.include_router(router_memory, tags=["memory"])

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "Sectors Institutional Report API",
            "docs": "/docs",
            "health": "/api/health",
            "endpoints": [
                "/api/report/{ticker}",
                "/api/dcf/{ticker}",
                "/api/outlook",
                "/api/news?ticker=BBCA",
                "/api/sentiment?ticker=BBCA",
                "/api/challenge (POST)",
                "/api/agent/health",
                "/api/agent/stream?ticker=BBCA (SSE live trace)",
                "/api/agent/run (POST)",
                "/api/health",
                "/api/mock/filings?symbol=BBCA",
                "/api/mock/news?symbols=BBCA",
                "/api/mock/corporate-actions?symbol=BBCA",
                "/api/mock/quarterly-financials?symbol=BBCA",
            ],
        }

    return app


app = create_app()
