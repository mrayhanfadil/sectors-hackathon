"""Rendered-output hygiene: catch literal escape sequences that leak into the page as visible text.

A stray \\n in a template prints the two characters backslash-n into the PDF. Syntax checks pass, the
deployment succeeds, and the defect only shows up when a human reads the footer of page 11 — so it gets a
test instead of a habit of looking.
"""
from __future__ import annotations

import re

import pytest

from server.routers.pdf import render_html_for_ticker


@pytest.fixture(scope="module")
def html():
    return render_html_for_ticker("AMMN", None)[1]


def test_no_literal_escape_sequences_in_rendered_text(html):
    body = html.split("<script", 1)[0]
    for escape in ("\\n", "\\t", "\\r\\n"):
        leaked = [m.start() for m in re.finditer(r">[^<]*" + re.escape(escape) + r"[^<]*<", body)]
        assert not leaked, (f"a literal {escape!r} reaches the page as visible text at "
                            f"{len(leaked)} place(s)")


def test_templates_do_not_carry_the_escape_in_markup():
    """The bytes that cause it: an escaped newline written inside HTML rather than in Python."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "templates"
    offenders = []
    for f in root.glob("*.html"):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("{#") or stripped.startswith("//"):
                continue
            if "\\n</div>" in stripped or "\\n<" in stripped or "\\t<" in stripped:
                offenders.append(f"{f.name}:{i}")
    assert not offenders, f"templates carry a literal escape in markup: {offenders}"
