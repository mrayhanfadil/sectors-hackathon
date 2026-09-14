"""The agent instructions must stay generic: any ticker, any licence, no baked-in numbers.

The failure this guards against is slow and invisible: a rule that starts as this name's rule and quietly
becomes part of the house doctrine, so the next ticker inherits another company's arithmetic.
"""
from __future__ import annotations

import re

import pytest

from agents.adk.agents import instructions as I

PAGE_RULES = ("HOUSE_FORMAT_RULE", "SLIDE_PAGES_RULE", "SLIDE5_RULE", "SLIDE6_RULE", "VALUATION_BASIS_RULE")
#: every agent instruction that builds or judges a PAGE
PAGE_BUILDERS = ("industry_instruction", "writer_instruction", "critic_instruction")
#: agents that only gather data — a page rule here is noise that dilutes their instruction
DATA_GATHERERS = ("collector_instruction", "news_harvester_instruction",
                  "modeler_instruction", "risk_instruction", "kpi_instruction")

THOUSANDS = re.compile(r"\b\d{1,3}(?:[.,]\d{3})+\b")
#: report tickers. BBTN is deliberately absent: the owner's rules cite it as a bank-table PATTERN
#: ("pola BBTN Exhibit 7-8"), which is a layout reference, not this report's arithmetic.
TICKERS = re.compile(r"\b(AMMN|BBCA|RATU|CDIA|MTEL|ADRO|ANTM|MDKA|INCO|TLKM)\b")
#: layout constants (a copy budget) are generic and allowed next to their label
LAYOUT = re.compile(r"(karakter|chars?|budget|pt\b|baris|halaman)", re.I)


@pytest.mark.parametrize("rule", PAGE_RULES)
def test_page_rules_carry_no_ticker_and_no_figures(rule: str):
    """A rule is a procedure. A ticker or a rupiah figure in one is a leak from a single report."""
    text = getattr(I, rule)
    tick = TICKERS.search(text)
    figure = next((m for m in THOUSANDS.finditer(text) if not LAYOUT.search(text[max(0, m.start() - 60):m.end() + 40])), None)
    assert tick is None, f"{rule} names a ticker: {tick.group(0) if tick else ''}"
    assert figure is None, f"{rule} bakes in a company figure: {figure.group(0) if figure else ''}"


def test_the_basis_rule_exists_and_is_generic_about_the_method():
    rule = I.VALUATION_BASIS_RULE
    for marker in ("different bases", "forward", "double-counts", "reconcile", "provenance",
                   "REJECTED", "GATE inputs", "EXCLUDED", "internally consistent"):
        assert marker.lower() in rule.lower(), f"the basis rule lost: {marker}"
    assert "every ticker" in rule.lower()


@pytest.mark.parametrize("name", PAGE_BUILDERS)
def test_page_builders_carry_the_basis_rule(name: str):
    assert "VALUATION BASIS DISCIPLINE" in getattr(I, name), f"{name} lost the valuation-basis rule"


@pytest.mark.parametrize("name", DATA_GATHERERS)
def test_data_gatherers_do_not_carry_page_rules(name: str):
    text = getattr(I, name)
    for marker in ("VALUATION BASIS DISCIPLINE", "SLIDE 5 — PEER VALUATION", "SLIDE 6 — INCOME STATEMENT"):
        assert marker not in text, f"{name} carries page rules it does not use: {marker}"


def test_every_rule_constant_is_composed_into_at_least_one_instruction():
    """A rule nobody concatenates is documentation, not enforcement — the exact failure mode this
    file exists for."""
    for rule in PAGE_RULES:
        text = getattr(I, rule)
        assert len(text) > 200, f"{rule} is suspiciously short"
        head = text.strip().splitlines()[0][:60]      # the constant's own opening line, not its name
        assert any(head in getattr(I, name) for name in PAGE_BUILDERS), \
            f"{rule} is not attached to any page-building instruction"


def test_rules_state_the_house_register_not_a_single_report():
    """Sanity: the rules are the owner's rules (deck pages, house terms), not generic filler."""
    assert "Page 2" in I.SLIDE_PAGES_RULE, "the deck-page rule lost its page-by-page structure"
    assert "Critic" in I.VALUATION_BASIS_RULE and "BUY" in I.VALUATION_BASIS_RULE
