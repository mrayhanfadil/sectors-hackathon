"""2A+4F forecast scheme tests (Lane N-FORECAST).

Covers:
  1. Projection math: forecast_t = last-actual x (1+g)^t (agents/valuation/forecast.py).
  2. Growth resolution: g from assumptions + news/sentiment overlay, clean fallback.
  3. Cell traceability: every forecast cell cites base + g + t + formula + source.
  4. ACES fixture 2A+4F: FY24A-FY25A actuals preserved (yfinance-verified),
     FY26F-FY29F match the formula, growth rate + source embedded in source strings.
  5. Live inline payload (server/routers/pdf.py) emits 6 columns via the same module.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.valuation.forecast import (  # noqa: E402
    build_trend_forecast,
    project_series,
    resolve_growth,
)

ACES_FIXTURE = REPO_ROOT / "scripts" / "fixtures" / "aces_report_data.json"
EXPECTED_YEARS = ["FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"]


# --- 1. projection math -------------------------------------------------------

def test_project_series_math():
    """forecast_t = base x (1+g)^t exactly."""
    got = project_series(1000.0, 0.05, 4)
    for t, v in enumerate(got, 1):
        assert v == pytest.approx(1000.0 * (1.05 ** t), rel=1e-9)


def test_project_series_zero_growth_flat():
    assert project_series(500.0, 0.0, 4) == [500.0] * 4


# --- 2. growth resolution -----------------------------------------------------

def test_resolve_growth_fallback_without_signals():
    """No news/sentiment -> clean fallback to base assumption, multiplier 1.0."""
    r = resolve_growth({"revenue_growth": 0.022}, news=None, sentiment=None)
    assert r["g"] == pytest.approx(0.022)
    assert r["base_g"] == pytest.approx(0.022)
    assert r["g_key"] == "revenue_growth"
    assert r["revenue_growth_multiplier"] == pytest.approx(1.0)


def test_resolve_growth_bullish_sentiment_boosts():
    """Bullish sentiment (>0.6) boosts g; boost is documented, not silent."""
    base = resolve_growth({"revenue_growth": 0.022}, sentiment={"score": 1.0})
    assert base["g"] > 0.022
    assert base["g"] == pytest.approx(0.022 * 1.15, rel=1e-6)
    assert base["sentiment_score"] == pytest.approx(1.0)
    assert any("Bullish" in n for n in base["notes"])


def test_resolve_growth_missing_key_uses_fallback():
    r = resolve_growth({}, fallback_g=0.015)
    assert r["g"] == pytest.approx(0.015)
    assert r["g_key"] == "fallback_g"


# --- 3. scheme + traceability -------------------------------------------------

def test_build_trend_default_labels_2a4f():
    fc = build_trend_forecast({"m": [1.0, 2.0]}, {"m": 0.01}, {"m": "test"})
    assert fc["years"] == EXPECTED_YEARS
    assert fc["years"][:2] == ["FY24A", "FY25A"]
    assert all(y.endswith("F") for y in fc["years"][2:])


def test_build_trend_traceability_every_cell():
    fc = build_trend_forecast(
        {"revenue": [8580.0, 8640.0]},
        {"revenue": 0.022},
        {"revenue": "g=+2,2% (SSSG H1-2026, Kontan 2026-07-21)"},
    )
    cells = fc["traces"]["revenue"]
    assert len(cells) == 6
    for c in cells[:2]:
        assert c["kind"] == "A" and c["t"] == 0
    for i, c in enumerate(cells[2:], 1):
        assert c["kind"] == "F"
        assert c["base"] == 8640.0 and c["g"] == pytest.approx(0.022) and c["t"] == i
        assert c["value"] == pytest.approx(8640.0 * (1.022 ** i), abs=1.0)
        assert "Kontan" in c["source"]


def test_build_trend_rejects_wrong_label_scheme():
    with pytest.raises(AssertionError):
        build_trend_forecast({"m": [1.0, 2.0]}, {"m": 0.01}, {"m": "s"},
                             years=["FY22A", "FY23A", "FY24A", "FY25A", "TTM", "FY26F"])


# --- 4. ACES fixture ----------------------------------------------------------

@pytest.fixture(scope="module")
def aces():
    assert ACES_FIXTURE.exists(), f"missing {ACES_FIXTURE}"
    return json.loads(ACES_FIXTURE.read_text(encoding="utf-8"))


def test_aces_exhibit_chart_2a4f(aces):
    ex = aces["exhibits"][0]
    assert ex["chart"]["data"]["labels"] == EXPECTED_YEARS
    rev = ex["chart"]["data"]["datasets"][0]["data"]
    ni = ex["chart"]["data"]["datasets"][1]["data"]
    assert rev[:2] == [8580, 8640] and ni[:2] == [892, 669]  # yfinance-verified actuals
    assert rev[2:] == [pytest.approx(v, abs=1.0) for v in project_series(8640, 0.022)]
    assert ni[2:] == [pytest.approx(v, abs=1.0) for v in project_series(669, 0.03)]
    assert "2,2%" in ex["source"] and "3,0%" in ex["source"]
    assert "Kontan" in ex["source"] and "calc_dcf" in ex["source"] and "forecast.py" in ex["source"]


def test_aces_financial_highlights_2a4f(aces):
    fh = aces["financial_highlights"]
    assert fh["years"] == EXPECTED_YEARS
    rows = {r[0]: r[1:] for r in fh["rows"]}
    assert rows["Pendapatan (Rp bn)"][:2] == [8580, 8640]
    assert rows["Laba Bersih (Rp bn)"][:2] == [892, 669]
    assert rows["Pendapatan (Rp bn)"][2:] == [pytest.approx(v, abs=1.0) for v in project_series(8640, 0.022)]
    assert rows["Laba Bersih (Rp bn)"][2:] == [pytest.approx(v, abs=1.0) for v in project_series(669, 0.03)]
    # Net margin F recomputed = NI F / revenue F
    rev, ni = rows["Pendapatan (Rp bn)"], rows["Laba Bersih (Rp bn)"]
    for i, m in enumerate(rows["Net margin (%)"][2:], 2):
        assert m == pytest.approx(round(ni[i] / rev[i] * 100, 1), abs=0.15)
    assert "forecast.py" in fh["source"] and "2,2%" in fh["source"] and "3,0%" in fh["source"]


def test_aces_financials_income_2a4f(aces):
    inc = aces["financials"][0]
    assert inc["headers"] == ["Rp bn", *EXPECTED_YEARS]
    rows = {r[0]: r[1:] for r in inc["rows"]}
    assert rows["Pendapatan"] == [8580, 8640, 8830, 9024, 9223, 9426]
    assert rows["Laba bersih"] == [892, 669, 689, 710, 731, 753]
    assert rows["Laba kotor"] == [4180, 4120, 4211, 4303, 4398, 4495]
    assert rows["Laba operasi"] == [1020, 624, 643, 662, 682, 702]
    assert "forecast.py" in inc["source"]


def test_aces_statements_income_balance(aces):
    income = aces["financial_statements"]["income"]
    assert income["headers"] == ["Akun Laba Rugi", *EXPECTED_YEARS]
    rev = [r for r in income["rows"] if r[0] == "Pendapatan"][0][1:]
    assert rev == ["8.580", "8.640", "8.830", "9.024", "9.223", "9.426"]
    assert "forecast.py" in income["source"]
    bal = aces["financial_statements"]["balance"]
    assert bal["headers"] == ["Pos Neraca", "FY24A", "FY25A"]  # actuals only, no invented BS forecast
    eq = [r for r in bal["rows"] if r[0] == "Total Ekuitas"][0][1:]
    assert eq == ["6.512", "6.598"]


def test_aces_no_stale_5col_labels(aces):
    """No FY22A/FY23A/TTM column labels survive in converted FY exhibits."""
    blob = json.dumps([aces["exhibits"][0], aces["financial_highlights"],
                       aces["financials"][0], aces["financial_statements"]["income"],
                       aces["financial_statements"]["balance"]])
    for stale in ("FY22A", "FY23A"):
        assert stale not in blob
    assert '"TTM"' not in blob


# --- 5. live payload ----------------------------------------------------------

def test_live_inline_payload_6col():
    """pdf.py inline payload emits 2A+4F via the shared forecast module."""
    from fastapi.exceptions import HTTPException

    from server.routers.pdf import _build_live_payload  # noqa: E402
    # LOUD policy (keyless): ADRO assumptions lack required keys -> 422
    # naming them instead of a fabricated 6-col table.
    with pytest.raises(HTTPException) as exc_info:
        _build_live_payload("ADRO", None)  # ADRO: assumptions JSON, no static fixture -> live path
    assert exc_info.value.status_code == 422
    assert "ADRO" in str(exc_info.value.detail)
