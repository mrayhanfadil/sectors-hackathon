"""The sensitivity page revamp (owner call, Sep 2026).

The page had to answer, in order: what moves the value, where the discount rate comes from, and
how the assumptions wire into the cash-flow lines. The numbers below are the contract: every
figure printed in a component must be the same figure the engine computed, and the prose must
not quote a different swing than the components next to it.
"""

from __future__ import annotations

import re

import pytest


@pytest.fixture(scope="module")
def payload() -> dict:
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


@pytest.fixture(scope="module")
def html() -> str:
    from server.routers.pdf import render_html_for_ticker

    _tpl, out, _payload = render_html_for_ticker("AMMN", None)
    return out


def test_levers_are_measured_one_at_a_time_at_the_base_case(payload: dict) -> None:
    """WACC moves with g held at base; g moves with WACC held at base."""
    page = payload["valuation_page"]
    sens = page["sensitivity"]
    grid = sens["fair_value"]
    base_row, base_col = sens["base"]
    lev = sens["levers"]

    wacc_col = [v for v in grid.iloc[:, base_col].tolist() if v is not None]
    g_row = [v for v in grid.iloc[base_row].tolist() if v is not None]
    assert lev["wacc"]["delta_rp"] == pytest.approx(max(wacc_col) - min(wacc_col))
    assert lev["g"]["delta_rp"] == pytest.approx(max(g_row) - min(g_row))
    assert lev["held_g"] == str(grid.columns[base_col])
    assert lev["held_wacc"] == str(grid.index[base_row])
    # the label the page prints must be the same number, not a re-rounded copy
    assert lev["wacc"]["delta_rp_label"] == f"{round(lev['wacc']['delta_rp']):,}".replace(",", ".")
    assert lev["dominant"] == ("WACC" if lev["wacc"]["delta_rp"] >= lev["g"]["delta_rp"] else "pertumbuhan akhir")


def test_the_prose_leaves_the_lever_numbers_to_the_cards(payload: dict) -> None:
    """One set of lever numbers on the page: the cards own them, the prose must not restate a
    second (and possibly different) swing, which is exactly what the old page did."""
    page = payload["valuation_page"]
    lev = page["sensitivity"]["levers"]
    narrative = " ".join(page["narrative"])
    assert lev["wacc"]["delta_rp_label"] not in narrative
    assert lev["g"]["delta_rp_label"] not in narrative
    assert "Parameter paling sensitif" not in narrative, "the old two-numbers framing came back"
    # the prose still carries what no component shows: the assumption wiring and the flag
    assert "Keterkaitan asumsi" in narrative and "UNRESOLVED" in narrative


def test_wacc_chain_matches_the_assumption_table_row_for_row(payload: dict) -> None:
    """The chain is a view of wacc_rows, so it can never drift from the full table."""
    page = payload["valuation_page"]
    chain = page["wacc_chain"]
    assert len(chain) == 4 and chain[-1]["total"] is True
    wacc_row = next(v for label, v, *_ in page["wacc_rows"] if str(label).lower().startswith("wacc ="))
    assert chain[-1]["value"] == wacc_row
    rows = {str(label).lower(): v for label, v, *_ in page["wacc_rows"]}

    def row(*needles: str) -> str:
        return next(v for label, v in rows.items() if all(n in label for n in needles))

    # each step names its inputs and lands on the table's own result
    assert chain[0]["value"] == row("cost of equity")
    assert row("risk-free") in chain[0]["formula"]
    assert row("beta") in chain[0]["formula"]
    assert row("erp") in chain[0]["formula"]
    assert chain[1]["value"] == row("after-tax")
    assert row("cost of debt pre-tax") in chain[1]["formula"]
    assert chain[2]["value"] == ""
    assert row("weight of equity") in chain[2]["formula"]
    for step in chain:
        assert "-" not in step["value"], f"a chain value failed to resolve: {step}"


def test_printed_page_carries_the_new_components(html: str) -> None:
    for marker in ('class="sens-ref"', 'class="lever-grid"', 'class="wacc-chain"'):
        assert marker in html, f"the revamped block lost {marker}"


def test_the_grid_states_where_it_sits_against_the_market_price(payload: dict) -> None:
    """The honest reading: every cell is below the traded price, so this leg is not the anchor."""
    page = payload["valuation_page"]
    sens = page["sensitivity"]
    market = float(page["drivers"]["price"])
    assert sens["swing"]["max"] < market, "the grid no longer sits below the market price"
    _tpl, html, _p = None, None, None
    from server.routers.pdf import render_html_for_ticker

    _tpl, html, _p = render_html_for_ticker("AMMN", None)
    assert "Tabel ini hanya skenario model arus kas (DCF)" in html
    assert "ditopang cara pembanding di halaman sebelumnya" in html


def test_disclosures_still_print_after_the_revamp(html: str) -> None:
    """The revamp moved nothing out of the disclosure block: UNRESOLVED and the reserve limit stay."""
    text = re.sub(r"<[^>]+>", " ", html)
    assert "UNRESOLVED" in text
    assert "Reserve finite" in text or "cadangan" in text.lower()
