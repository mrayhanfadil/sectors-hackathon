"""§15 - no machine trace reaches a reader.

Owner critique 19 Sep 2026: the shipped PDF printed "yang dikembalikan endpoint", "via AMMN.json",
"kolom F", "feed yang dipakai" and "kriteria evaluasi gate terpenuhi". Every one of those is a
description of how the report was BUILT, printed inside the report - debug output wearing a
research note's clothes. The plain-language scan could not catch them because it enumerated
surfaces by hand and the industry page was not on the list.

These tests pin the three properties that make the rule hold:
  1. the payload scan walks EVERYTHING (so a new page is covered without anyone remembering it),
  2. it exempts citations (a source line may name its dataset) and non-printed bookkeeping,
  3. the render path checks the HTML that is actually printed, and refuses to publish on a hit.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from server.report.house_rules import (
    PLUMBING_PATTERNS,
    audit_house_rules,
    audit_printed_html,
    audit_plumbing,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_a_printed_field_with_a_machine_trace_is_a_violation() -> None:
    payload = {"industry_page": {"paragraphs": [
        {"body": "Emiten ini terbesar di lima emiten berkapitalisasi teratas yang dikembalikan endpoint."}
    ]}}
    hits = audit_plumbing(payload)
    assert len(hits) == 1
    assert "endpoint" in hits[0]
    assert "industry_page.paragraphs[0].body" in hits[0], "the hit must name where it came from"


def test_the_scan_walks_pages_nobody_enumerated() -> None:
    """The bug class: a surface that no hand-written list mentions."""
    payload = {"some_future_page": {"blocks": [{"note": "angka dari file jalur proyeksi"}]}}
    assert audit_plumbing(payload), "an unenumerated page must still be scanned"


def test_a_citation_may_name_its_dataset() -> None:
    """Attribution is owed to the reader: 'Sectors filings' in a source line is not plumbing."""
    payload = {"peers_page": {"sources": ["Sectors filings (keterbukaan IDX)", "Sectors screener"]}}
    assert audit_plumbing(payload) == []


def test_bookkeeping_that_never_prints_is_exempt() -> None:
    payload = {"critic": {"reasons": ["slide 2 gate rejected: kolom F"]},
               "house_rules": {"violations": ["payload missing industry_page"]}}
    assert audit_plumbing(payload) == []


def test_short_labels_are_not_scanned() -> None:
    """A table cell like '2026F' is a label; the plain-language scan owns code-shaped tags."""
    assert audit_plumbing({"key_financials": {"columns": ["2026F", "kolom"]}}) == []


def test_every_pattern_is_a_word_not_a_substring() -> None:
    """'aggregate' must not trip 'gate', 'feedback' must not trip 'feed'."""
    payload = {"page": {"body": "aggregate demand and reader feedback stay clean"}}
    assert audit_plumbing(payload) == []


def test_the_html_check_reads_visible_text_only() -> None:
    html = ("<html><head><style>.feed { color: red }</style><script>var gate = 1;</script></head>"
            "<body><p>Laba naik 27,7% per tahun.</p></body></html>")
    assert audit_printed_html(html) == []


def test_the_html_check_catches_what_a_reader_sees() -> None:
    html = "<div class='page'><p>dokumen terakhir yang dikembalikan endpoint berisi 11 transaksi</p></div>"
    hits = audit_printed_html(html)
    assert len(hits) == 1 and "endpoint" in hits[0]


def test_house_rules_aggregate_carries_the_plumbing_check() -> None:
    payload = {"cover": {"slide1": {"theme_title": "Harga naik"}},
               "risks": [{"bucket": "1", "detail": "proyeksi analis tidak dipublikasikan di feed"}]}
    report = audit_house_rules(payload)
    assert any("machine trace" in v for v in report["violations"])


@pytest.mark.parametrize("token", ["endpoint", "kolom F", "payload", "gate", "deterministik"])
def test_the_named_tokens_that_shipped_are_all_covered(token: str) -> None:
    assert any(re.search(p, token, re.IGNORECASE) for p in PLUMBING_PATTERNS), (
        f"{token!r} shipped on a printed page once - it must stay covered"
    )


def test_the_instruction_tells_the_agents_the_rule_exists() -> None:
    from agents.adk.agents import instructions as I

    rule = I.PLAIN_LANGUAGE_RULE
    assert "audit_plumbing" in rule, "the agents must know the gate that will reject them"
    for word in ("endpoint", "kolom", "payload", "gate"):
        assert word in rule.lower(), f"the rule must name {word!r} so it can be avoided"


def test_the_doc_states_the_rule() -> None:
    doc = (REPO_ROOT / "docs" / "rules" / "house-report-format.md").read_text(encoding="utf-8")
    assert "## 15. No machine traces" in doc
    section = doc.split("## 15. No machine traces", 1)[1]
    assert "audit_plumbing" in section and "audit_printed_html" in section


def test_the_live_payload_prints_no_machine_trace() -> None:
    """The gate on the real document. Skips when the ticker's data lane is not present."""
    if not (REPO_ROOT / "data" / "assumptions" / "AMMN.json").exists():
        pytest.skip("AMMN data lane not present")
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    hits = audit_plumbing(payload)
    assert hits == [], "the shipped payload prints machine traces:\n" + "\n".join(hits[:10])
