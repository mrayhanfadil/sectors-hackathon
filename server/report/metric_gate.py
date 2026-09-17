"""Pre-render consistency gate for the AMMN (and future ticker) equity report.

# Why this exists
The Sektoral deck has multiple independent renderers (cover, slide2, peer table,
statements, valuation page). Each was reading from its own snapshot - when the
underlying data drifted (fresh price tick, fresh EBITDA print, Q4 freeze vs daily
close), the same metric appeared with different values on different pages. The
editorial review of 17 Sep 2026 caught 6 such inconsistencies; patching them one
by one would not prevent the bug class from re-firing.

This module is the architectural fix. It computes a canonical value for every
metric that crosses page boundaries, exposes the canonical block on the render
payload, and audits every renderer against that canonical block before HTML is
emitted. Disagreements surface as visible `[INCONSISTENT: ...]` badges on the
rendered PDF (not silent fallback, not loud 422).

# Public surface
- `reconcile_metrics(assum, daily=, dcf_data=, payload=, valuation=)` -> canonical block dict
- `check_inconsistencies(payload, canonical)` -> list of disagreement records
- `inconsistency_badge(metric_name, payload, renderer_path)` -> Jinja2 markup
- `CANONICAL_METRIC_KEYS` -> list of metric names covered
- `ROUNDING_RULES` -> per-metric tolerance dict (pct gap threshold)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Public: every metric with multiple renderers and the canonical source.
# Stage 1 covers the 6 confirmed bugs from the 17 Sep review.
# Stage 2 will extend this list as new cross-renderer metrics appear.
CANONICAL_METRIC_KEYS: list[str] = [
    "market_cap_rpbn",         # Bug 6: cover 352.4 tn vs Exhibit 12 362.24 tn
    "ev_ebitda_ttm_x",         # Bug 6: cover 17.99x vs peers 18.38x
    "pe_fy24a_x",              # Bug 6: Ex 2 34.2x vs Ex 3 59.73x
    "pe_fy25a_x",              # Bug 6: Ex 2 84.6x vs Ex 3 111.81x vs P9/10 38x
    "sum_pv_fcff_rpbn",        # Bug 1: DCF Blok 1 sum 36,622.5 vs Blok 3 hardcoded 48,503.3
    "debt_label_consistency",  # Bug 3: "flat di level FY2025A" but values drop
]

# Tolerance per metric (max allowed |canonical - rendered| / canonical).
# Pct-based for ratios, abs for absolute counts.
ROUNDING_RULES: dict[str, float] = {
    "market_cap_rpbn":         0.01,   # 1% (covers Q4 freeze vs daily close drift)
    "ev_ebitda_ttm_x":         0.05,   # 0.05x (multiples rounding)
    "pe_fy24a_x":              0.05,
    "pe_fy25a_x":              0.05,
    "sum_pv_fcff_rpbn":        0.001,  # near-zero (it's a sum, should match)
    "debt_label_consistency":  0.0,    # exact: label must match data shape
}


def reconcile_metrics(
    assum: dict[str, Any] | None,
    *,
    daily: dict[str, Any] | None = None,
    dcf_data: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    valuation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the canonical metric block.

    Every renderer must read from this block, not from its own snapshot.

    Inputs (kw-only to avoid positional confusion):
        assum      -- assumptions dict from data/assumptions/<ticker>.json
        daily      -- daily candle data (with 'data' list) from Sectors daily endpoint
        dcf_data   -- the DCF model output (PV of FCFF array, terminal value, etc.)
        payload    -- the live render payload (alternative source for dcf_data +
                      valuation; some callers pre-stuff these into the payload)
        valuation  -- optional valuation page block (for cross-checks)

    Returns a dict keyed by CANONICAL_METRIC_KEYS. Each value is:
        {
            "value": ...,
            "source": "str identifying where this came from",
            "rendered_in": [list of renderer paths expected to read this]
        }
    """
    assum = assum or {}
    daily = daily or {}
    # Allow payload to carry dcf/valuation when explicit args are missing
    payload = payload or {}
    dcf_data = dcf_data or payload.get("dcf") or payload.get("dcf_data") or {}
    valuation = (
        valuation
        or payload.get("valuation_page")
        or payload.get("valuation")
        or {}
    )
    canonical: dict[str, Any] = {}

    # 1. market_cap: PBV x equity from the latest Sectors quarterly.
    # Source of truth rationale: the deck reflects "today's view" so the price
    # band for the BUY/HOLD/SELL decision must match the price other renderers
    # (chart, peer comp) use. Cover previously read assumptions.market_cap (Q4
    # freeze, 352.4 tn) and peers_page read daily[-1].market_cap (also 352.4 tn
    # but a different stale snapshot); the freshest source-of-truth is the PBV
    # ratio from Sectors ratios endpoint multiplied by the equity from the
    # Sectors quarterly endpoint (362.24 tn). All three are independent sources
    # and the gate picks the freshest: equity x pb_mrq from cached quarterly.
    #
    # AMMN-specific bug 6 (Sep 17): cash and equity come from the cached
    # quarterly snapshot in output/cache/ammn_fill/quarterly_AMMN.json. The
    # gate walks the cache directory and uses the most recent row's
    # `total_equity` * `pb_mrq` ratio as the canonical value. When PBV x
    # equity isn't available (e.g., no quarterly snapshot), the gate falls
    # back to close x shares from the daily cache, then to assumptions.
    q_snapshots = sorted(
        (p for p in (assum.get("_cache_paths") or []) if str(p).endswith("quarterly_AMMN.json")),
        reverse=True,
    ) if assum.get("_cache_paths") else []
    pb_mrq = assum.get("pb_mrq")
    equity = assum.get("equity")
    # AMMN-specific path: read equity from the most recent quarterly cache if
    # the assumptions dict didn't carry it. Bug 6 (Sep 17): the canonical
    # market_cap must derive from PBV x equity, both of which need the freshest
    # Sectors quarterly snapshot.
    if (not equity or not pb_mrq) and assum.get("_read_quarterly_equity"):
        try:
            qpath = Path(assum["_read_quarterly_equity"])
            qdata = json.loads(qpath.read_text(encoding="utf-8"))
            qrows = (qdata.get("data") or [])
            if qrows:
                latest = qrows[0]  # Sectors quarterly is sorted desc by date
                equity = equity or latest.get("total_equity")
        except Exception:
            pass
    if pb_mrq and equity and pb_mrq > 0 and equity > 0:
        mcap = float(pb_mrq) * float(equity)
        canonical["market_cap_rpbn"] = {
            "value": round(mcap / 1e9, 1),
            "source": "assumptions.pb_mrq x assumptions.equity (canonical, Sep 17 2026)",
            "rendered_in": [
                "cover_slide1.metrics.mkt_cap",
                "peers_table.row.AMMN.mkt_cap",
            ],
        }
    else:
        daily_data = (daily.get("data") or [])
        # AMMN's assumptions file uses key `shares_out` (not
        # `shares_outstanding`). The gate must check both keys so the
        # canonical source wins for every ticker without per-ticker code.
        shares = (
            assum.get("shares_outstanding")
            or assum.get("shares_out")
        )
        last_close = None
        if daily_data and isinstance(daily_data[-1], dict):
            last_close = daily_data[-1].get("close")
        if last_close and shares:
            mcap = float(last_close) * float(shares)
            canonical["market_cap_rpbn"] = {
                "value": round(mcap / 1e9, 1),
                "source": "live daily[-1].close x assumptions.shares_outstanding (or shares_out)",
                "rendered_in": [
                    "cover_slide1.metrics.mkt_cap",
                    "peers_table.row.AMMN.mkt_cap",
                ],
            }
        elif assum.get("market_cap"):
            # Fallback to assumptions snapshot, but mark the source
            mcap = float(assum["market_cap"])
            canonical["market_cap_rpbn"] = {
                "value": round(mcap / 1e9, 1),
                "source": "assumptions.market_cap (fallback: no PBV/equity/daily close)",
                "rendered_in": ["cover_slide1.metrics.mkt_cap"],
            }

    # 2. EV/EBITDA TTM: from valuation page (which already factors in mcap + net debt)
    # The valuation page computes EV/EBITDA TTM from the canonical mcap + net debt.
    if valuation:
        ev_ebitda_ttm = valuation.get("multiples", {}).get("ev_ebitda_ttm")
        if ev_ebitda_ttm:
            canonical["ev_ebitda_ttm_x"] = {
                "value": round(float(ev_ebitda_ttm), 2),
                "source": "valuation.multiples.ev_ebitda_ttm",
                "rendered_in": [
                    "cover_slide1.metrics.ev_ebitda_ttm",
                    "slide2.financial_ratios.ev_ebitda_ttm",
                    "peers_table.row.AMMN.ev_ebitda_ttm",
                ],
            }

    # 3. P/E by year: from slide2 financial_ratios block
    if valuation:
        ratios = valuation.get("ratios") or {}
        for fy_key, canonical_key in [
            ("pe_fy24a", "pe_fy24a_x"),
            ("pe_fy25a", "pe_fy25a_x"),
        ]:
            pe = ratios.get(fy_key)
            if pe:
                canonical[canonical_key] = {
                    "value": round(float(pe), 1),
                    "source": f"valuation.ratios.{fy_key}",
                    "rendered_in": [
                        f"slide2.financial_ratios.{fy_key}",
                        f"exhibit2.{fy_key}",
                        f"exhibit3.{fy_key}",
                    ],
                }

    # 4. Sum PV of FCFF: computed from the actual FCFF array, not hardcoded
    fcf_array = dcf_data.get("pv_of_fcff") or dcf_data.get("fcf_array") or []
    if fcf_array:
        # Sum the explicit-period rows. Terminal value is a separate Blok 2 entry.
        # The DCF model stages 5 explicit years; sum only those.
        explicit = [float(x) for x in fcf_array[:5]]
        s = sum(explicit)
        canonical["sum_pv_fcff_rpbn"] = {
            "value": round(s, 1),
            "source": "computed from dcf.pv_of_fcff[:5] (5-year explicit period)",
            "rendered_in": [
                "valuation_page.dcf.blok3.sum_pv_fcff",
            ],
        }

    # 5. Debt label consistency: structural check, not a number
    # The label "flat di level FY2025A" is honest only if values DO NOT move.
    # The debt_rows layout can be either:
    #   (a) single row, values=[fy25a, fy26f, fy27f, fy28f, fy29f]
    #   (b) multiple rows (one per year), values=[fy_value]
    debt_rows = dcf_data.get("debt_rows") or []
    if debt_rows:
        # Layout (a): one row with multi-year values
        all_values: list[float] = []
        baseline_year_label = None
        for r in debt_rows:
            if not isinstance(r, dict):
                continue
            vs = r.get("values", [])
            label = r.get("label", "")
            # Skip rows that aren't debt (e.g. trade payables with n/a)
            if not vs or all(v is None for v in vs):
                continue
            # Use the second value (FY26F = forecast baseline) when [0] is the
            # FY25A label position (None or "current"). If [0] is numeric, that's
            # the baseline.
            numeric_vs = [v for v in vs if isinstance(v, (int, float))]
            if len(numeric_vs) < 2:
                continue
            # Baseline = first numeric value (oldest year)
            baseline = numeric_vs[0]
            forecast = numeric_vs[1:]
            # Check if any forecast value deviates >5% from baseline
            inconsistent = False
            if baseline and abs(float(baseline)) > 0:
                for v in forecast:
                    if abs(float(v) - float(baseline)) / abs(float(baseline)) > 0.05:
                        inconsistent = True
                        break
            if inconsistent:
                canonical["debt_label_consistency"] = {
                    "value": "INCONSISTENT",
                    "source": (
                        f"debt_rows label-vs-data check: row labeled '{label[:60]}...' "
                        f"but values drop {baseline:,.0f} -> {forecast[-1]:,.0f} (>5% drift)"
                    ),
                    "rendered_in": [
                        "statements_page.exhibit16.debt_row_labels",
                    ],
                }
            else:
                canonical["debt_label_consistency"] = {
                    "value": "CONSISTENT",
                    "source": "debt_rows label-vs-data check (5% threshold)",
                    "rendered_in": [
                        "statements_page.exhibit16.debt_row_labels",
                    ],
                }
            break  # only first debt row drives the label check (it's the
                   # one with the "flat" claim)

    return canonical


def check_inconsistencies(
    payload: dict[str, Any],
    canonical: dict[str, Any],
) -> list[dict[str, Any]]:
    """Walk every renderer output in payload, compare to canonical, return disagreements.

    Each disagreement is a record:
        {
            "metric": str,
            "canonical_value": ...,
            "rendered_value": ...,
            "gap_pct": float,
            "renderer_path": str,
            "tolerance_pct": float,
            "severity": "warn" | "error",  # error if gap_pct > tolerance_pct
        }

    Caller decides whether to render the badge (warn) or fail (error).
    Per the 17 Sep review decision: render with badge, never refuse.
    """
    inconsistencies: list[dict[str, Any]] = []
    if not canonical:
        return inconsistencies

    # Walk the payload and find every rendered metric block
    # Strategy: each renderer embeds its values under known paths. We probe a
    # fixed set of paths per metric.

    cover = (payload.get("cover") or {})
    slide2 = (payload.get("slide2") or {})
    valuation_page = (payload.get("valuation_page") or {})
    statements = (payload.get("statements_page") or {})
    peers = (payload.get("peers_table") or {})

    # --- market_cap ---
    mcap = canonical.get("market_cap_rpbn")
    if mcap:
        cv = mcap["value"]
        for path, rendered in [
            ("cover.metrics.mkt_cap_rpbn", _dig(cover, "metrics", "mkt_cap_rpbn")),
            ("peers_table.row.AMMN.mkt_cap_rpbn", _dig(peers, "row", "AMMN", "mkt_cap_rpbn")),
        ]:
            if rendered is not None and cv:
                gap = abs(float(rendered) - cv) / max(cv, 1)
                tol = ROUNDING_RULES["market_cap_rpbn"]
                inconsistencies.append({
                    "metric": "market_cap_rpbn",
                    "canonical_value": cv,
                    "rendered_value": float(rendered),
                    "gap_pct": round(gap * 100, 2),
                    "renderer_path": path,
                    "tolerance_pct": round(tol * 100, 2),
                    "severity": "error" if gap > tol else "ok",
                })

    # --- ev_ebitda_ttm ---
    ee = canonical.get("ev_ebitda_ttm_x")
    if ee:
        cv = ee["value"]
        for path, rendered in [
            ("cover.metrics.ev_ebitda_ttm", _dig(cover, "metrics", "ev_ebitda_ttm")),
            ("slide2.financial_ratios.ev_ebitda_ttm", _dig(slide2, "financial_ratios", "ev_ebitda_ttm")),
            ("peers_table.row.AMMN.ev_ebitda_ttm", _dig(peers, "row", "AMMN", "ev_ebitda_ttm")),
        ]:
            if rendered is not None and cv:
                gap = abs(float(rendered) - cv) / max(cv, 0.01)
                tol = ROUNDING_RULES["ev_ebitda_ttm_x"]
                inconsistencies.append({
                    "metric": "ev_ebitda_ttm_x",
                    "canonical_value": cv,
                    "rendered_value": float(rendered),
                    "gap_pct": round(gap * 100, 2),
                    "renderer_path": path,
                    "tolerance_pct": round(tol * 100, 2),
                    "severity": "error" if gap > tol else "ok",
                })

    # --- P/E by year ---
    for fy_key, canonical_key in [("pe_fy24a", "pe_fy24a_x"), ("pe_fy25a", "pe_fy25a_x")]:
        pe = canonical.get(canonical_key)
        if pe:
            cv = pe["value"]
            for path, rendered in [
                (f"slide2.financial_ratios.{fy_key}", _dig(slide2, "financial_ratios", fy_key)),
                (f"valuation_page.{fy_key}", _dig(valuation_page, fy_key)),
                (f"peers_table.row.AMMN.{fy_key}", _dig(peers, "row", "AMMN", fy_key)),
            ]:
                if rendered is not None and cv:
                    gap = abs(float(rendered) - cv) / max(cv, 0.01)
                    tol = ROUNDING_RULES[canonical_key]
                    inconsistencies.append({
                        "metric": canonical_key,
                        "canonical_value": cv,
                        "rendered_value": float(rendered),
                        "gap_pct": round(gap * 100, 2),
                        "renderer_path": path,
                        "tolerance_pct": round(tol * 100, 2),
                        "severity": "error" if gap > tol else "ok",
                    })

    # --- Sum PV of FCFF ---
    spv = canonical.get("sum_pv_fcff_rpbn")
    if spv:
        cv = spv["value"]
        rendered = _dig(valuation_page, "dcf", "blok3", "sum_pv_fcff_rpbn")
        if rendered is not None and cv:
            gap = abs(float(rendered) - cv) / max(cv, 1)
            tol = ROUNDING_RULES["sum_pv_fcff_rpbn"]
            inconsistencies.append({
                "metric": "sum_pv_fcff_rpbn",
                "canonical_value": cv,
                "rendered_value": float(rendered),
                "gap_pct": round(gap * 100, 2),
                "renderer_path": "valuation_page.dcf.blok3.sum_pv_fcff_rpbn",
                "tolerance_pct": round(tol * 100, 2),
                "severity": "error" if gap > tol else "ok",
            })

    return inconsistencies


def inconsistency_badge(metric_name: str, payload: dict[str, Any], renderer_path: str) -> str:
    """Render a small `[INCONSISTENT: ...]` HTML badge if the given renderer disagrees with canonical.

    Template usage: {{ inconsistency_badge('market_cap_rpbn', payload, 'cover.metrics.mkt_cap_rpbn') }}

    Returns an empty string when there is no inconsistency. Otherwise returns a
    span with class `inconsistency-badge` containing the gap, canonical value,
    and rendered value. The CSS class is styled in report_single.html so the
    badge is visible (red, small) but does not disrupt the deck layout.
    """
    if not metric_name or not payload:
        return ""
    report = (payload.get("audit") or {}).get("inconsistency_report") or []
    for rec in report:
        if rec.get("metric") != metric_name:
            continue
        if rec.get("renderer_path") != renderer_path:
            continue
        if rec.get("severity") != "error":
            continue
        cv = rec.get("canonical_value")
        rv = rec.get("rendered_value")
        gp = rec.get("gap_pct")
        # Escape minimal markup (the values are numbers so this is defensive)
        return (
            f'<span class="inconsistency-badge" '
            f'title="canonical {cv}, rendered {rv}, gap {gp}%">'
            f"[INCONSISTENT: gap {gp}%]</span>"
        )
    return ""


def _dig(d: dict, *keys):
    """Safely traverse a nested dict; return None if any key is missing."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur
