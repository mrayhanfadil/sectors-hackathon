"""Pytest test suite for Valuation Method Selection Framework quintet audit (5/5 PASS).

Exercises each of the 5 quintet tickers with realistic financial parameters
and verifies deterministic method selection, thin data disclosures, SOTP cross-checks,
and rating override logic.
"""

from __future__ import annotations

import pytest

from agents.valuation.gates import evaluate
from scripts.audit_quintet_gates import QUINTET, EXPECTATIONS


def test_ratu_audit_verdict():
    """RATU: mature single-business oil holding -> FCFF/WACC DCF, no override."""
    ticker = "RATU"
    verdict = evaluate(ticker, **QUINTET[ticker])
    assert verdict.primary == "FCFF/WACC DCF"
    assert verdict.rating_override is None
    assert verdict.thin_data is False
    assert EXPECTATIONS[ticker](verdict) is True


def test_cdia_audit_verdict():
    """CDIA: 2y filing history (<4y) -> DCF (shortened horizon), thin_data=True, 1a_filing_history failed."""
    ticker = "CDIA"
    verdict = evaluate(ticker, **QUINTET[ticker])
    assert verdict.primary == "DCF (shortened horizon)"
    assert verdict.thin_data is True
    assert "1a_filing_history" in verdict.gates_failed
    assert EXPECTATIONS[ticker](verdict) is True


def test_mtel_audit_verdict():
    """MTEL: infra tower with NCI 25% (15-40% band) -> FCFF/WACC DCF with mandatory SOTP cross-check reason."""
    ticker = "MTEL"
    verdict = evaluate(ticker, **QUINTET[ticker])
    assert verdict.primary == "FCFF/WACC DCF"
    assert any("SOTP cross-check" in r for r in verdict.reasons)
    assert verdict.rating_override is None
    assert EXPECTATIONS[ticker](verdict) is True


def test_bbca_audit_verdict():
    """BBCA: tier-1 private bank -> Gate 0 financial institution route -> DDM / Excess Return."""
    ticker = "BBCA"
    verdict = evaluate(ticker, **QUINTET[ticker])
    assert verdict.primary == "DDM / Excess Return"
    assert verdict.rating_override is None
    assert EXPECTATIONS[ticker](verdict) is True


def test_adro_audit_verdict():
    """ADRO: commodity coal mining -> Gate 0/3 finite reserves route -> NAV / Reserve-based."""
    ticker = "ADRO"
    verdict = evaluate(ticker, **QUINTET[ticker])
    assert verdict.primary == "NAV / Reserve-based"
    assert verdict.rating_override is None
    assert EXPECTATIONS[ticker](verdict) is True

