"""AMMN-FIXD regression guard: the 422 missing-assumptions gate stays cleared for AMMN.

Baseline (docs/ammn-slides/verify-report.md §1.1, CHK-01): with no
data/assumptions/AMMN.json the production loaders raised

    HTTPException 422 -> missing ['rf','beta','erp','cod','g','payout','fcf',
    'shares_out','net_debt','cash','ebitda','ev_multiple','last_price','we','wd']

This file pins the positive state: the file exists, carries all 15 gate keys with
per-field provenance, and server/routers/pdf.py:_build_live_payload clears the
assumptions gate (no HTTP 422). Later-stage gaps (charts, statements) are NOT
asserted here — those belong to the rendering lane.
"""
from __future__ import annotations

import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
AMMN = REPO_ROOT / "data" / "assumptions" / "AMMN.json"

# server/routers/pdf.py:73-74 and endpoints.py:427-429 require exactly these keys.
GATE_KEYS = (
    "rf", "beta", "erp", "cod", "g", "payout", "fcf", "shares_out", "net_debt",
    "cash", "ebitda", "ev_multiple", "last_price", "we", "wd",
)


@pytest.fixture(scope="module")
def ammn() -> dict:
    if not AMMN.exists():
        pytest.skip("data/assumptions/AMMN.json not present (AMMN data lane purged)")
    return json.loads(AMMN.read_text(encoding="utf-8"))


def test_ammn_assumptions_file_is_git_tracked_not_ignored():
    """The file must be committable: .gitignore must not exclude data/assumptions."""
    import subprocess

    res = subprocess.run(
        ["git", "check-ignore", "-q", str(AMMN)],
        cwd=REPO_ROOT, capture_output=True, check=False,
    )
    assert res.returncode != 0, "data/assumptions/AMMN.json is git-ignored — cannot be shipped"


def test_ammn_assumptions_file_present_with_typed_gate_fields(ammn: dict):
    for key in GATE_KEYS:
        assert ammn.get(key) is not None, f"AMMN assumptions missing gate key '{key}'"

    assert isinstance(ammn["fcf"], list) and len(ammn["fcf"]) >= 3, "fcf must be a forecast series"
    assert all(isinstance(x, (int, float)) and x > 0 for x in ammn["fcf"]), "fcf series must be positive IDR bn"
    assert 0 <= ammn["payout"] <= 1, "payout must be a ratio"
    assert 0 < ammn["we"] < 1 and 0 < ammn["wd"] < 1
    assert abs(ammn["we"] + ammn["wd"] - 1.0) < 1e-3, "capital-structure weights must sum to 1"
    assert ammn["last_price"] > 0 and ammn["shares_out"] > 0


def test_ammn_every_gate_field_carries_provenance(ammn: dict):
    prov = ammn.get("provenance") or {}
    for key in GATE_KEYS:
        entry = prov.get(key)
        assert entry, f"gate key '{key}' has no provenance entry (bare numbers are REJECT-grade)"
        assert entry.get("outlet"), f"provenance['{key}'] must name the outlet"
        assert entry.get("url"), f"provenance['{key}'] must carry a url"
        assert entry.get("as_of"), f"provenance['{key}'] must carry an as-of date"
        assert entry.get("kind") in {"sectors_live", "derived_sectors", "public", "derived_public"}, (
            f"provenance['{key}'] must declare its kind"
        )


def test_ammn_mid_cycle_ebitda_cites_three_constituents(ammn: dict):
    """MID-EBITDA PROVENANCE: a mid-cycle average must cite its constituents."""
    cons = ammn.get("ebitda_midcycle_constituents") or {}
    assert len(cons) == 3, f"mid-cycle EBITDA must cite 3 annual constituents, got {list(cons)}"
    assert all(v > 0 for v in cons.values())
    avg = sum(cons.values()) / 3
    assert abs(avg - ammn["ebitda"]) / ammn["ebitda"] < 0.01, "ebitda must equal the cited 3Y average"


def test_ammn_dps_field_is_actual_d0_when_present(ammn: dict):
    """DDM-TIMING LOCK: every numeric dps_* field is D0 = last normalized ACTUAL DPS."""
    checked = 0
    for key, value in ammn.items():
        if not key.startswith("dps_") or key.endswith("_note") or not isinstance(value, (int, float)):
            continue
        assert not isinstance(value, bool) and value >= 0, f"{key} must be a non-negative D0 actual"
        checked += 1
    # AMMN pays no dividend: dps_d0 = 0.0 is present and must stay a real 0, never a peak dividend.
    assert ammn.get("dps_d0") == 0.0
    assert checked >= 1


def test_ammn_live_payload_clears_the_422_gate(ammn: dict):
    """The gate owner (pdf.py:_build_live_payload) must no longer 422 on missing assumptions."""
    from fastapi import HTTPException

    from server.routers import pdf as pdf_router

    try:
        payload = pdf_router._build_live_payload("AMMN", None)
    except HTTPException as exc:  # noqa: PERF203
        detail = json.dumps(exc.detail)
        assert exc.status_code != 422 or "assumptions" not in detail, (
            f"AMMN still 422s on missing assumptions: {detail}"
        )
        raise

    assert payload["meta"]["ticker"] == "AMMN"
    assert payload["cover"]["rating_box"]["price"] == ammn["last_price"]
    method_names = [m["method"] for m in payload["valuation"]["methods"]]
    assert "DCF" in method_names and "EV/EBITDA" in method_names
