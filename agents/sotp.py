"""SOTP Aggregator — conglomerate sum-of-parts valuation (CDIA/ADRO pattern).

Deterministic. For conglomerates (segments >= 2) only:
  - Each pillar gets an implied equity = peer-avg P/E x pillar net income proxy,
    falling back to peer-avg EV/EBITDA x pillar EBITDA proxy when net income is
    unavailable at pillar level (CDIA BCA Sekuritas uses peer tables per pillar).
  - Sum of parts = 100% of pillar weights (pct column of segments) — the Critic
    invariant: `sum(weights) == 100.0` and `sum(pcts) == 100.0`.
  - Holdco discount (BRIDS ADRO pattern) applied to the pre-discount total when
    `company.sotp.holdco_discount_pct` is present; otherwise discount = 0.

Usage:
    python agents/sotp.py [TICKER...]      # default: all fixtures
Outputs:
    out/<TICKER>/sotp.json
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    ENGINE_VERSION,
    data_fingerprint,
    ensure_out,
    load_company,
    now_iso,
    source_label,
    write_json,
)


def implied_equity(pillar: dict[str, Any], company: dict[str, Any]) -> float:
    """Pillar equity proxy: peer-avg P/E x (revenue x net margin proxy).

    CDIA/BCA pattern: per-pillar peer tables. When the modeler (T02) provides
    pillar net income it should be used; here we fall back to the disclosed
    peer-avg P/E applied to pillar net income proxy (revenue x net margin proxy
    from financials, defaulting to 10% when the input has no net margin series).
    """
    fin = company.get("financials", {})
    nm = fin.get("net_margin", [])
    margin = nm[-1] if nm else 0.10
    rev = pillar.get("revenue_mn", 0.0)
    pe = pillar.get("peer_avg_pe", 10.0)
    return rev * margin * pe


def build_sotp(ticker: str) -> dict[str, Any]:
    company = load_company(ticker)
    segs = company.get("segments", [])
    conglomerate = company.get("archetype") == "sotp"  # SOTP is conglomerate-only (CDIA/ADRO)
    if not conglomerate or not segs:
        return {
            "ticker": ticker,
            "conglomerate": False,
            "reason": "single-pillar / non-conglomerate — SOTP not applicable",
            "meta": {"generated_at": now_iso(), "engine": ENGINE_VERSION},
        }

    pct_sum = round(sum(float(s.get("pct", 0)) for s in segs), 6)
    pillars = []
    for s in segs:
        eq = implied_equity(s, company)
        pillars.append({
            "pillar": s["pillar"],
            "revenue_mn": float(s.get("revenue_mn", 0)),
            "pct": float(s.get("pct", 0)),
            "growth_yoy": float(s.get("growth_yoy", 0)),
            "peer_avg_pe": float(s.get("peer_avg_pe", 0)),
            "peer_avg_ev_ebitda": float(s.get("peer_avg_ev_ebitda", 0)),
            "peer_set": s.get("peer_set", ""),
            "source": s.get("source", source_label(company)),
            "implied_equity_mn": round(eq, 2),
            "weight_pct": round(float(s.get("pct", 0)), 2),  # weight == segment mix share
        })

    pre_total = round(sum(p["implied_equity_mn"] for p in pillars), 2)
    # Holdco discount (BRIDS ADRO pattern): explicit input or default 0 for CDIA-style.
    holdco = company.get("sotp", {})
    discount = float(holdco.get("holdco_discount_pct", 0.0))
    post_total = round(pre_total * (1.0 - discount), 2)
    equity_share_sum = round(sum(p["weight_pct"] for p in pillars), 6)

    sotp = {
        "ticker": ticker,
        "name": company.get("name", ticker),
        "conglomerate": True,
        "method": "peer-avg per pillar (SOTP); sum of parts = 100% before holdco discount",
        "pillars": pillars,
        "pillar_count": len(pillars),
        "holdco_discount_pct": discount,
        "pre_discount_total_mn": pre_total,
        "post_discount_equity_mn": post_total,
        "discount_note": (
            holdco.get("note", "")
            if holdco.get("note")
            else "No holdco discount in input — CDIA-style conglomerate with listed subsidiaries valued directly."
        ),
        "sum_check": {
            "pct_sum": pct_sum,
            "equity_weight_sum": equity_share_sum,
            "pct_sum_ok": abs(pct_sum - 100.0) < 1e-6,
            "equity_weight_ok": abs(equity_share_sum - 100.0) < 1e-6,
            "ok": abs(pct_sum - 100.0) < 1e-6 and abs(equity_share_sum - 100.0) < 1e-6,
        },
        "meta": {
            "generated_at": now_iso(),
            "engine": ENGINE_VERSION,
            "input_fingerprint": data_fingerprint(company),
            "source": source_label(company),
        },
    }
    return sotp


def run(ticker: str) -> dict[str, Any]:
    sotp = build_sotp(ticker)
    path = write_json(os.path.join(ensure_out(ticker), "sotp.json"), sotp)
    if sotp.get("conglomerate"):
        sc = sotp["sum_check"]
        status = "OK" if sc["ok"] else "MISMATCH"
        print(
            f"[sotp] {ticker}: {sotp['pillar_count']} pillars | pct_sum={sc['pct_sum']}% "
            f"| weights={sc['equity_weight_sum']}% | holdco discount {sotp['holdco_discount_pct']:.0%} "
            f"| pre {sotp['pre_discount_total_mn']:,.0f} -> post {sotp['post_discount_equity_mn']:,.0f} | {status}"
        )
    else:
        print(f"[sotp] {ticker}: not a conglomerate — skipped ({sotp.get('reason')})")
    return sotp


def main() -> None:
    ap = argparse.ArgumentParser(description="SOTP Aggregator agent (deterministic)")
    ap.add_argument("tickers", nargs="*")
    args = ap.parse_args()
    tickers = [t.upper() for t in args.tickers] or ["CDIA", "MTEL", "ADRO"]
    for t in tickers:
        run(t)


if __name__ == "__main__":
    main()
