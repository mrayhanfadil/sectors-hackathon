"""Integration and unit tests for the /api/dcf/{ticker} endpoint and ADK DCF tools.

Covers:
  - test_endpoint_smoke_ratu: GET /api/dcf/RATU -> 200, has wacc, valuation, recommendation
  - test_endpoint_smoke_bbcA: GET /api/dcf/bbcA bare -> 422 (no seed-math)
  - test_endpoint_smoke_ratu_declared_inputs: declared overrides -> 200 full shape
  - test_endpoint_review_required: extreme upside triggers Review Required rating gate
  - test_endpoint_invalid_ticker: fallback on unknown ticker returns 200 (not 500)
  - test_endpoint_overrides_parsing: overrides={"rf": 0.10} applied correctly
  - test_endpoint_sensitivity_shape: 5x5 matrix when steps=2 (2*steps+1 on each axis)
  - test_endpoint_scenarios_structure: BEAR/BASE/BULL scenarios present
  - test_adk_friend_tools_unit: ADK FunctionTool wrappers behave correctly
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.main import app
from agents.adk.tools.dcf_friend import (
    calc_wacc_full,
    calc_fcff_projection,
    calc_terminal_value_check,
    calc_dcf_full_valuation,
    calc_recommendation,
    calc_sensitivity_grid,
    calc_scenarios,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# Explicit test inputs (Sep 2026): prod seed bases killed, so every valuation
# driver must be declared. Round fixture numbers — obviously test-only.
FULL_OV = {
    "rf": 0.0696, "beta": 0.9, "erp": 0.07, "cod": 0.06,
    "revenue": 5000e9, "ebit_margin": 0.20, "g1": 0.08, "g": 0.03,
    "tax": 0.22, "capex_pct": 0.06, "nwc_pct": 0.05,
    "shares_out": 5e9, "last_price": 2000.0,
}


def test_endpoint_smoke_ratu(client):
    """GET /api/dcf/RATU bare -> 422 (file lacks WACC inputs; no seed-math)."""
    res = client.get("/api/dcf/RATU")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    assert "RATU" in res.text


def test_endpoint_smoke_ratu_declared_inputs(client):
    """GET /api/dcf/RATU with declared overrides -> 200, full shape."""
    import json as _json

    res = client.get(f"/api/dcf/RATU?overrides={_json.dumps(FULL_OV)}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert isinstance(data, dict), "Response must be a dict"
    assert "wacc" in data, "Missing 'wacc' in response"
    assert "valuation" in data, "Missing 'valuation' in response"
    assert "recommendation" in data, "Missing 'recommendation' in response"
    assert "projection" in data, "Missing 'projection' in response"
    assert "sensitivity" in data, "Missing 'sensitivity' in response"
    assert "scenarios" in data, "Missing 'scenarios' in response"
    assert "provenance" in data, "Missing 'provenance' in response"
    assert "/api/dcf endpoint" in data["provenance"]
    assert data["valuation"]["fair_value_per_share"] is not None


def test_endpoint_smoke_bbcA(client):
    """GET /api/dcf/bbcA bare -> 422 (no seed-math, case-insensitive ticker)."""
    res = client.get("/api/dcf/bbcA")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    assert "BBCA" in res.text


def test_endpoint_review_required(client):
    """Overrides with extreme divergence trigger 'Review Required' gate."""
    overrides = json.dumps({**FULL_OV, "price": 50.0, "last_price": 50.0})
    res = client.get(f"/api/dcf/RATU?overrides={overrides}")
    assert res.status_code == 200
    data = res.json()
    assert data["recommendation"]["rating"] == "Review Required"
    assert "reason_override" in data["recommendation"]
    assert "defensible range" in data["recommendation"]["reason_override"]


def test_endpoint_invalid_ticker(client):
    """GET /api/dcf/NOPE -> returns dict (with error key or valid fallback), NOT 500."""
    res = client.get("/api/dcf/NOPE")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    assert "NOPE" in res.text


def test_endpoint_overrides_parsing(client):
    """Overrides={'rf': 0.10} returns 200 and reflects the custom risk-free rate."""
    overrides = json.dumps({**FULL_OV, "rf": 0.10})
    res = client.get(f"/api/dcf/RATU?overrides={overrides}")
    assert res.status_code == 200
    data = res.json()
    assert data["wacc"]["rf"] == pytest.approx(0.10)


def test_endpoint_sensitivity_shape(client):
    """Sensitivity grid has shape len = 2*steps+1 on each axis."""
    overrides = json.dumps({**FULL_OV, "sens_steps": 2})
    res = client.get(f"/api/dcf/RATU?overrides={overrides}")
    assert res.status_code == 200
    data = res.json()
    sens = data["sensitivity"]
    assert "fair_value" in sens
    assert "upside" in sens
    assert "wacc_axis" in sens
    assert "g_axis" in sens
    assert len(sens["fair_value"]) == 5
    assert all(len(row) == 5 for row in sens["fair_value"])
    assert len(sens["wacc_axis"]) == 5
    assert len(sens["g_axis"]) == 5
    assert sens["stats"]["n_cells"] == 25


def test_endpoint_scenarios_structure(client):
    """Scenarios payload contains BEAR, BASE, and BULL structures."""
    import json as _json2

    res = client.get(f"/api/dcf/RATU?overrides={_json2.dumps(FULL_OV)}")
    assert res.status_code == 200
    data = res.json()
    scen = data["scenarios"]
    assert "BEAR" in scen
    assert "BASE" in scen
    assert "BULL" in scen
    for name in ("BEAR", "BASE", "BULL"):
        assert "fair_value_per_share" in scen[name]
        assert "rating" in scen[name]
        assert "revenue_growth_y1" in scen[name]


def test_adk_friend_tools_unit():
    """Unit test ADK function tools in agents/adk/tools/dcf_friend.py."""
    # 1. calc_wacc_full
    wacc_res = calc_wacc_full(
        rf=0.065, beta=1.0, erp=0.07, cod=0.085, market_cap=1e12, total_debt=2e11, tax=0.22
    )
    assert "wacc" in wacc_res
    assert "components" in wacc_res
    assert isinstance(wacc_res["components"], list)
    assert len(wacc_res["components"]) >= 10

    # 2. calc_fcff_projection
    proj_res = calc_fcff_projection(
        revenue_t0=10000e9, g1=0.08, g_terminal=0.025, years=5, ebit_margin=0.15, tax=0.22, capex_pct=0.06, nwc_pct=0.10
    )
    assert "projection" in proj_res
    assert len(proj_res["projection"]) == 5
    assert proj_res["final_fcff"] > 0

    # 3. calc_terminal_value_check
    tv_res = calc_terminal_value_check(
        fcff_last=1000e9, ebitda_last=2000e9, wacc=0.10, g=0.025, years=5, enterprise_value=10000e9
    )
    assert tv_res["valid"] is True
    assert tv_res["terminal_value"] is not None
    assert tv_res["pv_terminal"] is not None
    assert tv_res["implied_exit_multiple"] is not None

    # 4. calc_recommendation
    rec_buy = calc_recommendation(fair_value=1200.0, market_price=1000.0)
    assert rec_buy["rating"] == "BUY"
    rec_rev = calc_recommendation(fair_value=2500.0, market_price=1000.0)
    assert rec_rev["rating"] == "Review Required"

    # 5. calc_sensitivity_grid
    snapshot = {
        "cash": 1000e9,
        "total_debt": 2000e9,
        "minority": 0.0,
        "shares_outstanding": 10e9,
        "price": 1000.0,
    }
    sens_res = calc_sensitivity_grid(
        proj=proj_res["projection"],
        wacc_base=0.10,
        g_base=0.025,
        snapshot=snapshot,
        steps=2,
    )
    assert len(sens_res["fair_value"]) == 5
    assert len(sens_res["wacc_axis"]) == 5

    # 6. calc_scenarios
    hist_std = {"rev_growth_sd": 0.03, "ebit_margin_sd": 0.01}
    scen_res = calc_scenarios(
        proj=proj_res["projection"],
        wacc_base=0.10,
        g_base=0.025,
        hist_std=hist_std,
        snapshot=snapshot,
    )
    assert "BEAR" in scen_res and "BASE" in scen_res and "BULL" in scen_res

    # 7. calc_dcf_full_valuation (explicit overrides — no prod seeds)
    full_res = calc_dcf_full_valuation("RATU", overrides=dict(FULL_OV))
    assert full_res["wacc"] is not None
    assert full_res["valuation"]["fair_value_per_share"] > 0
