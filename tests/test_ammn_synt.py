"""AMMN-SYNT pins (12 Sep 2026): p7-8 live engine numbers.

Locks the DCF-deep-dive exhibits filled by server/report/ammn_fill.py to real
engine output (scripts/dcf_engine = the same year-end Gordon math the live
/api/report path uses) recomputed from data/assumptions/AMMN.json + the Sectors
harvest — the 38 baked template numbers (sensitivity 25 cells, scenarios,
EV bridge, mock WACC 11,83% / g 5,00%) must stay dead on BOTH render paths.

Keyless: reads the local harvest dir only (0 credits) and skips honestly when
it is absent.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FILL_DIR = PROJECT_ROOT / "output" / "cache" / "ammn_fill"
ASSUMP = PROJECT_ROOT / "data" / "assumptions" / "AMMN.json"

needs_fill = pytest.mark.skipif(
    not (FILL_DIR / "company_report_AMMN_multisection.json").exists(),
    reason="needs sibling harvest output/cache/ammn_fill (t_2c5f420e), 0 credits",
)

#: Baked template fallbacks the fill must keep dead (report_single.typ:700-741).
MOCKS = ("Rp 4.562", "Bebas Utang", "Rev +10%", "EBIT 32%", "11,83%", "Rp 4.979")


def _payload():
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


def _assum() -> dict:
    return json.loads(ASSUMP.read_text(encoding="utf-8"))


def _num(s) -> float:
    """Parse an ID-formatted number string back to float."""
    return float(str(s).replace(".", "").replace(",", "."))


@needs_fill
def test_sensitivity_matrix_is_25_live_dcf_cells():
    d = _payload()
    a = _assum()
    from scripts.dcf_engine import dcf

    ddd = d["dcf_deep_dive"]
    sens = ddd["sensitivity"]
    assert sens["headers"][0] == "WACC \\ g"
    assert sens["headers"][1:] == ["2,00%", "2,25%", "2,50% (Base)", "2,75%", "3,00%"]
    assert len(sens["rows"]) == 5 and all(len(r) == 6 for r in sens["rows"])
    assert sens["rows"][2][0] == "13,77% (Base)"

    c = d["cDcf"]["sensitivity"]
    assert c["stats"]["n_valid"] == 25 and c["stats"]["n_cells"] == 25
    assert len(c["fair_value"]) == 5 and all(len(r) == 5 for r in c["fair_value"])
    # axes centred on the WACC/g actually applied by the live engine
    assert c["wacc_axis"][2] == pytest.approx(0.13774, abs=1e-5)
    assert c["g_axis"] == [0.02, 0.0225, 0.025, 0.0275, 0.03]

    fcf = [float(x) * 1e9 for x in a["fcf"]]
    for i, w in enumerate(c["wacc_axis"]):
        for j, g in enumerate(c["g_axis"]):
            exp = round(dcf(fcf, w, g, shares_out=float(a["shares_out"]),
                            cash=float(a["cash"]),
                            net_debt=float(a["net_debt"]))["fv_per_share"], 2)
            assert c["fair_value"][i][j] == exp, (i, j, w, g)
    # base cell == headline FV engine; the printed sensitivity row carries the same number
    base_cell = c["fair_value"][2][2]
    assert base_cell == d["cDcf"]["valuation"]["fair_value_per_share"]
    assert base_cell == pytest.approx(d["valuation"]["methods"][0]["fv"], abs=1.0)
    assert f"Rp {round(base_cell)}" in sens["rows"][2][3]


@needs_fill
def test_scenarios_use_harvested_ebitda_band_not_generic_growth():
    d = _payload()
    a = _assum()
    from scripts.dcf_engine import ev_ebitda

    sc = d["dcf_deep_dive"]["scenarios"]
    assert len(sc["rows"]) == 3
    assert [r[0].split(" — ")[0] for r in sc["rows"]] == ["BEAR", "BASE", "BULL"]
    blob = json.dumps(sc, ensure_ascii=False)
    for generic in ("Rev +", "EBIT 29%", "EBIT 32%", "EBIT 35%"):
        assert generic not in blob
    for row in sc["rows"]:
        assert "EBITDA" in row[0] and row[1].startswith("Rp ")
        assert any(k in row[2] for k in ("BUY", "HOLD", "SELL"))

    out = d["cDcf"]["scenarios"]
    cons = {k: float(v) / 1e9 for k, v in a["ebitda_midcycle_constituents"].items()}
    expect = {
        "BEAR": min(cons.values()),
        "BASE": sum(cons.values()) / len(cons),
    }
    for name, eb_bn in expect.items():
        exp = ev_ebitda(eb_bn * 1e9, float(a["ev_multiple"]),
                        net_debt=float(a["net_debt"]),
                        shares_out=float(a["shares_out"]),
                        cash=float(a["cash"]))["fv_per_share"]
        assert out[name]["fair_value_per_share"] == exp, name
    # BULL = latest harvested quarter annualised (Sectors 8Q, newest row first)
    q0 = json.loads((FILL_DIR / "quarterly_AMMN_8.json").read_text(encoding="utf-8"))["data"][0]
    bull_eb = float(q0["ebitda"]) * 4.0
    assert out["BULL"]["ebitda_idr"] == pytest.approx(bull_eb, rel=1e-6)
    # monotone, and BASE ties to the published mid-cycle cross-check
    assert (out["BEAR"]["fair_value_per_share"] < out["BASE"]["fair_value_per_share"]
            < out["BULL"]["fair_value_per_share"])
    assert out["BASE"]["fair_value_per_share"] == pytest.approx(5872.75, abs=1.0)
    mid = " ".join(str(c) for r in d["valuation"]["midcycle"]["rows"] for c in r)
    assert "5,873" in mid


@needs_fill
def test_ev_bridge_carries_real_debt_and_cash():
    d = _payload()
    a = _assum()

    br = d["dcf_deep_dive"]["bridge"]
    assert len(br["rows"]) == 4
    joined = " ".join(str(c) for r in br["rows"] for c in r)
    assert "107.602" in joined            # EV (Rp bn) = PV FCFF + PV TV
    assert "+13.846" in joined            # real cash, Q1-2026
    assert "−110.786" in joined           # real gross debt, Q1-2026
    assert "Bebas Utang" not in joined
    debt_row = [r for r in br["rows"] if "Utang" in r[0]][0]
    assert debt_row[1].startswith("−") and "110.786" in debt_row[1]

    c = d["cDcf"]["valuation"]
    assert c["cash"] == float(a["cash"])
    assert c["total_debt"] == float(a["net_debt"])
    assert c["equity_value"] == pytest.approx(
        c["enterprise_value"] + c["cash"] - c["total_debt"], abs=0.05)
    assert c["fair_value_per_share"] == pytest.approx(
        c["equity_value"] / float(a["shares_out"]), abs=0.05)
    # Exhibit-8 card keys mirror the bridge in Rp bn (no dashes)
    g = d["valuation"]["dcf_grid"]
    assert g["pv_explicit"] == "45.180" and g["pv_tv"] == "62.421"
    assert g["ev"] == "107.602" and g["net_cash"] == "−96.940"


@needs_fill
def test_wacc_build_and_fcff_table_are_live():
    d = _payload()
    a = _assum()
    from scripts.dcf_engine import dcf

    wb = d["dcf_deep_dive"]["wacc_build"]
    assert len(wb["rows"]) == 9
    rows = {r[0]: r[1] for r in wb["rows"]}
    assert rows["Risk-Free Rate (Rf)"] == "7,10%"
    assert rows["Equity Risk Premium (ERP)"] == "6,69%"
    assert "1,407" in rows["Beta relevered (sektor Metals & Mining)"]
    assert rows["WACC Final Diterapkan"] == "13,77%"
    assert d["cDcf"]["wacc_table"][-1] == {"label": "WACC Final Diterapkan", "value": "13,77%"}
    assert len(d["cDcf"]["wacc_table"]) == 9

    m = [x for x in d["valuation"]["methods"] if x["method"] == "DCF"][0]
    tbl = m["table"]
    assert tbl["headers"][0] == "Komponen DCF (Rp bn)" and len(tbl["headers"]) == 6
    rows = {r[0]: r[1:] for r in tbl["rows"]}
    assert [round(_num(v), 1) for v in rows["Free Cash Flow (FCFF)"]] == a["fcf"]
    base = dcf([float(x) * 1e9 for x in a["fcf"]], d["cDcf"]["valuation"]["wacc"],
               float(a["g"]), shares_out=float(a["shares_out"]),
               cash=float(a["cash"]), net_debt=float(a["net_debt"]))
    for i, df in enumerate(base["discount_factors"]):
        assert _num(rows["Discount Factor"][i]) == pytest.approx(round(df, 3), abs=1e-3)
        assert _num(rows["Present Value FCFF"][i]) == pytest.approx(
            _num(rows["Free Cash Flow (FCFF)"][i]) * df, rel=5e-3)


@needs_fill
def test_html_path_kills_mocks_and_shows_live_engine():
    from server.routers.pdf import render_html_for_ticker

    tpl, html, data = render_html_for_ticker("AMMN", None)
    assert tpl == "single"
    for mock in MOCKS + ("+500",):
        assert mock not in html
    # deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md) replaced the friend-style block, so the
    # live markers are the three exhibits and the narrative the rules ask for.
    assert "FCFF Forecast, Terminal Value and Bridge to Equity" in html
    assert "Exhibit 8." in html and "Exhibit 9." in html and "Exhibit 10." in html
    assert "Blok 1 — Periode proyeksi eksplisit" in html
    assert "Blok 2 — Terminal value" in html
    assert "Blok 3 — Bridge ke equity value" in html
    assert "WACC Components" in html
    assert "Sensitivity Analysis" in html
    assert "Parameter paling sensitif" in html
    assert "sens-base" in html                       # the base case is highlighted        # live BULL FV
