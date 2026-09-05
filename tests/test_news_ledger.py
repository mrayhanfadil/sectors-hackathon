"""News/sentiment -> assumptions ledger bridge (synthetic fixtures, no network).

Covers: extraction of quantified forward drivers, provenance completeness,
conservative-conflict rule, no-overlay-without-citation, and the
adjust_assumptions wiring (extend, don't break).
"""

import pytest

from agents.valuation.assumptions import adjust_assumptions
from agents.valuation.news_ledger import apply_ledger_overlays, extract_drivers


def _news_fixture():
    return [
        {
            "url": "https://kontan.co.id/aces-sssg-h1",
            "date": "2026-07-21",
            "title": "Penjualan ACES Naik 2,2% di Semester I-2026",
            "source": "Kontan.co.id",
            "snippet": "PT Aspirasi Hidup Indonesia (ACES) mencatatkan pertumbuhan SSSG "
                       "sebesar 2,2% secara tahunan pada semester I-2026.",
            "tier": "t1",
        },
        {
            "url": "https://bisnis.com/aces-laba-2026",
            "date": "2026-08-10",
            "title": "ACES Target Laba Bersih Tumbuh 8% di 2026",
            "source": "Bisnis.com",
            "snippet": "Manajemen menargetkan laba bersih tumbuh 8% di full-year 2026 "
                       "ditopang efisiensi opex pasca rebrand.",
            "tier": "t1",
        },
        {
            "url": "https://idxchannel.com/aces-capex-gerai",
            "date": "2026-08-28",
            "title": "ACES Tambah 15 Gerai Baru, Capex Naik 10%",
            "source": "IDXChannel",
            "snippet": "ACES akan membuka 15 gerai baru AZKO hingga akhir 2026; "
                       "capex naik 10% untuk ekspansi dan store refresh.",
            "tier": "t1",
        },
    ]


def _social_fixture():
    return {
        "ticker": "ACES",
        "gauge": 58,
        "sources": [
            {
                "platform": "stockbit",
                "url": "https://stockbit.com/synthetic/aces-capex",
                "date": "2026-09-01",
                "text": "Capex ACES naik terus buat rebrand AZKO, margin bisa ketekan semester II.",
                "sentiment": "neutral",
            }
        ],
    }


# 1. extraction ------------------------------------------------------------

def test_extract_quantified_drivers_with_citations():
    ledger = extract_drivers(_news_fixture(), _social_fixture(), ticker="ACES")
    kinds = {d["kind"] for d in ledger["drivers"]}
    assert {"revenue_growth", "ni_growth", "capex"} <= kinds

    rev = next(d for d in ledger["drivers"] if d["kind"] == "revenue_growth")
    assert rev["value_pct"] == pytest.approx(2.2)
    assert rev["url"].startswith("https://")
    assert rev["date"] == "2026-07-21"

    ni = next(d for d in ledger["drivers"] if d["kind"] == "ni_growth")
    assert ni["value_pct"] == pytest.approx(8.0)

    cap = next(d for d in ledger["drivers"] if d["kind"] == "capex")
    assert cap["direction"] == "up"
    assert cap["magnitude_pct"] == pytest.approx(10.0)
    assert cap["horizon"] != ""


# 2. provenance completeness -------------------------------------------------

def test_every_driver_and_overlay_carries_provenance():
    ledger = extract_drivers(_news_fixture(), _social_fixture(), ticker="ACES")
    for d in ledger["drivers"]:
        assert d["url"] and d["date"] and d["quote"], f"driver missing provenance: {d}"

    base = {"g1": 0.04, "capex_pct": 0.30, "revenue_growth": 0.04}
    out = apply_ledger_overlays(base, ledger)
    assert out["news_overlays"]["overlays_applied"] != []
    for key, prov in out["news_overlays"]["overlays"].items():
        if prov.get("non_quantified"):
            continue
        assert prov["drivers"], f"overlay {key} has no drivers"
        for s in prov["drivers"]:
            assert s["url"] and s["date"] and s["quote"]
    # numeric keys stay plain floats (dcf_full-compatible)
    assert isinstance(out["g1"], float)
    assert isinstance(out["ni_growth"], float)
    assert isinstance(out["capex_pct"], float)


# 3. conservative conflict ----------------------------------------------------

def test_conflicting_revenue_guides_use_conservative_and_flag():
    news = [
        {
            "url": "https://kontan.co.id/aces-bull",
            "date": "2026-08-01",
            "title": "Broker Ramal Revenue ACES +8%",
            "source": "Kontan",
            "snippet": "Analis meramal revenue ACES tumbuh 8% di 2026.",
            "tier": "t2",
        },
        {
            "url": "https://bisnis.com/aces-cautious",
            "date": "2026-08-20",
            "title": "Manajemen Pandu Revenue +3%",
            "source": "Bisnis",
            "snippet": "Manajemen memandu pertumbuhan revenue hanya 3% full-year 2026.",
            "tier": "t1",
        },
    ]
    ledger = extract_drivers(news, None, ticker="ACES")
    assert len(ledger["conflicts"]) == 1
    assert ledger["conflicts"][0]["conservative_pct"] == pytest.approx(3.0)

    out = apply_ledger_overlays({"g1": 0.04}, ledger)
    assert out["g1"] == pytest.approx(0.03)  # conservative min wins
    prov = out["g1_overlay"]
    assert prov["conflict"] is True
    assert "conservative" in prov["conflict_note"].lower()
    assert len(prov["drivers"]) == 2  # both recorded


# 4. no overlay without citation ----------------------------------------------

def test_uncited_quantified_claim_produces_no_overlay():
    news = [
        {
            "title": "Revenue to grow 25%",
            "snippet": "Revenue expected to grow 25% next year.",
            "source": "rumor",
            # no url, no date -> uncited
        },
        {
            "url": "",
            "date": "2026-08-01",
            "snippet": "Laba bersih diproyeksi naik 30%.",
            "source": "chat",
        },
    ]
    ledger = extract_drivers(news, None, ticker="ACES")
    assert ledger["drivers"] == []
    assert ledger["dropped_uncited"] == 2

    base = {"g1": 0.04, "capex_pct": 0.30}
    out = apply_ledger_overlays(base, ledger)
    assert out["g1"] == base["g1"]
    assert out["capex_pct"] == base["capex_pct"]
    assert out["news_overlays"]["overlays_applied"] == []
    assert "ni_growth" not in out


# 6. ratio levels are not growth guides ------------------------------------------

def test_valuation_ratios_do_not_become_growth_drivers():
    news = [
        {
            "url": "https://stockanalysis.com/quote/idx/ACES/statistics",
            "date": "2026-09-04",
            "title": "ACES Statistics & Valuation Metrics",
            "source": "StockAnalysis",
            "snippet": "Trailing PE 8.02, Forward PE 7.41, PB 0.95. ROE 12.12%, ROIC 13.65%. "
                       "Revenue TTM 8.91T, Net Income 766.16B. Dividend yield 8.94%.",
            "tier": "t2",
        }
    ]
    ledger = extract_drivers(news, None, ticker="ACES")
    assert ledger["drivers"] == []  # ROIC/yield/PE levels are not forward guides


# 5. wiring: adjust_assumptions extends, never breaks --------------------------

def test_adjust_assumptions_applies_cited_ledger_overlays():
    base = {"revenue_growth": 0.08, "capex_pct": 0.30, "g1": 0.08, "wacc": 0.09}
    out = adjust_assumptions("ACES", base, news=_news_fixture(), sentiment={"score": 0.1})
    # cited 2.2% revenue guide overlays g1 / revenue_growth
    assert out["g1"] == pytest.approx(0.022)
    assert out["revenue_growth"] == pytest.approx(0.022)
    assert out["ni_growth"] == pytest.approx(0.08)
    # existing multiplier schema untouched
    assert out["revenue_growth_multiplier"] == 1.0
    assert out["capex_multiplier"] == 1.0
    assert out["wacc"] == base["wacc"]
    assert out["news_overlays"]["overlays_applied"] != []
    assert any("ledger" in n.lower() for n in out["notes"])


def test_adjust_assumptions_legacy_score_news_unchanged():
    # Old-style score-only items carry no citations -> no overlays, legacy math intact.
    base = {"revenue_growth": 0.10, "capex_pct_revenue": 0.05}
    news = [{"score": 0.7, "date": "2026-09-01"}] * 25
    out = adjust_assumptions("BBCA", base, news=news, sentiment={"score": 1.0})
    assert out["revenue_growth"] == pytest.approx(0.115)
    assert out["capex_pct_revenue"] == pytest.approx(0.0535)
    assert out["news_overlays"]["overlays_applied"] == []
