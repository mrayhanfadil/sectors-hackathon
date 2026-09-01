import os
import pathlib
import re

# Inherit env vars from ~/.hermes/.env or .env if not in current os.environ
for _p in (
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
from .stockdata import get_stockdata
from .routers.endpoints import router_health, router_report, router_outlook, router_news, router_sentiment, router_challenge
from .routers.agent import router_agent
from .routers.mock_sectors import router_mock_sectors

try:
    from .routers.pdf import router_pdf  # type: ignore
except Exception:
    router_pdf = None  # type: ignore

log = logging.getLogger(__name__)
_started = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # init cache + stockdata pool
    cache = get_cache(settings.cache_ttl)
    sd = get_stockdata()
    try:
        await sd.startup()
    except Exception as e:
        log.warning(f"stockdata startup failed (will fallback yfinance): {e}")
    log.info(f"server up — cache ttl {settings.cache_ttl}s, stockdata {settings.stockdata_url}")
    yield
    try:
        await sd.shutdown()
    except Exception:
        pass
    log.info("server down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Sectors Institutional Report — API",
        version="t04-0.1.0",
        description=(
            "Backend solid for Institutional-Grade Equity Report (T03 Market Intelligence). "
            "Proxies stockdata:15437 (T01 collector), yfinance .JK fallback, Sectors v2 gated P2. "
            "Engines deterministic Python (DCF/DDM/SOTP/blended/bands/GGM). Cache KV 4h."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    # CORS — allow Vite + Pages.dev (regex handles *.pages.dev preview deploys)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Type"],
    )

    # routers — 6 endpoints per T04 spec + ADK agent stream
    app.include_router(router_health, tags=["health"])
    app.include_router(router_report, tags=["report"])
    app.include_router(router_outlook, tags=["outlook"])
    app.include_router(router_news, tags=["news"])
    app.include_router(router_sentiment, tags=["sentiment"])
    app.include_router(router_challenge, tags=["challenge"])
    app.include_router(router_agent, tags=["agent"])
    app.include_router(router_mock_sectors, prefix="/api/mock", tags=["mock-sectors"])
    if router_pdf is not None:
        app.include_router(router_pdf, tags=["pdf"])

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "Sectors Institutional Report API",
            "docs": "/docs",
            "health": "/api/health",
            "endpoints": [
                "/api/report/{ticker}",
                "/api/outlook",
                "/api/news?ticker=BBCA",
                "/api/sentiment?ticker=BBCA",
                "/api/challenge (POST)",
                "/api/agent/health",
                "/api/agent/stream?ticker=BBCA (SSE live trace)",
                "/api/agent/run (POST)",
                "/api/health",
            ],
        }

    return app


app = create_app()
