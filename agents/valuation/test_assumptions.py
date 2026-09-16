"""Tests for agents.valuation.assumptions - news & sentiment assumption modulation."""

import pytest
from agents.valuation.assumptions import adjust_assumptions


def test_news_driven_capex_boost_fires_when_count_gt_20_and_avg_sent_gt_0():
    """News-driven Capex boost fires when count>20 AND avg_sent>0."""
    base = {"revenue_growth": 0.08, "capex_pct_revenue": 0.05, "capex": 500.0}
    
    # Positive case: 25 items (>20) with positive sentiment 0.7 (>0)
    news = [{"score": 0.7, "date": "2026-09-01"}] * 25
    out = adjust_assumptions("BBCA", base, news=news, sentiment=None)
    
    assert out["capex_multiplier"] > 1.0
    assert out["capex_multiplier"] <= 1.10
    # At avg_sent=0.7, boost is 7% -> multiplier 1.07
    assert pytest.approx(out["capex_multiplier"], rel=1e-3) == 1.07
    assert out["capex_pct_revenue"] > base["capex_pct_revenue"]
    assert pytest.approx(out["capex_pct_revenue"], rel=1e-3) == 0.0535
    assert out["capex"] > base["capex"]
    assert pytest.approx(out["capex"], rel=1e-3) == 535.0
    assert out["news_count_last_30d"] == 25
    assert pytest.approx(out["avg_news_sentiment"], rel=1e-3) == 0.7
    
    # Boundary case: count <= 20 does NOT fire
    news_few = [{"score": 0.7, "date": "2026-09-01"}] * 20
    out_few = adjust_assumptions("BBCA", base, news=news_few, sentiment=None)
    assert out_few["capex_multiplier"] == 1.0
    assert out_few["capex_pct_revenue"] == base["capex_pct_revenue"]
    
    # Negative sentiment case: avg_sent <= 0 does NOT fire
    news_neg = [{"score": -0.4, "date": "2026-09-01"}] * 25
    out_neg = adjust_assumptions("BBCA", base, news=news_neg, sentiment=None)
    assert out_neg["capex_multiplier"] == 1.0
    assert out_neg["capex_pct_revenue"] == base["capex_pct_revenue"]


def test_sentiment_driven_revenue_growth_modulation_fires_at_both_extremes():
    """Sentiment-driven revenue growth modulation fires at both extremes (bullish > 0.6, bearish < -0.6)."""
    base = {"revenue_growth": 0.10, "capex_pct_revenue": 0.05}

    # 1. Bullish extreme: score = 1.0 -> boost up to +15%
    sent_bullish_max = {"score": 1.0, "count": 100}
    out_bullish_max = adjust_assumptions("BBCA", base, news=None, sentiment=sent_bullish_max)
    assert pytest.approx(out_bullish_max["revenue_growth_multiplier"], rel=1e-3) == 1.15
    assert pytest.approx(out_bullish_max["revenue_growth"], rel=1e-3) == 0.115
    assert out_bullish_max["revenue_growth"] > base["revenue_growth"]

    # Bullish intermediate: score = 0.8 -> boost +7.5%
    sent_bullish_mid = {"score": 0.8}
    out_bullish_mid = adjust_assumptions("BBCA", base, news=None, sentiment=sent_bullish_mid)
    assert pytest.approx(out_bullish_mid["revenue_growth_multiplier"], rel=1e-3) == 1.075
    assert pytest.approx(out_bullish_mid["revenue_growth"], rel=1e-3) == 0.1075

    # 2. Bearish extreme: score = -1.0 -> cut down to -15%
    sent_bearish_max = {"score": -1.0, "count": 100}
    out_bearish_max = adjust_assumptions("BBCA", base, news=None, sentiment=sent_bearish_max)
    assert pytest.approx(out_bearish_max["revenue_growth_multiplier"], rel=1e-3) == 0.85
    assert pytest.approx(out_bearish_max["revenue_growth"], rel=1e-3) == 0.085
    assert out_bearish_max["revenue_growth"] < base["revenue_growth"]

    # Bearish intermediate: score = -0.8 -> cut -7.5%
    sent_bearish_mid = {"score": -0.8}
    out_bearish_mid = adjust_assumptions("BBCA", base, news=None, sentiment=sent_bearish_mid)
    assert pytest.approx(out_bearish_mid["revenue_growth_multiplier"], rel=1e-3) == 0.925
    assert pytest.approx(out_bearish_mid["revenue_growth"], rel=1e-3) == 0.0925

    # 3. Neutral zone: -0.6 <= score <= 0.6 -> no adjustment (multiplier = 1.0)
    sent_neutral = {"score": 0.3}
    out_neutral = adjust_assumptions("BBCA", base, news=None, sentiment=sent_neutral)
    assert out_neutral["revenue_growth_multiplier"] == 1.0
    assert out_neutral["revenue_growth"] == base["revenue_growth"]


def test_fallback_to_base_assumptions_when_news_or_sentiment_unavailable():
    """When news/sentiment unavailable, falls back cleanly to base assumptions."""
    base = {"revenue_growth": 0.08, "capex_pct_revenue": 0.05, "wacc": 0.09}

    # None inputs
    out_none = adjust_assumptions("BBCA", base, news=None, sentiment=None)
    assert out_none["revenue_growth"] == base["revenue_growth"]
    assert out_none["capex_pct_revenue"] == base["capex_pct_revenue"]
    assert out_none["wacc"] == base["wacc"]
    assert out_none["revenue_growth_multiplier"] == 1.0
    assert out_none["capex_multiplier"] == 1.0
    assert out_none["notes"] == []

    # Empty inputs
    out_empty = adjust_assumptions("BBCA", base, news=[], sentiment={})
    assert out_empty["revenue_growth"] == base["revenue_growth"]
    assert out_empty["capex_pct_revenue"] == base["capex_pct_revenue"]
    assert out_empty["revenue_growth_multiplier"] == 1.0
    assert out_empty["capex_multiplier"] == 1.0


def test_list_assumptions_modulation():
    """Verify that multi-period projection lists are modulated element-wise."""
    base = {
        "revenue_growth": [0.10, 0.09, 0.08],
        "capex_pct_revenue": [0.05, 0.05, 0.04],
    }
    sent = {"score": 1.0}  # +15%
    news = [{"score": 1.0, "date": "2026-09-01"}] * 25  # +10%
    out = adjust_assumptions("MTEL", base, news=news, sentiment=sent)

    assert pytest.approx(out["revenue_growth"][0], rel=1e-3) == 0.115
    assert pytest.approx(out["revenue_growth"][1], rel=1e-3) == 0.1035
    assert pytest.approx(out["revenue_growth"][2], rel=1e-3) == 0.092
    assert pytest.approx(out["capex_pct_revenue"][0], rel=1e-3) == 0.055
    assert pytest.approx(out["capex_pct_revenue"][1], rel=1e-3) == 0.055
    assert pytest.approx(out["capex_pct_revenue"][2], rel=1e-3) == 0.044
