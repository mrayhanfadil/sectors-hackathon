"""The deck is source-independent: no third-party research house is named on a printed page.

The owner's rule: the report cites its licensed dataset (Sectors), the issuer's own filings, public news and
the team's own estimates. The calibration trail for the forecast inputs stays in the repo
(docs/ammn-slides/forecast-inputs-provenance.md) and never reaches a page.
"""
from __future__ import annotations

import copy
import re

import pymupdf
import pytest

from server.report.forecast_path import display_attribution
from server.report.house_rules import audit_source_independence
from server.routers.pdf import render_html_for_ticker

NAMES = ["BRIDS", "BRI Danareksa", "Danareksa Sekuritas", "Bahana Sekuritas", "Mandiri Sekuritas",
         "BCA Sekuritas", "BNI Sekuritas", "Trimegah Sekuritas", "Samuel Sekuritas", "Maybank Sekuritas",
         "Mirae Asset", "Ciptadana", "MNC Sekuritas", "Panin Sekuritas", "Phillip Sekuritas",
         "RHB Sekuritas", "CGS-CIMB", "Nomura", "Macquarie", "Morgan Stanley", "Goldman Sachs", "JPMorgan"]


@pytest.fixture(scope="module")
def payload():
    return render_html_for_ticker("AMMN", None)[2]


def test_no_research_house_is_named_in_the_rendered_deck(payload):
    """A news wire naming which broker was buying is published flow data, not a citation — so this looks for
    the attribution form ('<house> Equity Research', '<house> Sekuritas', '<house> initiation')."""
    html = render_html_for_ticker("AMMN", None)[1]
    text = html + "\n" + "\n".join(p.get_text() for p in pymupdf.open("/tmp/AMMN_slide7.pdf"))
    for name in ("BRIDS", "BRI Danareksa", "Danareksa"):
        assert name.lower() not in text.lower(), f"{name} still reaches the page"
    for name in NAMES:
        form = re.compile(re.escape(name) + r"\s*[,\-–—]?\s*(equity research|research|sekuritas|securities|"
                          r"initiation)\b", re.I)
        assert not form.search(text), f"the page cites {name}"


def test_the_printed_attribution_carries_no_house_name(payload):
    kf = payload["cover"]["slide2"]["key_financials"]
    label = str(kf.get("forecast_attribution") or "")
    assert label and "estimasi tim" in label.lower()
    for name in NAMES:
        assert name.lower() not in label.lower(), name
    note = " ".join(str(n) for n in (kf.get("notes") or [])).lower()
    assert "proyeksi" in note or "bukan realisasi" in note, \
        "the note must still say the columns are a projection, not realised figures"


def test_display_attribution_strips_a_house_name():
    assert "brids" not in display_attribution("BRIDS Equity Research — initiation 29 Jun 2026").lower()
    assert display_attribution("BRIDS Equity Research") == "estimasi tim"
    assert display_attribution(None) == "estimasi tim"


def test_gate_flags_an_injected_house_name(payload):
    assert audit_source_independence(payload) == []
    for inject in ("BRIDS Equity Research — initiation 29 Jun 2026",
                   "Maybank Sekuritas, AMMN initiation",
                   "source: Samuel Sekuritas report"):
        broken = copy.deepcopy(payload)
        broken["cover"]["slide2"]["key_financials"]["forecast_attribution"] = inject
        assert audit_source_independence(broken), f"the gate let {inject!r} through"
    # the internal trail is exempt on purpose: it is the audit trail, and no page prints it
    broken = copy.deepcopy(payload)
    broken["_trail"] = {"attribution_internal": "BRIDS Equity Research"}
    assert audit_source_independence(broken) == []


def test_internal_fields_do_not_reach_the_rendered_html(payload):
    """The trail lives on disk. If an internal field rode along in the payload it would print in the script
    blob at the bottom of the page and be readable in the browser."""
    html = render_html_for_ticker("AMMN", None)[1]
    assert "attribution_internal" not in html and "source_internal" not in html
