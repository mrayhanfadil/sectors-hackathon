"""Slide-2 guards: the Key Financials forecast bridge must tie to the assumptions file.

These are tie-out tests, not snapshot tests. The exhibit's forecast columns are derived at
render time, so the way this breaks silently is a drift between the exhibit and the file the
rest of the report is priced off — e.g. someone re-points the revenue growth at a different
source, or a "forecast curve" creeps in where the file asserts a flat FCFF path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSUM_PATH = REPO_ROOT / "data" / "assumptions" / "AMMN.json"

pytestmark = pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")


@pytest.fixture(scope="module")
def payload() -> dict:
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


@pytest.fixture(scope="module")
def assum() -> dict:
    return json.loads(ASSUM_PATH.read_text(encoding="utf-8"))


def _kf(payload: dict) -> dict:
    return (payload.get("cover", {}).get("slide2", {}) or {}).get("key_financials", {}) or {}


def _cell(kf: dict, row_label: str, col_index: int):
    for r in kf.get("rows") or []:
        if str(r[0]).startswith(row_label):
            return r[1 + col_index]
    raise AssertionError(f"row {row_label!r} missing from Key Financials")


def _num(s):
    return float(str(s).replace(".", "").replace(",", "."))


def test_header_is_two_actual_three_forecast(payload):
    kf = _kf(payload)
    assert kf.get("headers") == ["(Rp bn)", "2024A", "2025A", "2026F", "2027F", "2028F"], kf.get("headers")
    assert kf.get("exhibit_title") == "Key Financials (2024A–2028F)", kf.get("exhibit_title")


def test_all_mandated_rows_present_in_order(payload):
    labels = [str(r[0]) for r in _kf(payload).get("rows") or []]
    assert labels == [
        "Revenue", "EBITDA", "EBITDA Growth (%)", "Net Profit", "EPS (Rp)",
        "EPS Growth (%)", "PER (x)", "PBV (x)", "EV/EBITDA (x)",
    ], labels


def test_revenue_and_eps_forecast_come_from_the_sectors_subsector_print(payload, assum):
    sc = (assum.get("sector_context") or {})["sectors_growth_forecast_2026"]
    kf = _kf(payload)
    rev25, rev26 = _num(_cell(kf, "Revenue", 1)), _num(_cell(kf, "Revenue", 2))
    ni25, ni26 = _num(_cell(kf, "Net Profit", 1)), _num(_cell(kf, "Net Profit", 2))
    assert rev26 == pytest.approx(rev25 * (1 + sc["revenue_growth"]), abs=1.5)
    assert ni26 == pytest.approx(ni25 * (1 + sc["eps_growth"]), abs=1.5)


def test_forecast_ebitda_is_the_files_own_mid_cycle_average(payload, assum):
    cons = assum["ebitda_midcycle_constituents"]
    mid_tn = sum(float(v) for v in cons.values()) / len(cons) / 1e12
    kf = _kf(payload)
    for col in (2, 3, 4):
        assert _num(_cell(kf, "EBITDA", col)) == pytest.approx(mid_tn * 1000, abs=1.5)


def test_forecast_years_are_flat_no_invented_growth_curve(payload):
    """The assumptions file asserts a FLAT FCFF path FY26F-FY30F; a rising curve here would
    contradict the file the valuation is priced off."""
    kf = _kf(payload)
    for row in ("Revenue", "EBITDA", "Net Profit", "EPS (Rp)"):
        v26, v27, v28 = (_num(_cell(kf, row, c)) for c in (2, 3, 4))
        assert v26 == v27 == v28, (row, v26, v27, v28)


def test_multiples_are_computed_at_todays_price(payload):
    kf = _kf(payload)
    price = float((payload["cover"]["rating_box"])["price"])
    eps26 = _num(_cell(kf, "EPS (Rp)", 2))
    assert _num(_cell(kf, "PER (x)", 2)) == pytest.approx(price / eps26, abs=0.15)


def test_katalis_paragraph_carries_a_priced_in_verdict(payload):
    body = (payload["cover"]["slide2"]["katalis"])["body"]
    assert "Katalis terverifikasi" in body
    assert "di-price-in" in body
    assert "relatif vs IHSG" in body or "relatif" in body
    # the raw pipeline housekeeping note must not leak into reader copy
    assert "cap API 90 hari" not in body


def test_valuasi_paragraph_has_the_four_mandated_blocks(payload):
    body = (payload["cover"]["slide2"]["valuasi"])["body"]
    assert "menggunakan" in body and "TP Rp" in body          # 1. methodology
    assert "CAGR" in body and "FY26F-FY28F" in body           # 2. forecast linkage
    assert "dibandingkan" in body and "rata-rata historis" in body  # 3. trading multiple
    assert "Risiko terhadap pandangan ini" in body            # 4. risk to view
