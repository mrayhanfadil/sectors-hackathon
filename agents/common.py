"""Shared helpers for T08 agents (Writer / Visualizer / SOTP Aggregator).

Pure, deterministic, no network. Every rendered number must trace to the input
company.json (or a scripts/ engine result) — anti-hallucination contract.

Path conventions:
    repo/
      agents/            <- this package
      out/<ticker>/      <- per-ticker output (thesis.json, sotp.json, charts/, charts.json)
      tests/fixtures/company/<ticker>.json
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO_ROOT, "out")
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "company")
SOURCE_BOOK = os.path.join(REPO_ROOT, "references", "source-library.md")

ENGINE_VERSION = "t08-writer-visualizer-sotp v1 (31 Aug 2026)"

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def company_path(ticker: str) -> str:
    """Resolve company.json: out/<ticker>/company.json if present (T01 output),
    else tests/fixtures/company/<ticker>.json (deterministic fallback)."""
    ticker = ticker.upper()
    live = os.path.join(OUT_DIR, ticker, "company.json")
    if os.path.exists(live):
        return live
    fixture = os.path.join(FIXTURES_DIR, f"{ticker}.json")
    if os.path.exists(fixture):
        return fixture
    raise FileNotFoundError(
        f"No company.json for {ticker}: tried {live} and {fixture}"
    )


def load_company(ticker: str) -> dict[str, Any]:
    with open(company_path(ticker), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_financials(ticker: str) -> dict[str, Any] | None:
    """Optional T02 modeler output that enriches the visualizer (ratio trajectories)."""
    path = os.path.join(OUT_DIR, ticker, "financials.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return None


# ---------------------------------------------------------------------------
# Provenance / source labeling
# ---------------------------------------------------------------------------

PRIMARY_SOURCES = {
    "idx": "IDX / company filings",
    "sectors": "Sectors API v2",
    "yfinance": "Sectors API v2 (legacy label)",
    "broker": "broker research (BCA Sekuritas / KSI)",
    "synthetic": "synthetic (seed=42, disclosed — IDX fundamentals gap)",
    "news": "news harvester (T01)",
    "sentiment": "social sentiment (T01)",
}


def source_label(company: dict[str, Any]) -> str:
    primary = company.get("source", {})
    key = primary.get("primary", "idx")
    label = PRIMARY_SOURCES.get(key, key)
    extra = primary.get("label")
    if extra:
        # avoid duplication when the label already carries the source name
        if extra.startswith(label):
            return str(extra)
        return f"{label} — {extra}"
    return label


def data_fingerprint(company: dict[str, Any]) -> str:
    """Short stable hash of the input so output provenance can be audited."""
    blob = json.dumps(company, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------


def ensure_out(ticker: str, sub: str | None = None) -> str:
    ticker = ticker.upper()
    base = os.path.join(OUT_DIR, ticker)
    if sub:
        base = os.path.join(base, sub)
    os.makedirs(base, exist_ok=True)
    return str(base)


def write_json(path: str, payload: dict[str, Any]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def write_markdown(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


# ---------------------------------------------------------------------------
# Small deterministic math helpers (no numpy dependency for callers)
# ---------------------------------------------------------------------------


def pct_delta(new: float, old: float) -> float:
    """Percent change new vs old, as a number (e.g. -72.0 for a 72% decline)."""
    if old == 0:
        raise ValueError("pct_delta: old value is 0")
    return round((new - old) / old * 100.0, 2)


def fmt_idr(value: float, unit: str = "mn") -> str:
    """Format IDR values: 420000.0 mn -> 'IDR 420bn' (compact for thesis prose)."""
    if unit == "bn":
        return f"IDR {value / 1000.0:,.1f}bn"
    if abs(value) >= 1e6:  # >= IDR 1tn in mn units
        return f"IDR {value / 1e6:,.1f}tn"
    if abs(value) >= 1e3:  # >= IDR 1bn in mn units
        return f"IDR {value / 1e3:,.1f}bn"
    return f"IDR {value:,.0f} mn"


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100.0:.{digits}f}%"


def x_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}x"
