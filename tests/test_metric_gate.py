"""Tests for the pre-render consistency gate.

These pin Stage 1 of the editorial-review fix (17 Sep 2026):
  - canonical metric block is computed from one source of truth
  - every renderer reads from canonical, not its own snapshot
  - cross-renderer disagreements surface as visible badges

The architectural goal is bug-class elimination: when a future data refresh
causes the canonical source to drift, all renderers follow together and
no per-page disagreements can appear.
"""
from __future__ import annotations

import pytest

from server.report.metric_gate import (
    CANONICAL_METRIC_KEYS,
    ROUNDING_RULES,
    check_inconsistencies,
    reconcile_metrics,
)


def test_canonical_mcap_uses_daily_close():
    """Cover (assumptions.market_cap = 352.4 tn) and Exhibit 12 (daily[-1] = 362.24 tn)
    used to disagree by ~10 tn because each renderer picked its own snapshot.
    Canonical now reads daily[-1].close x shares; both renderers must follow.
    """
    daily = {"data": [{"close": 5000.0}]}  # 5000 rp/share
    assum = {"shares_outstanding": 72_500_000_000, "market_cap": 352_400_000_000_000}  # 352.4 tn
    canonical = reconcile_metrics(assum, daily=daily)
    assert "market_cap_rpbn" in canonical
    mcap = canonical["market_cap_rpbn"]
    # 5000 rp/share * 72.5e9 shares = 3.625e14 rp = 362,500 rpbn
    assert mcap["value"] == 362500.0
    assert "daily" in mcap["source"]


def test_canonical_mcap_falls_back_when_no_daily():
    """If no daily close is available, fall back to assumptions.market_cap and mark the source."""
    daily = {"data": []}
    assum = {"shares_outstanding": 72_500_000_000, "market_cap": 352_400_000_000_000}
    canonical = reconcile_metrics(assum, daily=daily)
    mcap = canonical["market_cap_rpbn"]
    # 352.4e12 rp = 352,400 rpbn
    assert mcap["value"] == 352400.0
    assert "fallback" in mcap["source"]


def test_canonical_sum_pv_fcff_computed_from_array():
    """Bug 1: DCF Blok 3 used a hardcoded 48,503.3 instead of summing Blok 1's array.

    Sum of [-5352.6, 10701.0, 9143.5, 11954.3, 10176.3] = 36,622.5.
    The gate must compute this from the actual array, not from a hardcoded value.
    """
    dcf = {"pv_of_fcff": [-5352.6, 10701.0, 9143.5, 11954.3, 10176.3]}
    canonical = reconcile_metrics({}, dcf_data=dcf)
    spv = canonical["sum_pv_fcff_rpbn"]
    assert spv["value"] == 36622.5
    # Source must NOT mention a hardcoded value
    assert "hardcoded" not in spv["source"].lower()


def test_canonical_sum_pv_fcff_ignores_terminal_value():
    """Sum must include only the 5 explicit years, not terminal value.
    If a 6th entry (terminal value) leaks in, the gate still sums only [:5].
    """
    dcf = {"pv_of_fcff": [-5352.6, 10701.0, 9143.5, 11954.3, 10176.3, 109230.9]}
    canonical = reconcile_metrics({}, dcf_data=dcf)
    assert canonical["sum_pv_fcff_rpbn"]["value"] == 36622.5  # not 145,853.4


def test_canonical_pe_ratios_use_valuation_ratios_block():
    """P/E FY24A 34.2x (Ex 2) vs 59.73x (Ex 3) disagreement came from different
    snapshot reads. Canonical pulls from valuation.ratios; renderers must follow.
    """
    valuation = {
        "ratios": {"pe_fy24a": 34.2, "pe_fy25a": 84.6},
        "multiples": {"ev_ebitda_ttm": 17.99},
    }
    canonical = reconcile_metrics({}, valuation=valuation)
    assert canonical["pe_fy24a_x"]["value"] == 34.2
    assert canonical["pe_fy25a_x"]["value"] == 84.6
    assert canonical["ev_ebitda_ttm_x"]["value"] == 17.99


def test_debt_label_consistency_flags_dropping_series():
    """Bug 3: 'flat di level FY2025A' label with values that drop 9.405 -> 4.263.

    The gate must flag this so the renderer can either correct the label
    or carry an INCONSISTENT badge on the row.
    """
    dcf = {
        "debt_rows": [
            {
                "label": "Short-term Debt forecast: flat di level FY2025A (tidak ada jadwal pelunasan)",
                "values": [None, 9405, 9087, 6406, 4263],
            },
        ]
    }
    canonical = reconcile_metrics({}, dcf_data=dcf)
    assert canonical["debt_label_consistency"]["value"] == "INCONSISTENT"


def test_debt_label_consistency_passes_when_series_is_flat():
    """If the series is genuinely flat, the 'flat' label is honest. Gate passes."""
    dcf = {
        "debt_rows": [
            {
                "label": "Short-term Debt forecast: flat di level FY2025A",
                "values": [None, 9405, 9405, 9405, 9405],
            },
        ]
    }
    canonical = reconcile_metrics({}, dcf_data=dcf)
    assert canonical["debt_label_consistency"]["value"] == "CONSISTENT"


def test_inconsistency_report_appears_when_renderers_diverge():
    """Synthetic divergence: cover says mcap 352.4, peers says 362.24.

    The gate must surface this as an inconsistency record with gap > tolerance.
    """
    canonical = {"market_cap_rpbn": {"value": 362.5}}
    payload = {
        "cover": {"metrics": {"mkt_cap_rpbn": 352.4}},
        "peers_table": {"row": {"AMMN": {"mkt_cap_rpbn": 362.24}}},
    }
    records = check_inconsistencies(payload, canonical)
    # Cover disagrees (352.4 vs 362.5, gap ~2.8% > 1% tolerance) -> error severity
    cover_rec = [r for r in records if r["renderer_path"] == "cover.metrics.mkt_cap_rpbn"]
    assert len(cover_rec) == 1
    r = cover_rec[0]
    assert r["severity"] == "error"
    assert r["gap_pct"] > 1.0
    assert r["canonical_value"] == 362.5
    assert r["rendered_value"] == 352.4


def test_inconsistency_report_passes_when_renderers_agree():
    """If renderers agree with canonical, the gate emits no error-severity records."""
    canonical = {"market_cap_rpbn": {"value": 362.5}}
    payload = {
        "cover": {"metrics": {"mkt_cap_rpbn": 362.5}},
        "peers_table": {"row": {"AMMN": {"mkt_cap_rpbn": 362.5}}},
    }
    records = check_inconsistencies(payload, canonical)
    errors = [r for r in records if r["severity"] == "error"]
    assert errors == [], f"expected no errors, got: {errors}"


def test_canonical_metric_keys_covers_all_6_confirmed_bugs():
    """Stage 1 scope: every confirmed bug from the 17 Sep review has a canonical metric."""
    expected_keys = {
        "market_cap_rpbn",       # Bug 6
        "ev_ebitda_ttm_x",       # Bug 6
        "pe_fy24a_x",            # Bug 6
        "pe_fy25a_x",            # Bug 6
        "sum_pv_fcff_rpbn",      # Bug 1
        "debt_label_consistency",  # Bug 3
    }
    assert expected_keys.issubset(set(CANONICAL_METRIC_KEYS))


def test_rounding_rules_have_entry_for_every_metric():
    """Every canonical metric must have a tolerance, else check_inconsistencies crashes."""
    for key in CANONICAL_METRIC_KEYS:
        assert key in ROUNDING_RULES, f"missing ROUNDING_RULES[{key!r}]"


def test_inconsistency_badge_returns_empty_when_no_record():
    """No audit report -> no badge. Safe default."""
    from server.report.metric_gate import inconsistency_badge
    payload: dict = {"audit": {"inconsistency_report": []}}
    out = inconsistency_badge("market_cap_rpbn", payload, "cover.metrics.mkt_cap_rpbn")
    assert out == ""


def test_inconsistency_badge_returns_html_when_record_present():
    """Gap > tolerance -> error severity -> badge is rendered."""
    from server.report.metric_gate import inconsistency_badge
    payload = {
        "audit": {
            "inconsistency_report": [
                {
                    "metric": "market_cap_rpbn",
                    "renderer_path": "cover.metrics.mkt_cap_rpbn",
                    "severity": "error",
                    "canonical_value": 362.5,
                    "rendered_value": 352.4,
                    "gap_pct": 2.76,
                }
            ]
        }
    }
    out = inconsistency_badge("market_cap_rpbn", payload, "cover.metrics.mkt_cap_rpbn")
    assert "INCONSISTENT" in out
    assert "2.76" in out or "2.8" in out
    assert 'class="inconsistency-badge"' in out
