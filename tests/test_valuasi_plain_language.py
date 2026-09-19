"""Paragraph 3 (Valuasi) in plain Indonesian, with the mandate's markers kept verbatim.

The owner asked for the same treatment P1/P2 got ("bungkus juga, biar enak bacanya") while the
four-element mandate that `audit_valuasi` enforces must survive untouched. Two things are pinned
here: the mandate tokens still print, and P3 is now inside the plain-language scan - with a
carve-out narrow enough that it cannot hide real jargon.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.report.house_rules import (VALUASI_MANDATE_TOKENS, audit_house_rules,
                                       audit_plain_language, audit_valuasi)

#: Jargon that used to print in P3, and the denylist token each one trips.
OLD_P3_JARGON = (
    ("mid-cycle", "mid-cycle"),
    ("print 2026", "print 20"),
    ("insider selling", "insider"),
    # the scan reports the first denylist token that hits, and "multiple" precedes
    # "exit multiple" in the tuple - either name is the same defect
    ("exit multiple", "multiple"),
    ("re-rating", "re-rating"),
    ("downside", "downside"),
)


@pytest.fixture(scope="module")
def payload() -> dict:
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


def test_p3_keeps_the_four_mandated_markers(payload) -> None:
    body = payload["cover"]["slide2"]["valuasi"]["body"]
    assert audit_valuasi(body) == []
    for token in ("menggunakan", "TP Rp", "CAGR", "FY26F-FY28F", "dibandingkan",
                  "rata-rata historis", "Risiko terhadap pandangan ini"):
        assert token in body, f"the plain rewrite dropped the mandated marker {token!r}"


def test_p3_is_now_inside_the_plain_language_scan(payload) -> None:
    assert audit_plain_language(payload) == [], "the shipped P3 must be clean"


@pytest.mark.parametrize("jargon,expected", OLD_P3_JARGON)
def test_p3_jargon_would_be_caught_again(payload, jargon, expected) -> None:
    """Mutation test: every phrasing the rewrite removed trips the scan if it comes back."""
    bad = copy.deepcopy(payload)
    valuasi = bad["cover"]["slide2"]["valuasi"]
    valuasi["body"] = f"{valuasi['body']} Catatan: {jargon}."

    hits = audit_plain_language(bad)
    assert any("P3 body" in h and expected in h for h in hits), (jargon, hits)


def test_the_carve_out_covers_only_the_mandated_markers(payload) -> None:
    """The carve-out is by name, so a mandated marker must not mask real jargon next to it."""
    bad = copy.deepcopy(payload)
    valuasi = bad["cover"]["slide2"]["valuasi"]
    # "CAGR" is carved out; the jargon in the same sentence is not.
    valuasi["body"] = valuasi["body"].replace(
        "CAGR EBITDA FY26F-FY28F", "CAGR EBITDA FY26F-FY28F dengan exit multiple")
    hits = audit_plain_language(bad)
    assert any("multiple" in h for h in hits), hits

    assert "CAGR" in VALUASI_MANDATE_TOKENS and "FY26F-FY28F" in VALUASI_MANDATE_TOKENS
    assert len(VALUASI_MANDATE_TOKENS) == 3, "the carve-out grew - justify it before widening"


def test_p3_shares_print_as_lembar_not_sh(payload) -> None:
    body = payload["cover"]["slide2"]["valuasi"]["body"]
    assert "juta lembar" in body
    assert " sh " not in body and " sh," not in body


def test_live_p3_still_passes_the_whole_house_gate(payload) -> None:
    assert audit_house_rules(payload)["ok"] is True
