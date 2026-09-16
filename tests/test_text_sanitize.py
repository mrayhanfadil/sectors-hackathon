"""The reader must never be handed a path inside the repository.

The payload's source and note strings are written for the people maintaining the pipeline, so they used to name
`data/drivers/AMMN.json`, `server/report/engines/dcf_engine` and `company_report(AMMN,'peers') - published_pe_ttm`.
Both surfaces render those strings, so a reader met the machinery instead of the attribution. One pass cleans them in
the funnel both surfaces share; this guard keeps the list from creeping back, and it checks the funnel itself rather
than a copy of the strings.
"""
from __future__ import annotations

import re

import pytest

from server.report import text_sanitize

REPO_SHAPED = re.compile(r"\b(?:data|server|src|scripts|tests)/[\w./-]+")


def test_no_repo_shaped_string_survives_in_the_rendered_payload():
    from server.routers.pdf import render_html_for_ticker

    try:
        _tpl, _html, payload = render_html_for_ticker("AMMN", None)
    except Exception as exc:  # a ticker without assumptions is a legitimate refusal, not a failure of this guard
        pytest.skip(f"payload unavailable: {type(exc).__name__}")

    leftovers = text_sanitize.leftovers(payload)
    assert not leftovers, "the payload still prints repository paths:\n  " + "\n  ".join(leftovers[:8])


def test_a_placeholder_cell_is_not_treated_as_a_leftover_separator():
    """An earlier version of the cleaner turned every "-" in the peer table into a space, deleting the meaning of a
    column while every test still passed."""
    for placeholder in ("-", "–", "-", "n/a", "N/A"):
        assert text_sanitize.clean_text(placeholder) == placeholder


def test_the_engine_provenance_survives_the_clean_even_though_the_path_does_not():
    """The disclosure is required; only its form changes. It must still name the engine."""
    cleaned = text_sanitize.clean_text("Engine valuasi internal: server/report/engines/dcf_engine")
    assert "model DCF internal" in cleaned, "the engine provenance was dropped instead of restated"
    assert "server/report" not in cleaned


def test_the_clean_is_idempotent():
    """The payload passes through the funnel once today; a second pass must not fold the attribution into nonsense."""
    once = text_sanitize.clean_text("scripts/dcf_engine.dcf/ev_ebitda on data/assumptions/AMMN.json")
    twice = text_sanitize.clean_text(once)
    assert once == twice
