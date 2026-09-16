"""Test ticker-agnostic freeze lookup (Sep 16 2026).

Two checks:
  1. The collector serves any ticker's freeze from output/cache/ticker_fill/
     (the new directory) and from output/cache/ammn_fill/ (the legacy alias).
  2. The source label on the payload says `ticker_fill_freeze` for new freezes
     and `ticker_fill_freeze + legacy_source=ammn_fill_freeze` for freezes that
     live in the legacy alias directory.

Fixtures:
  output/cache/ticker_fill/company_report_ADRO_multisection.json
    (created by this test on import, removed at session-end)

The historical AMMN freeze at output/cache/ammn_fill/... is left alone - this
test reads it but does not modify it. A previous CI run created it from the
kanban t_2c5f420e lane.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, "/home/fadil/projects/sectors-hackathon")

_REPO = Path("/home/fadil/projects/sectors-hackathon")
_NEW_DIR = _REPO / "output" / "cache" / "ticker_fill"
_LEGACY_DIR = _REPO / "output" / "cache" / "ammn_fill"

_FIXTURE = {
    "overview": {
        "symbol": "ADRO",
        "company_name": "Alamtri Resources Indonesia TBK",
        "sector": "Coal",
        "subsector_slug": "basic-materials",
        "currency": "IDR",
        "market_cap": 60000000000000,
    },
    "financials": {"annual": {}, "quarterly": {}},
}


@pytest.fixture(scope="module")
def adro_freeze():
    """Drop a minimal ADRO freeze into the new ticker_fill/ dir, clean up after."""
    _NEW_DIR.mkdir(parents=True, exist_ok=True)
    p = _NEW_DIR / "company_report_ADRO_multisection.json"
    created = not p.exists()
    if created:
        p.write_text(json.dumps(_FIXTURE), encoding="utf-8")
    try:
        yield p
    finally:
        if created and p.exists():
            p.unlink()


def test_new_dir_freeze_serves_any_ticker(adro_freeze):
    """A freeze in output/cache/ticker_fill/ is found by ticker (not by name)."""
    from agents.collector import _ticker_fill_payload, _freeze_path_for

    # _freeze_path_for returns the new dir for ADRO
    p = _freeze_path_for("ADRO")
    assert p == _NEW_DIR, f"expected {_NEW_DIR}, got {p}"

    # _ticker_fill_payload returns a payload with the new label
    payload = _ticker_fill_payload("ADRO")
    assert payload is not None, "ADRO freeze should be served"
    assert payload["source"] == "ticker_fill_freeze"
    assert payload["legacy_source"] is None
    assert payload["info"]["symbol"] == "ADRO"


def test_legacy_dir_freeze_still_serves(adro_freeze):
    """AMMN's freeze at output/cache/ammn_fill/ is still served via the legacy alias."""
    from agents.collector import _ticker_fill_payload, _freeze_path_for

    if not (_LEGACY_DIR / "company_report_AMMN_multisection.json").exists():
        pytest.skip("legacy AMMN freeze not present in this clone")

    p = _freeze_path_for("AMMN")
    assert p == _LEGACY_DIR, f"expected legacy dir, got {p}"

    payload = _ticker_fill_payload("AMMN")
    assert payload is not None
    assert payload["source"] == "ticker_fill_freeze"
    # The legacy_source field preserves the historical label for callers that
    # pattern-match on it.
    assert payload["legacy_source"] == "ammn_fill_freeze"


def test_unknown_ticker_returns_none(adro_freeze):
    """A ticker with no freeze returns None (loud-empty, not a default)."""
    from agents.collector import _ticker_fill_payload

    assert _ticker_fill_payload("ZZZZZZ") is None


def test_collect_runs_end_to_end_for_non_ammn_ticker(adro_freeze):
    """collect('ADRO') with a freeze in ticker_fill/ serves from cache at 0 Sectors cost.

    This is the headline agnostic-ticker check: any ticker that has a freeze file in
    the new directory runs through the full pipeline (collect -> freeze mirror -> cache
    save -> payload) without needing an AMMN-specific code path.
    """
    from agents.collector import collect

    # Clear the rendered cache so we exercise the freeze path, not the rendered-cache hit.
    rendered = _REPO / "data" / "output" / "cache_collector_ADRO.json"
    if rendered.exists():
        rendered.unlink()

    result = collect("ADRO", use_cache=False, force_refresh=True)
    assert result["source"] == "ticker_fill_freeze"
    # The 5 passthrough labels all carry the new "ticker_fill_" prefix
    for key in ("segments_source", "jci_source", "holders_source",
                "ratios_source", "kpi_source"):
        assert result[key] == "ticker_fill_freeze_passthrough", \
            f"{key} should be ticker_fill_freeze_passthrough, got {result[key]}"
    assert result["company"]["symbol"] == "ADRO"


if __name__ == "__main__":
    # Manual sanity run without pytest fixture machinery
    _NEW_DIR.mkdir(parents=True, exist_ok=True)
    fix = _NEW_DIR / "company_report_ADRO_multisection.json"
    created = not fix.exists()
    if created:
        fix.write_text(json.dumps(_FIXTURE), encoding="utf-8")
    try:
        test_new_dir_freeze_serves_any_ticker(fix)
        test_legacy_dir_freeze_still_serves(fix)
        test_unknown_ticker_returns_none(fix)
        test_collect_runs_end_to_end_for_non_ammn_ticker(fix)
        print("ALL TICKER-AGNOSTIC FREEZE TESTS PASSED")
    finally:
        if created and fix.exists():
            fix.unlink()
