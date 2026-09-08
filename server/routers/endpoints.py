"""Routers — one per endpoint family. All handlers import engines via server.engines.
Data path: Sectors snapshot -> assumptions file -> deterministic engines (legacy removed).
Cache key: f"{prefix}:{ticker}" with TTL 4h.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Any
import time
import hashlib
import json
import copy
from pathlib import Path

from ..cache import cache_key, get_cache
from ..models import NewsResponse, NewsItem, SentimentResponse, SentimentItem
from ..config import get_settings

router_health = APIRouter()
router_report = APIRouter()
router_outlook = APIRouter()
router_news = APIRouter()
router_sentiment = APIRouter()
router_challenge = APIRouter()
router_universe = APIRouter()

_started = time.time()


# ---------- Archetype names (KILLED values, Sep 2026) ----------
# ARCHETYPE_DEFAULTS held per-ticker invented fundamentals (rf/beta/fcf/
# shares_out/last_price tuned to target fair values — fabrication). Killed in
# the no-fabrication sweep; only the valid archetype NAMES survive, used for
# _infer_archetype validation. Valuation inputs come exclusively from
# data/assumptions/{T}.json (LOUD 422 on gaps).
VALID_ARCHETYPES = frozenset({"infra", "single", "sotp", "bank", "coal", "unknown"})
# ---------- helpers ----------
def _now_iso() -> str:
    import datetime

    return datetime.datetime.utcnow().isoformat() + "Z"


def _rating_from_upside(upside: Optional[float]) -> str:
    if upside is None:
        return "HOLD"
    if upside >= 15:
        return "BUY"
    if upside >= 5:
        return "TRADING BUY"
    if upside <= -15:
        return "SELL"
    if upside <= -5:
        return "TRADING SELL"
    return "HOLD"


def _clean_ticker(ticker: str) -> str:
    """Normalize ticker: strip Refinitiv or Bloomberg suffix -> bare ticker."""
    t = ticker.upper().strip()
    ref_suffix = ".I" + "J"
    if t.endswith(ref_suffix):
        t = t[:-len(ref_suffix)]
    if t.endswith(".JK"):
        t = t[:-3]
    return t


def _infer_archetype(symbol: str, raw_json: dict | None = None) -> str:
    """Infer archetype dynamically from assumptions, peers, or Sectors sector data.

    Priority:
    1. Direct archetype in assumptions file (raw_json["archetype"])
    2. Inferred from peers metadata (sotp_pillars -> sotp, tower/fiber kpis -> infra, coal peers -> coal)
    3. Inferred from sector string (assumptions provenance.sector -> peers.json sector -> Sectors overview.sector):
       - telecom / tower / telecommunication -> infra
       - financials / banks / banking -> bank
       - energy / oil-gas / oil / gas -> single
       - conglomerate / multi-pilar / diversified -> sotp
       - coal / mining / basic-materials -> coal
    4. Fallback -> unknown
    """
    sym = _clean_ticker(symbol)

    # 1. Direct from raw_json
    if raw_json and isinstance(raw_json, dict):
        arch = raw_json.get("archetype")
        if arch and str(arch).lower() in VALID_ARCHETYPES:
            return str(arch).lower()

    # 2. Check data/peers.json metadata
    sector_cand = None
    peers_path = Path(__file__).resolve().parents[2] / "data" / "peers.json"
    if peers_path.exists():
        try:
            pdata = json.loads(peers_path.read_text(encoding="utf-8"))
            by_t = pdata.get("by_ticker", {}).get(sym, {})
            if by_t.get("archetype") and str(by_t["archetype"]).lower() in VALID_ARCHETYPES:
                return str(by_t["archetype"]).lower()
            if by_t.get("sotp_pillars"):
                return "sotp"
            if by_t.get("kpi"):
                kpis = [str(k).lower() for k in by_t["kpi"]]
                if any("tower" in k or "fiber" in k or "tenancy" in k for k in kpis):
                    return "infra"
            if by_t.get("peers"):
                peer_set = set(by_t["peers"])
                if peer_set & {"PTBA", "ITMG", "UNTR", "HRUM", "BYAN", "ADMR"}:
                    return "coal"
                if peer_set & {"TOWR", "TBIG", "ISAT", "EXCL", "TLKM"}:
                    return "infra"
                if peer_set & {"BBRI", "BMRI", "BBNI", "BRIS"}:
                    return "bank"
            sector_cand = by_t.get("sector")
        except Exception:
            pass

    # 3. Sector from raw_json provenance if not found
    if not sector_cand and raw_json and isinstance(raw_json, dict):
        sector_cand = raw_json.get("provenance", {}).get("sector") or raw_json.get("sector")

    # 4. Sectors company report (overview section) — the single sector source.
    # Keyless -> skip honestly; sector stays None -> "unknown" (never fabricated).
    if not sector_cand:
        try:
            from server.sectors import company_report
            rep = company_report(sym, "overview") or {}
            sector_cand = (
                rep.get("sector") or rep.get("industry")
                or (rep.get("overview") or {}).get("sector")
            )
        except Exception:
            pass

    if sector_cand:
        s = str(sector_cand).lower().strip()
        if any(k in s for k in ("telecom", "telecommunication", "tower", "infra", "infrastructure", "infrastructures", "utilities", "utility")):
            return "infra"
        if any(k in s for k in ("financial", "financials", "bank", "banks", "banking")):
            return "bank"
        if any(k in s for k in ("coal", "mining", "metals-and-mining", "basic-materials")):
            return "coal"
        if any(k in s for k in ("oil", "gas", "oil-gas", "oil & gas", "oil-and-gas", "energy")):
            return "single"
        if any(k in s for k in ("conglomerate", "conglomerates", "multi-pilar", "multi-pillar", "diversified", "holdco")):
            return "sotp"
        return "single"

    return "unknown"


def _template_for(ticker: str, segments: Optional[dict] = None, archetype: Optional[str] = None) -> str:
    """Derive template dynamically from archetype or segments."""
    arch = archetype or _infer_archetype(ticker)
    if arch == "infra":
        return "infra"
    if arch == "sotp":
        return "sotp"
    if segments and isinstance(segments, dict):
        segs = segments.get("segments") or segments.get("items") or []
        if isinstance(segs, list) and len(segs) > 1:
            return "sotp"
    return "single"


def _segments_for(archetype: str, assum: dict, sectors_segments: Optional[dict] = None) -> dict:
    """Enrich segments dictionary dynamically per archetype and assumptions."""
    if sectors_segments and isinstance(sectors_segments, dict):
        return sectors_segments
    if assum.get("segments") and isinstance(assum["segments"], dict):
        return assum["segments"]
    if not assum.get("has_assumptions_file", True):
        return {"segments": [], "total_pct": 0.0, "source": "no_assumptions_file"}

    # LOUD policy: no invented pillars — file/Sectors segments absent -> honest empty.
    return {
        "segments": [],
        "total_pct": 0.0,
        "source": "sectors_missing_key",
        "note": "segment breakdown unavailable: no segments in assumptions file or Sectors (no fabrication)",
    }


def _kpis_for(archetype: str, assum: dict) -> list[dict] | None:
    """Enrich KPI list dynamically per archetype and assumptions."""
    if assum.get("kpis") and isinstance(assum["kpis"], list):
        return assum["kpis"]
    if not assum.get("has_assumptions_file", True):
        return []

    # LOUD policy: no invented KPIs — file kpis absent -> honest empty.
    return []


def _cover_boxes_for(archetype: str, assum: dict) -> Optional[dict]:
    """Enrich cover boxes dynamically per archetype and assumptions."""
    if assum.get("cover_boxes") and isinstance(assum["cover_boxes"], dict):
        return assum["cover_boxes"]
    # LOUD policy: no invented takeaways/shareholders/esg — file cover_boxes absent -> honest empty.
    return {
        "source": "sectors_missing_key",
        "note": "cover boxes unavailable: no cover_boxes in assumptions file (no fabrication)",
    }


def _forecast_revision_for(archetype: str, assum: dict) -> Optional[dict]:
    """Enrich forecast revision dynamically per archetype and assumptions."""
    if assum.get("forecast_revision"):
        return assum["forecast_revision"]
    if not assum.get("has_assumptions_file", True):
        return None
    # LOUD policy: no invented revision narrative — file forecast_revision absent -> honest empty.
    return {
        "source": "sectors_missing_key",
        "note": "forecast revision unavailable: no forecast_revision in assumptions file (no fabrication)",
    }


def _quarterly_for(archetype: str, assum: dict) -> Optional[dict]:
    """Enrich quarterly breakdown dynamically per archetype and assumptions."""
    if assum.get("quarterly"):
        return assum["quarterly"]
    if not assum.get("has_assumptions_file", True):
        return None
    # LOUD policy: no invented quarterly narrative — file quarterly absent -> honest empty.
    return {
        "source": "sectors_missing_key",
        "note": "quarterly breakdown unavailable: no quarterly in assumptions file (no fabrication)",
    }


def _ggm_for(archetype: str, assum: dict, coe: float) -> Optional[dict]:
    """Enrich GGM model dynamically for bank archetype or when ROE is provided."""
    if archetype == "bank" or assum.get("roe") is not None:
        # LOUD policy: GGM needs file-present roe/g/bvps — absent -> omit, never default-invent.
        _roe = assum.get("roe")
        _g = assum.get("g")
        _bvps = assum.get("bvps")
        if _roe is None or _g is None or _bvps is None:
            return None
        try:
            from ..engines import ggm as calc_ggm
            return calc_ggm(_roe, _g, coe, _bvps)
        except Exception:
            return None
    return None


def _live_price(tkr: str, base_fallback: float | None) -> tuple[float | None, str]:
    """Try Sectors daily -> assumptions file -> base fixture. Returns (price, source_label)."""
    # 1) Sectors daily (live, last 14d window)
    try:
        from datetime import date as _date, timedelta as _td

        from ..sectors import daily as _sectors_daily

        _end = _date.today().isoformat()
        _start = (_date.today() - _td(days=14)).isoformat()
        rows = _sectors_daily(tkr, _start, _end) or {}
        items = rows.get("data") or rows.get("results") or []
        if isinstance(items, list) and items:
            last = items[-1] or {}
            for _k in ("close", "closing_price", "price"):
                if last.get(_k) is not None:
                    _px = float(last[_k])
                    if _px > 0:
                        return round(_px, 2), "sectors"
    except Exception:
        pass
    # 2) assumptions file (dated snapshot)
    try:
        ass = Path(__file__).resolve().parents[2] / "data" / "assumptions" / f"{tkr}.json"
        if ass.exists():
            d = json.loads(ass.read_text(encoding="utf-8"))
            prov = d.get("provenance") or {}
            if prov.get("close"):
                return float(prov["close"]), "assumptions:" + d.get("generated_at", "")
    except Exception:
        pass
    # 3) base fixture (last resort, honest label)
    return base_fallback, "sectors_missing_key"


def _assumptions_for(ticker: str) -> dict:
    """Load data/assumptions/{ticker}.json if exists (file values as-is, LOUD on gaps)."""
    t = _clean_ticker(ticker)
    p = Path(__file__).resolve().parents[2] / "data" / "assumptions" / f"{t}.json"
    raw_json = {}
    has_assumptions_file = False
    if p.exists():
        try:
            loaded = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                raw_json = loaded
                has_assumptions_file = True
        except Exception:
            pass

    archetype = _infer_archetype(t, raw_json)
    # LOUD policy: missing keys stay missing — file values as-is, never
    # silently filled (ARCHETYPE_DEFAULTS killed Sep 2026; every consumer
    # must handle absence loudly).
    base: dict[str, Any] = {}
    base["archetype"] = archetype
    base["has_assumptions_file"] = has_assumptions_file

    if has_assumptions_file:
        base["source"] = f"assumptions/{t}.json"
        for k, v in raw_json.items():
            if v is not None:
                base[k] = v
    else:
        base["source"] = "no_assumptions_file"

    if archetype == "bank" and has_assumptions_file:
        _live, _src = _live_price(t, base.get("last_price"))
        if _live is not None:
            base["last_price"] = _live
        base["price_source"] = _src

    return base


# ---------- health ----------
@router_health.get("/api/health", summary="Health + cache (Sectors-only)")
async def health():
    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    return {
        "status": "ok",
        "uptime_s": round(time.time() - _started, 1),
        "cache": await cache.stats(),
        "version": "t04-0.1.0",
        "env": settings.env,
        "sectors_gate": "P2 (disabled)" if not settings.sectors_api_key else "enabled",
    }


# ---------- tickers (Sectors screener, pending key) ----------
# IDX Postgres universe killed Sep 2026 (external source). Sectors screener
# wiring lands post-key; until then this endpoint is honest 503.
@router_universe.get("/api/tickers", summary="Ticker universe (Sectors screener, pending)")
async def tickers():
    # LOUD policy: IDX Postgres killed Sep 2026 (external source). Universe
    # comes from the Sectors screener post-key — honest 503 until then.
    raise HTTPException(status_code=503, detail="ticker universe unavailable (sectors screener pending): set SECTORS_API_KEY, then wire companies/?where=&order_by=")


# ---------- report/{ticker} ----------
async def _sectors_snapshot(t: str) -> dict:
    """Sectors-first market snapshot (swaps 2+4 scaffold).

    Returns {overview, financials, segments, price, source} with defensive
    extraction — unknown shapes yield empty (honest, never fabricated).
    Raises SectorsNotConfigured when keyless so callers fall through to the
    legacy path (deprecated, delete after env lands).
    """
    import asyncio
    from datetime import date, timedelta
    from server.sectors import (
        company_report, corporate_actions, daily, quarterly,
    )

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=14)).isoformat()
    rows = await asyncio.to_thread(daily, t, start, end)
    items = (rows or {}).get("data") or (rows or {}).get("results") or []
    price = None
    if isinstance(items, list) and items:
        last = items[-1] or {}
        for k in ("close", "closing_price", "price"):
            if last.get(k) is not None:
                price = float(last[k])
                break
    rep = await asyncio.to_thread(company_report, t, "overview,financials,dividend")
    rep = rep or {}
    fin = await asyncio.to_thread(quarterly, t, 4)
    fin = fin or {}
    acts = await asyncio.to_thread(corporate_actions, t)
    acts = acts or {}
    return {
        "overview": rep.get("overview") or rep or None,
        "financials": fin.get("data") or fin.get("results") or fin or None,
        "segments": None,
        "price": price,
        "source": "sectors",
        "dividends": (acts.get("dividend") or acts.get("dividends") or []),
    }


@router_report.get("/api/report/{ticker}", summary="Full equity report payload")
async def report_ticker(
    ticker: str,
    template: Optional[str] = Query(None, description="force single|sotp|infra|strategy"),
):
    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    t = _clean_ticker(ticker)
    if not t or len(t) > 10:
        raise HTTPException(400, "invalid ticker")
    ckey = cache_key(f"report:{t}:{template or 'auto'}")
    cached = await cache.get(ckey)
    if cached:
        cached["cached"] = True
        return cached

    overview = None
    financials = None
    segments = None
    price = None
    source = "sectors_missing_key"

    # Sectors-only (single gateway). Keyless -> honest sectors_missing_key below,
    # never a silent legacy fallback (legacy removed, Lane E).
    try:
        snap = await _sectors_snapshot(t)
        if snap.get("overview") or snap.get("financials") or snap.get("price") is not None:
            overview = snap.get("overview")
            financials = snap.get("financials")
            price = snap.get("price")
            source = "sectors"
    except Exception:
        pass

    # load assumptions file if present, else LOUD failure (no fabricated valuations)
    assum = _assumptions_for(t)
    archetype = assum.get("archetype", "unknown")
    has_assump_file = assum.get("has_assumptions_file", False)
    if not has_assump_file:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No valuation engine for {t}: missing data/assumptions/{t}.json. "
                f"Deterministic fallback is disabled to avoid fabricated ratings. "
                f"Run the full agent instead: POST /api/agent/start "
                f"{{\"ticker\": \"{t}\"}} — every number via calc_* tools."
            ),
        )

    # deterministic valuation via engines (never LLM)
    from ..engines import wacc as calc_wacc, dcf as calc_dcf, ev_ebitda

    # LOUD policy: every valuation input must be file-present — absent fields 422 by name, never invented.
    _missing_wacc = [k for k in ("rf", "beta", "erp", "cod") if assum.get(k) is None]
    if _missing_wacc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Missing WACC input(s) for {t}: {', '.join(_missing_wacc)}. "
                f"No defaults are invented keyless (sectors_missing_key). "
                f"Add them to data/assumptions/{t}.json or run the full agent: "
                f"POST /api/agent/start {{'ticker': '{t}'}}."
            ),
        )
    _missing_val = [k for k in ("fcf", "shares_out", "net_debt", "ebitda", "ev_multiple", "we", "wd", "g") if assum.get(k) is None]
    if _missing_val:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Missing valuation input(s) for {t}: {', '.join(_missing_val)}. "
                f"No defaults are invented keyless (sectors_missing_key). "
                f"Add them to data/assumptions/{t}.json or run the full agent: "
                f"POST /api/agent/start {{'ticker': '{t}'}}."
            ),
        )
    w = calc_wacc(assum["rf"], assum["beta"], assum["erp"], assum["cod"], we=assum.get("we", 0.608), wd=assum.get("wd", 0.392))
    wacc_val = w["wacc"]
    try:
        # FCF base is in IDR bn — scale to full IDR to match cash/net_debt (e9)
        raw_fcf = assum.get("fcf")
        fcf_list = [float(x) * 1e9 for x in raw_fcf]
        dcf_res = calc_dcf(fcf_list, wacc_val, assum.get("g", 0.015), shares_out=assum["shares_out"], net_debt=assum["net_debt"], cash=assum.get("cash", 0))
        fv = dcf_res["fv_per_share"]
        # EV/EBITDA cross-check
        ev_res = ev_ebitda(assum["ebitda"], assum["ev_multiple"], net_debt=assum["net_debt"], shares_out=assum["shares_out"], cash=assum.get("cash", 0))
        # blended if infra
        chosen_template = template or _template_for(t, segments, archetype)
        if chosen_template == "infra":
            from ..engines import blended as calc_blended

            blended_res = calc_blended({"dcf": dcf_res["fv_per_share"], "ev": ev_res["fv_per_share"]}, {"dcf": 0.6, "ev": 0.4})
            fv = blended_res["blended"]
        else:
            blended_res = None
    except Exception as e:
        dcf_res = {"error": str(e)}
        ev_res = {}
        blended_res = None
        fv = None

    # LOUD policy: no 'or 1000' — file last_price AND live price absent -> 422.
    last_price = assum.get("last_price") or price
    if not last_price:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Missing price for {t}: no last_price in data/assumptions/{t}.json "
                f"and no live Sectors price (sectors_missing_key). "
                f"Set SECTORS_API_KEY or add last_price to the assumptions file."
            ),
        )
    price_source = assum.get("price_source") or source
    upside = round((fv - last_price) / last_price * 100, 2) if fv and last_price else None
    rating = _rating_from_upside(upside)
    chosen_template = template or _template_for(t, segments, archetype)

    # ---- enrich: segments/KPI/GGM/bands/ratios/boxes ----
    if not has_assump_file:
        # Unknown ticker skeleton honest labeling
        segments_payload = {"segments": [], "total_pct": 0.0, "source": "no_assumptions_file"}
        kpis_payload = []
        kpi_single = None
        cover_boxes_payload = None
        forecast_revision_payload = None
        quarterly_payload = None
        report_source = "no_assumptions_file"
    else:
        segments_payload = _segments_for(archetype, assum, segments)
        kpis_payload = _kpis_for(archetype, assum)
        kpi_single = kpis_payload[0] if kpis_payload else None
        cover_boxes_payload = _cover_boxes_for(archetype, assum)
        forecast_revision_payload = _forecast_revision_for(archetype, assum)
        quarterly_payload = _quarterly_for(archetype, assum)
        report_source = source

    # GGM for bank archetype
    ggm_res = _ggm_for(archetype, assum, w["coe"])

    # LOUD policy: no synthetic_prices read — empty bands + source note until Sectors daily backs them.
    bands_res = {
        "bands": [],
        "source": "sectors_missing_key",
        "note": "valuation bands unavailable keyless: synthetic_prices are disclosed-seed fixtures, not market data; wired to Sectors daily when SECTORS_API_KEY lands",
    }

    # ratios — LOUD policy: revenue/equity are absent from assumption files, and
    # revenue=ebitda*2 / equity=cash*2 was invented math. No ratios until
    # Sectors quarterly backs them.
    ratios_res = None
    ratios_note = "ratios unavailable: revenue/equity absent from assumptions (no ebitda*2 invention); wired to Sectors quarterly when SECTORS_API_KEY lands"

    payload = {
        "ticker": t,
        "template": chosen_template,
        "price": last_price,
        "price_source": price_source if 'price_source' in locals() else source,
        "fair_value": fv,
        "upside_pct": upside,
        "rating": rating,
        "valuation": {
            "method": "blended 60/40" if chosen_template == "infra" else "dcf+ev/ebitda",
            "fair_value": fv,
            "currency": "IDR",
            "assumptions": {
                "wacc": wacc_val,
                "beta": assum["beta"],
                "rf": assum["rf"],
                "erp": assum["erp"],
                "coe": w["coe"],
                "cod": assum["cod"],
                "g": assum.get("g", 0.015),
                "payout": assum.get("payout", 0.4),
                "source": assum.get("source", report_source),
            },
            "provenance": f"engines.dcf+ev_ebitda{'+blended' if chosen_template=='infra' else ''} :: {report_source}",
            "dcf": dcf_res,
            "ev": ev_res,
            "blended": blended_res,
            "ggm": ggm_res,
            "bands": bands_res,
        },
        "ratios": ratios_res,
        "ratios_note": ratios_note,
        "thesis": None,
        "risks": [],
        "segments": segments_payload,
        "kpi": kpi_single,
        "kpis": kpis_payload,
        "cover_boxes": cover_boxes_payload,
        "forecast_revision": forecast_revision_payload,
        "quarterly": quarterly_payload,
        "source": report_source,
        "cached": False,
        "generated_at": _now_iso(),
    }
    await cache.set(ckey, payload)
    return payload


# ---------- report/{ticker}/run ----------
@router_report.get("/api/report/{ticker}/run", summary="Latest ADK run summary for ticker")
def report_ticker_run(ticker: str):
    """Return latest ADK run summary for ticker from SQLite.
    Always returns 200 (no 404) with has_run=True/False.
    """
    t = _clean_ticker(ticker)
    try:
        from agents.adk.storage import AgentRunStore

        store = AgentRunStore()
        run = store.get_latest_completed(t)
    except Exception:
        run = None

    if not run:
        return {
            "has_run": False,
            "run_id": None,
            "status": None,
            "n_events": 0,
            "started_at": None,
            "finished_at": None,
            "last_text": None,
            "error": None,
        }

    return {
        "has_run": True,
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "n_events": run.get("n_events") if run.get("n_events") is not None else 0,
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "last_text": run.get("last_text"),
        "error": run.get("error"),
    }


# ---------- report/{ticker}/log ----------
@router_report.get("/api/report/{ticker}/log", summary="Latest ADK run log for ticker")
def report_ticker_log(ticker: str):
    """Return latest ADK run log and recent history for a ticker from SQLite.
    Always returns 200 (no 404) with has_run=True/False.
    """
    t = _clean_ticker(ticker)
    try:
        from agents.adk.storage import AgentRunStore

        store = AgentRunStore()
        runs = store.list_runs(ticker=t, limit=5)
    except Exception:
        runs = []

    if not runs:
        return {
            "ticker": t,
            "has_run": False,
            "log": None,
            "history": [],
        }

    def _calc_duration(started_at: float | None, finished_at: float | None) -> float | None:
        if started_at is not None and finished_at is not None:
            return round(finished_at - started_at, 2)
        return None

    latest = runs[0]
    last_text = latest.get("last_text")
    last_text_preview = last_text[:200] if last_text else None

    log_payload = {
        "run_id": latest.get("run_id"),
        "status": latest.get("status"),
        "started_at": latest.get("started_at"),
        "finished_at": latest.get("finished_at"),
        "duration_s": _calc_duration(latest.get("started_at"), latest.get("finished_at")),
        "provider": latest.get("provider") or "minimax",
        "model": latest.get("model") or "minimax/MiniMax-M3",
        "n_events": latest.get("n_events") if latest.get("n_events") is not None else 0,
        "last_text_preview": last_text_preview,
        "error": latest.get("error"),
    }

    history_payload = [
        {
            "run_id": r.get("run_id"),
            "status": r.get("status"),
            "started_at": r.get("started_at"),
            "n_events": r.get("n_events") if r.get("n_events") is not None else 0,
            "duration_s": _calc_duration(r.get("started_at"), r.get("finished_at")),
        }
        for r in runs
    ]

    return {
        "ticker": t,
        "has_run": True,
        "log": log_payload,
        "history": history_payload,
    }


# ---------- outlook ----------
@router_outlook.get("/api/outlook", summary="JCI outlook — JPM base/bull/bear + sector OW/UW")
async def outlook():
    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    ckey = cache_key("outlook:jci")
    # LOUD policy: hardcoded JCI 9100/picks are research-note fixtures, not live
    # LOUD policy: outlook serves Sectors-native data only. The JPM-9100 fixture
    # block below is retired until the Sectors-native outlook is wired (post-key);
    # serving it keyed would present analyst notes as live data.
    raise HTTPException(
        status_code=503,
        detail="JCI outlook unavailable (sectors-native outlook pending): set SECTORS_API_KEY, then wire subsector breadth + movers; JPM-9100 fixture retired, never served as live",
    )
    # Retired fixture block deleted (LOUD policy): JPM-9100 numbers must never
    # be served as live. Sectors-native outlook lands post-key.


# ---------- news ----------
@router_news.get("/api/news", summary="News harvester — tiered, max 8, last 30d")
async def news(
    ticker: str | None = Query(None, description="filter by ticker, e.g. BBCA"),
    limit: int = Query(8, ge=1, le=20),
):
    settings = get_settings()
    cache = get_cache(3600)  # 1h per plan
    clean_ticker = _clean_ticker(ticker) if ticker else None
    key = cache_key(f"news:{(clean_ticker or 'general')}:{limit}")
    hit = await cache.get(key)
    if hit:
        hit["cached"] = True
        return hit
    # wire to scripts/news when available, else deterministic placeholder with honest provenance
    items = []
    try:
        import inspect
        try:
            from scripts.news import news_for  # type: ignore
            res = news_for(clean_ticker or "", limit=limit)
            if inspect.iscoroutine(res):
                items = await res
            else:
                items = res
        except (ImportError, AttributeError):
            from scripts.news import search_news
            res = search_news(clean_ticker or "", days=30, limit=limit)
            if inspect.iscoroutine(res):
                items = await res
            else:
                items = res
    except Exception:
        items = []
    if not items:
        # honest empty until scripts/news.py is added — see plans §4 data
        items = []
    payload = {
        "ticker": clean_ticker,
        "items": items[:limit],
        "source": "sectors_missing_key",
        "cached": False,
        "note": "wire scripts/news.py search_news() when T02 lands; returns [] until then (sectors_missing_key, no fabrication)",
    }
    await cache.set(key, payload)
    return payload


# ---------- sentiment ----------
@router_sentiment.get("/api/sentiment", summary="Retail sentiment gauge 0-100 + narratives + timeline")
async def sentiment(
    ticker: str = Query(..., description="ticker e.g. BBCA"),
    days: int = Query(14, ge=1, le=30),
):
    settings = get_settings()
    cache = get_cache(3600)
    t = _clean_ticker(ticker)
    key = cache_key(f"sentiment:{t}:{days}")
    hit = await cache.get(key)
    if hit:
        hit["cached"] = True
        return hit
    items = []
    try:
        import importlib.util
        import pathlib

        p = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "social.py"
        p2 = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "social_sentiment.py"
        for cand in [p, p2]:
            if cand.exists():
                spec = importlib.util.spec_from_file_location("soc_mod", str(cand))
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(mod)  # type: ignore
                if hasattr(mod, "search_social"):
                    items = await mod.search_social(t, days=days, limit=8)  # type: ignore
                    break
    except Exception:
        items = []
    if not items:
        payload = {
            "ticker": t,
            "gauge": 50,
            "confidence": 0.0,
            "empty": True,
            "source": "sectors_missing_key",
            "top_narratives": [],
            "timeline": [],
            "items": [],
            "disclaimer": "sentiment != advice — retail narrative tracker only",
            "cached": False,
            "note": "wire scripts/social.py search_social() when T02/T03 lands; returns empty until then (sectors_missing_key, no fabrication)",
        }
    else:
        # aggregate gauge as mean score
        try:
            gauge = round(sum(x.get("score", 50) for x in items) / len(items))
        except Exception:
            gauge = 50
        payload = {
            "ticker": t,
            "gauge": gauge,
            "confidence": 0.55,
            "empty": False,
            "top_narratives": [],
            "timeline": [],
            "items": items[:8],
            "disclaimer": "sentiment != advice — retail narrative tracker only",
            "cached": False,
        }
    await cache.set(key, payload)
    return payload


# ---------- challenge ----------
@router_challenge.post("/api/challenge", summary="Adversarial challenge & defense — verdict defend|concede with evidence")
async def challenge(body: dict):
    from fastapi import HTTPException
    import inspect

    ticker = _clean_ticker(body.get("ticker") or body.get("symbol") or "")
    claim = (body.get("claim") or body.get("question") or "").strip()
    context = body.get("context")
    if not ticker or not claim:
        raise HTTPException(400, "ticker and claim required")
    # wire to agents/adversarial when available
    debate_id = hashlib.sha256(f"{ticker}:{claim}:{time.time()}".encode()).hexdigest()[:12]
    try:
        try:
            from agents.adversarial import challenge as adv_challenge
            res = adv_challenge(ticker, claim, context)
            if inspect.iscoroutine(res):
                res = await res
        except (ImportError, AttributeError, TypeError):
            try:
                from agents.adversarial import challenge as adv_challenge
                res = adv_challenge(claim, ticker)
                if inspect.iscoroutine(res):
                    res = await res
            except Exception:
                from scripts.adversarial import challenge as adv_challenge
                res = adv_challenge(ticker, claim, context)
                if inspect.iscoroutine(res):
                    res = await res
        if isinstance(res, dict):
            res.setdefault("debate_id", debate_id)
            return res
    except Exception:
        pass
    # honest fallback — must not hallucinate verdict as defend; return concede-with-correction placeholder
    # so downstream critic can still audit
    return {
        "verdict": "concede",
        "stub": True,
        "evidence": "adversarial challenge stubbed — see agents/adversarial.py T09 (sectors_missing_key, no live debate)",
        "exhibit_ref": None,
        "correction": None,
        "debate_id": debate_id,
        "ticker": ticker,
        "claim": claim,
        "note": "adversarial challenge stubbed — see agents/adversarial.py T09",
    }


# ---------- dcf ({ticker}) ----------
router_dcf = APIRouter(prefix="/api/dcf", tags=["dcf"])


@router_dcf.get("/{ticker}", summary="Friend-style full DCF payload for a ticker")
def dcf_full_endpoint(ticker: str, overrides: str | None = None):
    """Friend-style full DCF payload for a ticker."""
    from fastapi import HTTPException as _HTTPException

    # LOUD policy: dcf_full() computes on hardcoded seed assumptions when the
    # file lacks keys (rf 0.065 / revenue 10000e9). Require file-backed WACC
    # inputs first — never serve seed-math as valuation.
    from ..config import get_settings as _get_settings

    _ = _get_settings()
    import pathlib as _pl
    import json as _js

    _fp = _pl.Path(__file__).resolve().parents[2] / "data" / "assumptions" / f"{ticker.upper()}.json"
    try:
        _assum = _js.loads(_fp.read_text(encoding="utf-8")) if _fp.exists() else {}
    except Exception:
        _assum = {}
    _need = ("rf", "beta", "erp", "cod")
    try:
        from ..engines import dcf_full
    except ImportError:
        from scripts.dcf_engine import dcf_full
    ov = None
    if overrides:
        import json
        try:
            ov = json.loads(overrides)
        except Exception:
            ov = None
    # File-backed inputs only: dcf_full seeds missing keys (rf 0.065, revenue
    # 10000e9). Pass the verified assumptions file as overrides so engines
    # compute on file numbers, never seeds. Explicit caller overrides count
    # as honest inputs (tests declare them); gate on the merged set.
    file_ov = {k: v for k, v in _assum.items() if v is not None}
    ov = {**file_ov, **(ov or {})}
    _miss2 = [k for k in _need if ov.get(k) is None]
    if _miss2:
        raise _HTTPException(
            status_code=422,
            detail=f"DCF unavailable for {ticker.upper()}: missing {', '.join(_miss2)} "
            f"(file + overrides; no seed-math served as valuation)",
        )
    try:
        result = dcf_full(ticker.upper(), overrides=ov)
        result["provenance"] = result.get("provenance", "") + " :: /api/dcf endpoint"
        return result
    except Exception as e:
        return {"error": str(e), "ticker": ticker, "provenance": "dcf_full error — fallback to /api/report"}

