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
    assert kf.get("headers") == ["Year to 31 Dec", "2024A", "2025A", "2026F", "2027F", "2028F"], kf.get("headers")
    assert kf.get("exhibit_title") == "Key Financials (2024A–2028F)", kf.get("exhibit_title")


def test_all_mandated_rows_present_in_order(payload):
    labels = [str(r[0]) for r in _kf(payload).get("rows") or []]
    assert labels == [
        "Revenue (Rpbn)", "EBITDA (Rpbn)", "EBITDA Growth (%)", "Net Profit (Rpbn)",
        "EPS (Rp)", "EPS Growth (%)", "PER (x)", "PBV (x)", "EV/EBITDA (x)",
    ], labels


def test_negatives_use_the_accounting_parenthesis_convention(payload):
    """Benchmark cover table prints (28,8) for a decline, never -28,8."""
    kf = _kf(payload)
    for r in kf.get("rows") or []:
        for cell in r[1:]:
            assert not str(cell).startswith("-"), (r[0], cell)
    eb_g = [cell for r in kf["rows"] if r[0] == "EBITDA Growth (%)" for cell in r[1:]]
    assert any(str(c).startswith("(") for c in eb_g), eb_g


DRIVER_PATH = REPO_ROOT / "data" / "drivers" / "AMMN.json"


def test_forecast_columns_trace_to_the_declared_basis(payload, assum):
    """Every forecast column must be traceable to the basis the exhibit declares — a cited path, an
    analyst series, or the labelled normalised fallback. Nothing else may reach the page."""
    kf = _kf(payload)
    basis = kf.get("forecast_basis")
    assert basis, "the exhibit must declare where its forecast columns came from"
    if basis == "third-party-estimate":
        doc = json.loads(DRIVER_PATH.read_text())
        fx = doc["fx_rp_bn_per_usd_mn"]
        for col, i in ((2, 0), (3, 1), (4, 2)):
            for row, key in (("Revenue", "revenue"), ("EBITDA", "ebitda"), ("Net Profit", "net_profit")):
                want = doc["drivers"][key]["path"][i] * fx
                assert _num(_cell(kf, row, col)) == pytest.approx(want, abs=1.5), (row, col)
        assert kf.get("forecast_attribution"), "a forecast path must be attributed"
        assert kf.get("forecast_as_of"), "a forecast path must carry an as-of date"
        # Owner instruction 13 Sep 2026: the deck is independent — the path is presented as the team's
        # estimate over the licensed dataset and no other research house is named. The disclosure that
        # survives is the substantive one: the columns are a projection, not realised figures.
        notes = " ".join(str(n) for n in kf.get("notes") or []).lower()
        assert "proyeksi" in notes or "bukan realisasi" in notes, \
            "the reader must be told the forecast columns are a projection, not realised figures"
        from server.report.forecast_path import RESEARCH_HOUSE_PATTERN

        label = str(kf.get("forecast_attribution") or "")
        assert "estimasi tim" in (notes + label.lower()), \
            "the columns must be presented as the team's own estimate"
        assert not RESEARCH_HOUSE_PATTERN.search(notes + label), \
            "no other research house may be named on the page"
    else:
        sc = (assum.get("sector_context") or {})["sectors_growth_forecast_2026"]
        rev25, rev26 = _num(_cell(kf, "Revenue", 1)), _num(_cell(kf, "Revenue", 2))
        ni25, ni26 = _num(_cell(kf, "Net Profit", 1)), _num(_cell(kf, "Net Profit", 2))
        assert rev26 == pytest.approx(rev25 * (1 + sc["revenue_growth"]), abs=1.5)
        assert ni26 == pytest.approx(ni25 * (1 + sc["eps_growth"]), abs=1.5)


def test_forecast_ebitda_matches_its_basis(payload, assum):
    kf = _kf(payload)
    if kf.get("forecast_basis") == "third-party-estimate":
        doc = json.loads(DRIVER_PATH.read_text())
        fx = doc["fx_rp_bn_per_usd_mn"]
        for col, i in ((2, 0), (3, 1), (4, 2)):
            assert _num(_cell(kf, "EBITDA", col)) == pytest.approx(
                doc["drivers"]["ebitda"]["path"][i] * fx, abs=1.5)
    else:
        cons = assum["ebitda_midcycle_constituents"]
        mid_tn = sum(float(v) for v in cons.values()) / len(cons) / 1e12
        for col in (2, 3, 4):
            assert _num(_cell(kf, "EBITDA", col)) == pytest.approx(mid_tn * 1000, abs=1.5)


def test_a_flat_column_set_is_only_allowed_when_it_is_labelled(payload):
    """Flat columns read as a growth forecast unless the exhibit says they are a normalised level.
    Either the basis is `midcycle-normalised` AND the note says so, or the columns must move."""
    kf = _kf(payload)
    basis = kf.get("forecast_basis")
    flat = all(_num(_cell(kf, "Revenue", c)) == _num(_cell(kf, "Revenue", 2)) for c in (3, 4))
    if flat:
        assert basis == "midcycle-normalised", f"flat columns under basis {basis!r}"
        assert any("normalised" in str(n).lower() for n in kf.get("notes") or []), \
            "flat columns must carry the normalised-level note"
    else:
        assert basis in ("third-party-estimate", "analyst"), basis
        assert kf.get("forecast_attribution"), "a moving path must be attributed"


def test_multiples_are_computed_at_todays_price(payload):
    kf = _kf(payload)
    price = float((payload["cover"]["rating_box"])["price"])
    eps26 = _num(_cell(kf, "EPS (Rp)", 2))
    assert _num(_cell(kf, "PER (x)", 2)) == pytest.approx(price / eps26, abs=0.15)


def test_katalis_paragraph_carries_a_priced_in_verdict(payload):
    body = (payload["cover"]["slide2"]["katalis"])["body"]
    assert "Katalis terverifikasi" in body
    assert "Priced-in" in body
    assert "relatif vs IHSG" in body or "relatif" in body
    # the raw pipeline housekeeping note must not leak into reader copy
    assert "cap API 90 hari" not in body


def test_valuasi_paragraph_has_the_four_mandated_blocks(payload):
    body = (payload["cover"]["slide2"]["valuasi"])["body"]
    assert "menggunakan" in body and "TP Rp" in body          # 1. methodology
    assert "CAGR" in body and "FY26F-FY28F" in body           # 2. forecast linkage
    assert "dibandingkan" in body and "rata-rata historis" in body  # 3. trading multiple
    assert "Risiko terhadap pandangan ini" in body            # 4. risk to view


def test_cover_copy_stays_within_the_one_pager_budget(payload):
    """The cover is a one-page spread (benchmark layout): paragraphs 1-3 plus the Key
    Financials exhibit have to share one page, so the generated copy has a hard length budget.
    Crossing it silently pushes the exhibit to the next page and breaks the layout."""
    s1 = payload["cover"]["slide1"]
    s2 = payload["cover"]["slide2"]
    budget = 2600  # chars of body copy, measured at 7.9pt in the 70% column
    total = (len(s1["financial_para"]["body"]) + len(s2["katalis"]["body"])
             + len(s2["valuasi"]["body"]))
    assert total <= budget, f"cover copy {total} chars exceeds the {budget} budget"
    for part in (s1["financial_para"]["body"], s2["katalis"]["body"], s2["valuasi"]["body"]):
        assert len(part) < 1500, len(part)
