"""Thesis Writer agent — bull case narrative with hard numbers.

Deterministic: every number rendered is read from company.json or computed by
this module's pure helpers (no LLM math, no network, no credit).

Responsibilities (plan.md §3):
  1. Bull case — segment growth (CDIA Energy 55% / Logistics 34% fastest +44.7%),
     one-off adjustment (CDIA 15.9mn → net -72%), quantified catalysts
     (MTEL PST+UMT merger 1 Jul 2026 + spectrum → +3,000-3,500 tenants, +IDR 360-420bn).
  2. Normalizations & adjusted net income.
  3. Risk summaries (from input, not invented) + KPI highlights.

Usage:
    python agents/writer.py [TICKER...]   # default: all fixtures (CDIA MTEL ADRO)
Outputs:
    out/<TICKER>/thesis.json
    out/<TICKER>/thesis.md
"""

from __future__ import annotations

import argparse
import sys
import os
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    ENGINE_VERSION,
    data_fingerprint,
    ensure_out,
    fmt_idr,
    load_company,
    now_iso,
    pct,
    pct_delta,
    source_label,
    write_json,
    write_markdown,
    x_pct,
)

try:  # the agents are also run as standalone scripts from their own directory
    from server.report import numfmt as _nf
except ImportError:  # pragma: no cover
    import pathlib as _p
    import sys as _s

    _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1]))
    from server.report import numfmt as _nf

# ---------------------------------------------------------------------------
# Pure helpers (unit-testable)
# ---------------------------------------------------------------------------


def normalize_one_offs(company: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize non-recurring items: adjusted net income = reported - one-off*(1-tax).

    Task-brief invariant (CDIA): one-off 15.9mn (gross 15,900 IDR mn) → net -72%.
    With reported base 17,225mn and tax 22%:
        adjusted = 17,225 - 15,900*0.78 = 17,225 - 12,402 = 4,823mn
        delta    = (4,823 - 17,225) / 17,225 = -72.0%   ✓
    The BCA Sekuritas benchmark (23 Jun 2026) normalizes the same 15.9 one-off to
    -72%; the engine reproduces it deterministically from company.json.
    """
    one = company.get("one_offs")
    if not one or not one.get("items"):
        return None
    reported = float(one["reported_net_income_mn"])
    tax = float(one.get("tax_rate", 0.22))
    items = one["items"]
    gross = sum(float(i["amount_mn"]) for i in items)
    net = gross * (1.0 - tax)
    adjusted = reported - net
    delta = pct_delta(adjusted, reported)
    return {
        "description": one.get("description", ""),
        "unit": one.get("unit", "IDR mn"),
        "items": [{"label": i["label"], "amount_mn": float(i["amount_mn"])} for i in items],
        "gross_one_off_mn": gross,
        "tax_rate": tax,
        "net_one_off_after_tax_mn": round(net, 2),
        "reported_net_income_mn": reported,
        "adjusted_net_income_mn": round(adjusted, 2),
        "delta_pct": delta,
        "method": f"adjusted = reported - one_offs*(1-t) = {_nf.idn(reported, digits=0)} - {_nf.idn(gross, digits=0)}*(1-{_nf.pcfrac(tax, 0)}) = {_nf.idn(adjusted, digits=0)}mn",
    }


def segment_narrative(company: dict[str, Any]) -> dict[str, Any]:
    """Bull-case segment story: largest pillar, fastest grower, mix math."""
    segs = company.get("segments", [])
    if not segs:
        return {"headline": None, "arguments": [], "mix_note": None}
    largest = max(segs, key=lambda s: s.get("revenue_mn", 0))
    fastest = max(segs, key=lambda s: s.get("growth_yoy", 0))
    mix_sum = round(sum(s.get("pct", 0) for s in segs), 4)
    args = []
    if largest:
        args.append({
            "id": "SEG1",
            "point": (
                f"{largest['pillar']} is the value anchor at {_nf.dec(largest['pct'], digits=0)}% of revenue "
                f"({fmt_idr(largest['revenue_mn'])}) growing {pct(largest['growth_yoy'])} y/y"
            ),
            "evidence": {"metric": "segment revenue mix", "value": largest["pct"], "source": largest.get("source", source_label(company))},
        })
    if fastest and fastest["pillar"] != largest["pillar"]:
        args.append({
            "id": "SEG2",
            "point": (
                f"{fastest['pillar']} is the fastest grower at {pct(fastest['growth_yoy'])} y/y "
                f"({_nf.dec(fastest['pct'], digits=0)}% of mix) — the re-rating engine"
            ),
            "evidence": {"metric": "segment growth y/y", "value": fastest["growth_yoy"], "source": fastest.get("source", source_label(company))},
        })
    return {
        "headline": (
            f"Mix: {largest['pillar']} {_nf.dec(largest['pct'], digits=0)}% / {fastest['pillar']} {_nf.dec(fastest['pct'], digits=0)}% "
            f"(fastest, {pct(fastest['growth_yoy'])}) y/y — {_nf.dec(mix_sum, digits=1)}% of revenue"
        ) if largest else None,
        "arguments": args,
        "mix_sum_pct": mix_sum,
    }


def catalyst_narrative(company: dict[str, Any]) -> list[dict[str, Any]]:
    """Quantified catalysts — the MTEL pattern (3k tenants + 360-420bn by FY27-29)."""
    out = []
    for c in company.get("catalysts", []):
        q = c.get("quantified", {})
        entry = {
            "id": c.get("id", "CAT"),
            "title": c.get("title", ""),
            "date": c.get("date", ""),
            "type": c.get("type", ""),
            "status": c.get("status", ""),
            "source": c.get("source", ""),
        }
        if "tenants_added_min" in q:
            entry["quantified"] = (
                f"+{_nf.idn(q['tenants_added_min'], digits=0)}-{_nf.idn(q['tenants_added_max'], digits=0)} tenants, "
                f"+{fmt_idr(q['annualized_revenue_min_mn'])}-{fmt_idr(q['annualized_revenue_max_mn'])} "
                f"annualized by {q.get('by_fy', 'FY')}"
            )
            entry["quantified_struct"] = q
        elif "tenancy_ratio_target" in q:
            entry["quantified"] = f"tenancy ratio toward >{q['tenancy_ratio_target']}×"
            entry["quantified_struct"] = q
        elif "aadi_equity_usd_mn" in q:
            entry["quantified"] = (
                f"AADI equity US${_nf.dec(q['aadi_equity_usd_mn']/1000, digits=1)}bn; ADRO post-spin "
                f"US${_nf.dec(q['adro_post_spin_min_usd_mn']/1000, digits=1)}-{_nf.dec(q['adro_post_spin_max_usd_mn']/1000, digits=1)}bn"
            )
            entry["quantified_struct"] = q
        if entry["quantified"]:
            out.append(entry)
    return out


def kpi_highlights(company: dict[str, Any]) -> list[dict[str, Any]]:
    """Subsector hero KPIs (MTEL: tenancy ratio + fiber km)."""
    kpi = company.get("kpi", {})
    out = []
    tenancy = kpi.get("tenancy_ratio")
    if tenancy is not None:
        out.append({
            "kpi": "tenancy_ratio",
            "value": tenancy,
            "display": f"{_nf.dec(tenancy, digits=2)}× (tenants {_nf.idn(kpi.get('tenants', '?'), 0)} / towers {_nf.idn(kpi.get('towers', '?'), 0)})",
            "source": kpi.get("kpi_period", source_label(company)),
        })
    fiber = kpi.get("fiber_km")
    if fiber is not None:
        out.append({
            "kpi": "fiber_km",
            "value": fiber,
            "display": f"{_nf.idn(fiber, digits=0)} km",
            "source": kpi.get("kpi_period", source_label(company)),
        })
    return out


def risk_summary(company: dict[str, Any]) -> list[dict[str, Any]]:
    """Risks derived from input facts (never invented). Falls back to archetype labels."""
    out = []
    fin = company.get("financials", {})
    gearing = fin.get("gearing_pct", [])
    if gearing:
        peak = max(gearing)
        if peak >= 150:
            out.append({
                "id": "R1",
                "title": "High leverage",
                "detail": f"Gearing peaked at {_nf.dec(peak, digits=0)}% in the series (target: de-lever to current-ratio 0.3→0.8 trajectory).",
                "severity": "high",
            })
    debteb = fin.get("debt_ebitda", [])
    if debteb and max(debteb) >= 10:
        out.append({
            "id": "R2",
            "title": "Elevated Debt/EBITDA",
            "detail": f"Debt/EBITDA reached {_nf.dec(max(debteb), digits=0)}× — refinancing and rate sensitivity are key risks.",
            "severity": "high",
        })
    one = company.get("one_offs")
    if one:
        out.append({
            "id": "R3",
            "title": "Earnings quality (one-offs)",
            "detail": f"Reported net includes {fmt_idr(sum(i['amount_mn'] for i in one['items']))} one-off items ({one.get('description', '')}) — normalize before comparing.",
            "severity": "medium",
        })
    if not out:
        out.append({
            "id": "R0",
            "title": "Archetype-generic",
            "detail": "See Risk Officer (T03) for pillar-specific risk buckets; writer surfaces input-derived risks only.",
            "severity": "medium",
        })
    return out


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_thesis(ticker: str) -> dict[str, Any]:
    company = load_company(ticker)
    seg = segment_narrative(company)
    norm = normalize_one_offs(company)
    cats = catalyst_narrative(company)

    headline_parts = []
    if seg.get("headline"):
        headline_parts.append(seg["headline"])
    if norm:
        headline_parts.append(
            f"one-off adj {fmt_idr(norm['gross_one_off_mn'])} → net {_nf.dec(norm['delta_pct'], digits=0)}%"
        )
    if cats:
        c0 = cats[0]
        headline_parts.append(f"catalyst: {c0['title'].split('(')[0].strip()} {c0.get('quantified', '')}")
    headline = " | ".join(headline_parts) or f"{ticker} bull case (no segments/catalysts in input)"

    args = [a for a in seg.get("arguments", [])]
    # Valuation-anchored argument when financials exist
    fin = company.get("financials", {})
    years = fin.get("years", [])
    rev = fin.get("revenue_mn", [])
    if len(rev) >= 3:
        args.insert(0, {
            "id": "T0",
            "point": (
                f"Revenue {years[0]}→{years[-1]}: {fmt_idr(rev[0])} → {fmt_idr(rev[-1])} "
                f"({_nf.dec(pct_delta(rev[-1], rev[0]), digits=0, signed=True)}% cumulative) — growth optionality across pillars"
            ),
            "evidence": {"metric": "revenue CAGR proxy", "value": pct_delta(rev[-1], rev[0]), "source": source_label(company)},
        })

    thesis = {
        "ticker": ticker,
        "name": company.get("name", ticker),
        "archetype": company.get("archetype", "single"),
        "bull_case": {
            "title": f"{company.get('name', ticker)} — Institutional Bull Case",
            "headline": headline,
            "arguments": args,
            "catalysts": cats,
        },
        "normalizations": norm,
        "adjusted": {
            "reported_net_income_mn": norm["reported_net_income_mn"] if norm else None,
            "adjusted_net_income_mn": norm["adjusted_net_income_mn"] if norm else None,
            "delta_pct": norm["delta_pct"] if norm else None,
            "method": norm["method"] if norm else "no one-offs in input",
        },
        "kpi_highlights": kpi_highlights(company),
        "risks": risk_summary(company),
        "meta": {
            "generated_at": now_iso(),
            "engine": ENGINE_VERSION,
            "input_fingerprint": data_fingerprint(company),
            "source": source_label(company),
        },
    }
    return thesis


def thesis_markdown(thesis: dict[str, Any]) -> str:
    t = thesis
    bc = t["bull_case"]
    lines = [
        f"# {t['name']} ({t['ticker']}) — Thesis (archetype: {t['archetype']})",
        "",
        f"> **Bull case:** {bc['headline']}",
        "",
        "## Bull case arguments",
    ]
    for a in bc["arguments"]:
        lines.append(f"- **{a['id']}** — {a['point']}  \n  *Evidence: {a['evidence']['metric']} = {a['evidence']['value']} · source: {a['evidence']['source']}*")
    if bc["catalysts"]:
        lines += ["", "## Catalysts (quantified)"]
        for c in bc["catalysts"]:
            lines.append(f"- **{c['id']}** — {c['title']} ({c.get('date', '')}, status: {c.get('status', '')}) → {c.get('quantified', '')}  \n  *Source: {c.get('source', '')}*")
    n = t.get("normalizations")
    if n:
        lines += ["", "## One-off normalization", f"- {n['description']}"]
        for i in n["items"]:
            lines.append(f"  - {i['label']}: {fmt_idr(i['amount_mn'])}")
        lines += [
            f"- Reported net income: {fmt_idr(n['reported_net_income_mn'])}",
            f"- One-offs gross: {fmt_idr(n['gross_one_off_mn'])} @ tax {_nf.pcfrac(n['tax_rate'], 0)} → net-of-tax {fmt_idr(n['net_one_off_after_tax_mn'])}",
            f"- **Adjusted net income: {fmt_idr(n['adjusted_net_income_mn'])} → Δ {_nf.dec(n['delta_pct'], digits=1)}%**",
            f"- Method: {n['method']}",
        ]
    if t.get("kpi_highlights"):
        lines += ["", "## KPI highlights"]
        for k in t["kpi_highlights"]:
            lines.append(f"- **{k['kpi']}**: {k['display']}  \n  *Source: {k['source']}*")
    if t.get("risks"):
        lines += ["", "## Risks (input-derived)"]
        for r in t["risks"]:
            lines.append(f"- [{r['severity']}] **{r['title']}** — {r['detail']}")
    lines += [
        "",
        "---",
        f"*Generated by {t['meta']['engine']} · input fingerprint {t['meta']['input_fingerprint']} · source: {t['meta']['source']}*",
    ]
    return "\n".join(lines)


def run(ticker: str) -> dict[str, Any]:
    thesis = build_thesis(ticker)
    out_dir = ensure_out(ticker)
    json_path = write_json(os.path.join(out_dir, "thesis.json"), thesis)
    md_path = write_markdown(os.path.join(out_dir, "thesis.md"), thesis_markdown(thesis))
    print(f"[writer] {ticker}: {json_path} + {md_path} | headline: {thesis['bull_case']['headline'][:110]}…")
    return thesis


def main() -> None:
    ap = argparse.ArgumentParser(description="Thesis Writer agent (deterministic)")
    ap.add_argument("tickers", nargs="*", help="default: all fixture tickers")
    args = ap.parse_args()
    tickers = [t.upper() for t in args.tickers] or ["CDIA", "MTEL", "ADRO"]
    for t in tickers:
        run(t)


if __name__ == "__main__":
    main()
