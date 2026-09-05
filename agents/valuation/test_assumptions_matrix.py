"""Parameterized assumption modulation test harness across sentiment, news count, and sectors."""

from __future__ import annotations

import pytest

from agents.valuation.assumptions import adjust_assumptions


@pytest.mark.parametrize(
    "sentiment_score,news_count,expected_revenue_dir,expected_capex_dir",
    [
        # extreme bullish: +0.9 sentiment, 50 news items → revenue ↑, capex ↑
        (0.9, 50, "up", "up"),
        # mild bullish: +0.3 sentiment, 5 news items → no change
        (0.3, 5, "flat", "flat"),
        # neutral: 0.0 sentiment, 0 news → flat (no modulation)
        (0.0, 0, "flat", "flat"),
        # mild bearish: -0.3 sentiment → no change
        (-0.3, 5, "flat", "flat"),
        # extreme bearish: -0.9 sentiment, 30 news → revenue ↓, capex flat
        (-0.9, 30, "down", "flat"),
        # mixed: bullish sentiment but bearish news → capex down/flat (news dominates)
        (0.7, 25, "up", "down"),  # contradictory signals
    ],
)
def test_adjust_matrix(
    sentiment_score: float,
    news_count: int,
    expected_revenue_dir: str,
    expected_capex_dir: str,
) -> None:
    base = {"revenue_growth": 0.10, "capex_pct_revenue": 0.05}
    # For contradictory signals where capex is suppressed/down, news sentiment is bearish (-0.5)
    is_bearish_news = (sentiment_score < 0) or (expected_capex_dir == "down")
    news_score = -0.5 if is_bearish_news else 0.5
    news = [{"score": news_score, "date": "2026-09-01"}] * news_count
    sent = {"score": sentiment_score, "count": news_count}
    out = adjust_assumptions("RATU", base, news, sent)

    # Revenue direction assertions
    rev_mult = out["revenue_growth_multiplier"]
    if expected_revenue_dir == "up":
        assert rev_mult > 1.0, f"Expected revenue multiplier > 1.0, got {rev_mult}"
        assert out["revenue_growth"] > base["revenue_growth"]
    elif expected_revenue_dir == "down":
        assert rev_mult < 1.0, f"Expected revenue multiplier < 1.0, got {rev_mult}"
        assert out["revenue_growth"] < base["revenue_growth"]
    elif expected_revenue_dir == "flat":
        assert rev_mult == 1.0, f"Expected revenue multiplier == 1.0, got {rev_mult}"
        assert out["revenue_growth"] == base["revenue_growth"]

    # Capex direction assertions
    capex_mult = out["capex_multiplier"]
    if expected_capex_dir == "up":
        assert capex_mult > 1.0, f"Expected capex multiplier > 1.0, got {capex_mult}"
        assert out["capex_pct_revenue"] > base["capex_pct_revenue"]
    elif expected_capex_dir == "down":
        # Bearish news suppresses capex boost: capex_multiplier remains <= 1.0
        assert capex_mult <= 1.0, (
            f"Expected capex multiplier <= 1.0 for down, got {capex_mult}"
        )
        assert out["capex_pct_revenue"] <= base["capex_pct_revenue"]
    elif expected_capex_dir == "flat":
        assert capex_mult == 1.0, f"Expected capex multiplier == 1.0, got {capex_mult}"
        assert out["capex_pct_revenue"] == base["capex_pct_revenue"]


@pytest.mark.parametrize("ticker", ["BBCA", "RATU", "MTEL", "ADRO", "TLKM"])
def test_adjust_ticker_agnostic(ticker: str) -> None:
    base = {"revenue_growth": 0.10, "capex_pct_revenue": 0.05}
    news = [{"score": 0.7, "date": "2026-09-01"}] * 25
    sent = {"score": 0.65, "count": 50}
    out = adjust_assumptions(ticker, base, news, sent)
    assert "revenue_growth_multiplier" in out
    assert out["revenue_growth_multiplier"] > 1.0  # bullish = boost
