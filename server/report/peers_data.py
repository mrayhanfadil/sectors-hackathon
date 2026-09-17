"""Slide-5 data layer: peer table (cross-sectional) + own-history bands (time-series).

Contract
--------
* Everything here is **cache-first** and **Sectors-only**. A re-run that finds its artifacts on disk
  makes **zero billed calls**; `refresh=True` (CLI `--refresh`) is the only path that can spend.
* The renderer never calls this module's network path: the page builder reads the JSON artifacts, so a
  PDF render is offline and deterministic.
* Raw responses are archived per request, so a cached rebuild can be verified against what Sectors
  actually returned.

Technique notes that cost real credits to learn (keep them):
  - Peer ratios (`pe_ttm`, `pb_mrq`) come from `company_report(ticker, 'peers')` - one snapshot, one
    as-of, consistent across every row. Do NOT mix them with market caps from another source: the
    peers payload's `market_cap` is a prior fiscal year's, and blending it with LTM earnings produced
    nonsense (TBMS 2.31x against Sectors' own published 12.51x).
  - market cap on the published basis is recovered as `pb_mrq x latest equity`.
  - Peer financials in `company_report(sym,'financials')` are ANNUAL; only `quarterly(sym)` gives
    per-quarter rows. Mixing the two breaks the "one consistent period" rule, so peers are pulled from
    `quarterly(sym)`.
  - `/daily/` is capped at 90 days per call: one year = four windows.
  - TTM = sum of the last four quarters; stock items (equity, net debt) take the latest quarter.
  - `net_debt` is absent from quarterly rows but `total_debt` and `cash_and_short_term_investments`
    are present, so net debt = total_debt - cash.
  - Negative / near-zero earnings give a meaningless multiple: print `n.m.` and exclude from the
    median and average, and say so in the footnote.
"""
from __future__ import annotations

import json
import os
import statistics as st
from datetime import date, timedelta
from typing import Any, Optional
from server.report import numfmt as _nf

TICKERS = ("AMMN",)
PEER_SET = ("TBMS", "EMAS", "BRMS", "ANTM", "MDKA", "NCKL", "MBMA", "INCO", "TINS")
PE_MAX = 200.0            # above this the P/E is not a usable comparison
AS_OF = "2026-09-11"
DAILY_WINDOW_DAYS = 90    # Sectors caps /daily/ at 90 days
TTM_QUARTERS = 4

_CACHE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "output", "cache", "sectors")


def cache_dir(ticker: str) -> str:
    d = os.path.join(_CACHE_ROOT, ticker.upper())
    os.makedirs(os.path.join(d, "raw"), exist_ok=True)
    return d


def raw_dir(ticker: str) -> str:
    d = os.path.join(cache_dir(ticker), "raw")
    os.makedirs(d, exist_ok=True)
    return d


# --------------------------------------------------------------------------- helpers
def _read(path: str) -> Optional[Any]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write(path: str, payload: Any) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1)
    return path


def _num(row: dict, *names: str) -> Optional[float]:
    for n in names:
        v = row.get(n)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def _client():
    """Sectors client with the team key loaded - only used on a cache miss."""
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)
    env_file = os.path.expanduser("~/.config/sectors-be/env")
    if os.path.exists(env_file) and not os.environ.get("SECTORS_API_KEY"):
        with open(env_file) as fh:
            for line in fh:
                if line.strip().startswith("SECTORS_API_KEY="):
                    os.environ["SECTORS_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    from server import sectors  # noqa: PLC0415
    return sectors


class CreditLog:
    """Records what actually hit the API, so a cache rebuild can prove it spent nothing."""

    def __init__(self) -> None:
        self.billed = 0
        self.hits = 0

    def miss(self, what: str) -> None:
        self.billed += 1
        print(f"  BILLED  {what}")

    def hit(self, what: str) -> None:
        self.hits += 1
        print(f"  cache   {what}")

    def report(self) -> str:
        return f"billed calls: {self.billed} | cache hits: {self.hits}"


# --------------------------------------------------------------------------- raw pulls
def peer_ratios(ticker: str, refresh: bool = False, log: Optional[CreditLog] = None) -> dict:
    """Published LTM/MRQ ratios for the whole peer set, incl. the covered name."""
    log = log or CreditLog()
    path = os.path.join(raw_dir(ticker), f"peers_{ticker}.json")
    data = None if refresh else _read(path)
    if data is None:
        log.miss(f"company_report({ticker},'peers')")
        data = _client().company_report(ticker, "peers")
        _write(path, data)
    else:
        log.hit(f"peers_{ticker}.json")
    rows = (data.get("peers") or [{}])[0].get("peers_data", {}).get("companies", [])
    return {str(r.get("symbol", "")).replace(".JK", ""): r for r in rows}


def quarterly(ticker: str, symbol: str, refresh: bool = False, log: Optional[CreditLog] = None) -> list:
    """Per-quarter statement rows, newest last."""
    log = log or CreditLog()
    path = os.path.join(raw_dir(ticker), f"quarterly_{symbol}.json")
    data = None if refresh else _read(path)
    if data is None:
        log.miss(f"quarterly({symbol})")
        got = _client().quarterly(symbol)
        data = got.get("data") or got.get("results") or []
        _write(path, data)
    else:
        log.hit(f"quarterly_{symbol}.json")
    rows = [r for r in data if isinstance(r, dict)]
    return sorted(rows, key=lambda r: str(r.get("date") or r.get("period") or ""))


def daily_history(ticker: str, end: Optional[str] = None, refresh: bool = False,
                  log: Optional[CreditLog] = None) -> list:
    """One year of daily closes + market cap, pulled as four 90-day windows."""
    log = log or CreditLog()
    end = end or AS_OF
    path = os.path.join(raw_dir(ticker), "daily_1y.json")
    data = None if refresh else _read(path)
    if data is None:
        end_d = date.fromisoformat(end)
        rows, seen = [], set()
        for i in range(3, -1, -1):
            s = (end_d - timedelta(days=DAILY_WINDOW_DAYS * (i + 1)) + timedelta(days=1)).isoformat()
            e = (end_d - timedelta(days=DAILY_WINDOW_DAYS * i)).isoformat()
            log.miss(f"daily({ticker}, {s}..{e})")
            got = _client().daily(ticker, start=s, end=e)
            for r in (got.get("data") if isinstance(got, dict) else got) or []:
                if r.get("date") not in seen:
                    seen.add(r.get("date"))
                    rows.append(r)
        rows.sort(key=lambda r: str(r.get("date")))
        _write(path, {"data": rows})
    else:
        log.hit("daily_1y.json")
        rows = data.get("data", [])
    return rows


# --------------------------------------------------------------------------- derivations
def ttm(rows: list, *names: str) -> Optional[float]:
    """Sum of the last four quarters - the flow driver for a trailing multiple."""
    last = rows[-TTM_QUARTERS:]
    vals = [_num(r, *names) for r in last]
    vals = [v for v in vals if v is not None]
    return sum(vals) if len(vals) == TTM_QUARTERS else None


def net_debt(row: dict) -> Optional[float]:
    debt = _num(row, "total_debt")
    cash = _num(row, "cash_and_short_term_investments", "cash_only")
    if debt is None:
        return None
    return debt - (cash or 0.0)


def build_peer_table(ticker: str = "AMMN", refresh: bool = False) -> dict:
    """Exhibit 11 payload - one arithmetic for every row, median/average from the peer set only."""
    log = CreditLog()
    ratios = peer_ratios(ticker, refresh, log)
    rows_out = []
    for sym in list(PEER_SET) + [ticker]:
        q = quarterly(ticker, sym, refresh, log)
        last = q[-1] if q else {}
        pub = ratios.get(sym, {})
        earnings_ttm = ttm(q, "earnings", "net_income")
        ebitda_ttm = ttm(q, "ebitda")
        equity = _num(last, "total_equity", "stockholders_equity")
        nd = net_debt(last)
        pe, pb = pub.get("pe_ttm"), pub.get("pb_mrq")
        if sym == ticker.upper():
            # For covered issuer, canonical market cap = equity x pb_mrq.
            # Bug 6 (17 Sep): cached daily_history rows carry a stale
            # `market_cap` from the Q4-2025 freeze (352.4 tn). The fresh
            # PBV x equity snapshot is 362.24 tn. Before this fix, every
            # section that read market_cap directly (cover, Exhibit 12, EV/EBITDA)
            # picked the snapshot its caller already had; the same metric
            # shipped on the page with two different values. The canonical
            # source is PBV x equity, computed from the most recent Sectors
            # quarterly (which has both fields, both fresh). Use that, and
            # fall back to daily close x shares only if PBV is missing.
            cap = (pb * equity) if (pb and equity) else None
            if cap is None:
                d_hist = daily_history(ticker, AS_OF, refresh, log)
                if d_hist and d_hist[-1].get("close"):
                    shares = (
                        d_hist[-1].get("shares_outstanding")
                        or d_hist[-1].get("market_cap", 0) / d_hist[-1]["close"]
                    )
                    cap = float(d_hist[-1]["close"]) * float(shares) if shares else None
        else:
            cap = (pb * equity) if (pb and equity) else None
        ev = (cap + nd) if (cap and nd is not None) else None
        rows_out.append({
            "symbol": sym,
            "company_name": pub.get("company_name"),
            "is_covered": sym == ticker.upper(),
            "pe_ttm": pe,
            "pb_mrq": pb,
            "pe_meaningful": bool(pe and 0 < pe <= PE_MAX),
            "market_cap": cap,
            "net_debt": nd,
            "ev": ev,
            "ebitda_ttm": ebitda_ttm,
            "earnings_ttm": earnings_ttm,
            "equity": equity,
            "roe_ttm": (earnings_ttm / equity) if (earnings_ttm and equity) else None,
            "ev_ebitda_ttm": (ev / ebitda_ttm) if (ev and ebitda_ttm and ebitda_ttm > 0) else None,
            "pe_computed": (cap / earnings_ttm) if (cap and earnings_ttm and earnings_ttm > 0) else None,
            "quarters_used": len(q),
            "period_end": str(last.get("date") or last.get("period") or "")[:10],
        })

    def collect(key: str) -> list:
        return [r[key] for r in rows_out
                if not r["is_covered"] and r.get(key) is not None
                and (key != "pe_ttm" or r["pe_meaningful"])]

    def median(v: list) -> float:
        v = sorted(v)
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

    stats = {}
    for key in ("pe_ttm", "pb_mrq", "ev_ebitda_ttm", "roe_ttm"):
        v = collect(key)
        stats[key] = {"median": median(v) if v else None,
                      "average": (sum(v) / len(v)) if v else None,
                      "n": len(v)}
    payload = {
        "ticker": ticker.upper(),
        "basis": "LTM (TTM = sum of the last four quarters; ratios are Sectors' published LTM/MRQ)",
        "as_of": AS_OF,
        "peer_set": list(PEER_SET),
        "rows": rows_out,
        "stats": stats,
        "pe_excluded": [r["symbol"] for r in rows_out if not r["is_covered"] and not r["pe_meaningful"]],
        "sources": [
            f"Sectors API: company_report({ticker},'peers') - published pe_ttm / pb_mrq, as of {AS_OF}",
            "Sectors API: quarterly financials per peer - TTM earnings, TTM EBITDA, latest equity and net debt",
            "market cap recovered on the published basis: pb_mrq x latest equity",
        ],
        "credit_log": log.report(),
    }
    _write(os.path.join(cache_dir(ticker), "peer_table.json"), payload)
    return payload


def build_bands(ticker: str = "AMMN", refresh: bool = False) -> dict:
    """Exhibits 12-13 payload - trailing multiples over a one-year window + implied prices."""
    log = CreditLog()
    sessions_raw = daily_history(ticker, AS_OF, refresh, log)
    q = quarterly(ticker, ticker, refresh, log)

    ttm_sets = []
    for i in range(len(q)):
        win = q[max(0, i - (TTM_QUARTERS - 1)): i + 1]
        if len(win) < TTM_QUARTERS:
            continue
        ttm_sets.append({
            "as_of": win[-1]["date"],
            "earnings": sum(_num(r, "earnings", "net_income") or 0 for r in win),
            "ebitda": sum(_num(r, "ebitda") or 0 for r in win),
            "revenue": sum(_num(r, "revenue", "total_revenue") or 0 for r in win),
            "equity": _num(win[-1], "total_equity", "stockholders_equity"),
            "net_debt": net_debt(win[-1]),
        })
    if not ttm_sets:
        return {"ticker": ticker.upper(), "available": False,
                "reason": "no complete TTM window in the quarterly history"}

    sessions = []
    for d in sessions_raw:
        day, close, mcap = d.get("date"), d.get("close"), d.get("market_cap")
        if not (day and close and mcap):
            continue
        driver = ttm_sets[0]
        for t in ttm_sets:
            if t["as_of"] <= day:
                driver = t
        shares = mcap / close
        ev = mcap + (driver["net_debt"] or 0)
        eps = driver["earnings"] / shares
        bvps = (driver["equity"] or 0) / shares
        sessions.append({
            "date": day, "close": close, "market_cap": mcap, "driver_as_of": driver["as_of"],
            "pe": (close / eps) if eps > 0 else None,
            "pbv": (close / bvps) if bvps > 0 else None,
            "ev_ebitda": (ev / driver["ebitda"]) if driver["ebitda"] > 0 else None,
            "ev_sales": (ev / driver["revenue"]) if driver["revenue"] > 0 else None,
        })

    summary = {}
    for key in ("pe", "pbv", "ev_ebitda", "ev_sales"):
        vals = [s[key] for s in sessions if s[key] is not None]
        if len(vals) < 10:
            summary[key] = None
            continue
        sv = sorted(vals)
        cur = vals[-1]
        summary[key] = {
            "n": len(vals), "mean": st.mean(vals), "median": st.median(vals),
            "min": sv[0], "max": sv[-1],
            "p25": sv[len(sv) // 4], "p75": sv[(3 * len(sv)) // 4],
            "current": cur, "sd": st.pstdev(vals) if len(vals) > 1 else 0.0,
            "percentile": 100.0 * sum(1 for v in vals if v <= cur) / len(vals),
        }

    last, driver = sessions[-1], ttm_sets[-1]
    shares_now = last["market_cap"] / last["close"]
    nd_ps = (driver["net_debt"] or 0) / shares_now
    per_share = {"pe": driver["earnings"] / shares_now, "pbv": (driver["equity"] or 0) / shares_now,
                 "ev_ebitda": driver["ebitda"] / shares_now, "ev_sales": driver["revenue"] / shares_now}
    implied = {}
    for key, ps in per_share.items():
        s = summary.get(key)
        if not s or not ps:
            continue
        if key in ("pe", "pbv"):
            implied[key] = {"to_mean": s["mean"] * ps, "to_median": s["median"] * ps}
        else:
            # per-share EV multiple -> subtract net debt per share to land on equity value
            implied[key] = {"to_mean": s["mean"] * ps - nd_ps, "to_median": s["median"] * ps - nd_ps}
    for key, v in implied.items():
        lo, hi = sorted((v["to_mean"], v["to_median"]))
        v["low"], v["high"] = lo, hi
        v["is_range"] = (hi - lo) / hi > 0.10 if hi else False

    payload = {
        "ticker": ticker.upper(), "available": True, "basis": "trailing multiples, one-year window",
        "window": {"from": sessions[0]["date"], "to": last["date"], "sessions": len(sessions)},
        "as_of": last["date"], "last_close": last["close"], "market_cap": last["market_cap"],
        "driver": {"as_of": driver["as_of"], "earnings_ttm": driver["earnings"],
                   "ebitda_ttm": driver["ebitda"], "revenue_ttm": driver["revenue"],
                   "equity": driver["equity"], "net_debt": driver["net_debt"]},
        "driver_frozen_sessions": sum(1 for s in sessions if s["driver_as_of"] != driver["as_of"]),
        "summary": summary, "implied_price": implied, "sessions": sessions,
        "sources": [
            f"Sectors API: daily prices + market cap, {sessions[0]['date']} to {last['date']} "
            f"({len(sessions)} sessions, pulled as four 90-day windows)",
            f"Sectors API: quarterly financials - rolling TTM ending {driver['as_of']}",
        ],
        "credit_log": log.report(),
    }
    _write(os.path.join(cache_dir(ticker), "bands_1y.json"), payload)
    return payload


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    ref = "--refresh" in sys.argv
    tk = (args[0] if args else "AMMN").upper()
    pt = build_peer_table(tk, ref)
    bd = build_bands(tk, ref)
    print(f"\n{tk} peer table: {len(pt['rows'])} rows | median P/E {_nf.dec(pt['stats']['pe_ttm']['median'], digits=2)} "
          f"| {pt['credit_log']}")
    print(f"{tk} bands: {bd['window']['sessions']} sessions | {bd['credit_log']}")
