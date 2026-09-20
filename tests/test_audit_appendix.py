"""The audit disclosure page is a conditional appendix (Fadil, Sep 2026).

He read the shipped deck and asked for the two near-empty pages to go: the Exhibit 12
"Metode pembanding" table (a 2-row page repeating the valuation ladder) and the audit page,
which printed "Hasil audit: PASS" plus a sentence saying nothing was contested.

The audit page is NOT deleted: it is now an appendix that renders only when there is
something to disclose (non-PASS verdict, contested anchor, valuation ladder, or a
metric-consistency mismatch). These tests pin both halves of that contract, so the safety
net cannot be removed by accident and the empty page cannot come back.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "report_single.html"
COVER = Path(__file__).resolve().parents[1] / "templates" / "report_single.html"


def _served_html() -> str:
    from server.routers.pdf import render_html_for_ticker

    _tpl, html, _payload = render_html_for_ticker("AMMN", None)
    return html


def test_clean_pass_prints_no_audit_page() -> None:
    """AMMN audits PASS with nothing contested, so the deck must not carry the page."""
    html = _served_html()
    assert "Hasil audit" not in html, "the audit page printed on a clean PASS"
    assert "Catatan Audit" not in html, "the audit section header printed on a clean PASS"


def test_the_exhibit_12_method_table_is_gone() -> None:
    """The 2-row cross-check table was removed; its title must not come back unnoticed."""
    html = _served_html()
    assert "Metode pembanding" not in html, "the removed Exhibit 12 table is being rendered again"


def test_audit_page_still_renders_when_there_is_something_to_disclose() -> None:
    """The guard must be a condition, not a deletion - REJECT/dissent still gets a page.

    The real REJECT render is exercised end-to-end by
    agents/valuation/test_reject_downgrade.py; this pins the template-level condition so a
    future edit cannot turn the appendix into dead code.
    """
    tpl = TEMPLATE.read_text(encoding="utf-8")
    assert "_audit_prints" in tpl, "the audit page lost its render condition"
    guard = re.search(r"\{% set _audit_prints = (.+) %\}", tpl)
    assert guard, "the audit render condition is no longer a single readable expression"
    expr = guard.group(1)
    for trigger in ("verdict') != 'PASS'", "anchor_contested", "ladder", "inconsistency_report"):
        assert trigger in expr, f"the audit appendix no longer reacts to {trigger}"


def test_audit_appendix_sits_at_the_back_of_the_deck() -> None:
    """An appendix that renders last keeps the 11 numbered pages contiguous."""
    tpl = TEMPLATE.read_text(encoding="utf-8")
    assert tpl.index("AUDIT DISCLOSURE (conditional appendix, printed LAST)") > tpl.index(
        "PAGE 5 - PEERS + RISKS + DISCLAIMER"
    ), "the audit appendix drifted back into the middle of the deck"
    assert "{{ m.pagefoot(12, ns) }}" in tpl, "the appendix lost its own page number"


def test_footer_numbers_stay_sequential_on_the_shipped_deck() -> None:
    """11 pages, numbered 1..11 with no gap where the removed pages used to be."""
    html = _served_html()
    numbers = sorted({int(n) for n in re.findall(r"back of this report · (\d+)", html)})
    assert numbers == list(range(1, len(numbers) + 1)), f"footers are not sequential: {numbers}"
    assert len(numbers) == 11, f"expected the 11-page deck, found {len(numbers)} numbered pages"
