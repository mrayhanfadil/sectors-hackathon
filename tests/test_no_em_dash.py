"""Typographic guard: the reader never sees an em dash (house-report-format.md §12).

Why this is a separate guard rather than a line in the format test: an em dash reaches a
document from a place no source scan can see. Three writers produce it at RUN time -

  * prose an agent wrote (the LLM emits em dashes by default, in Indonesian and English alike),
  * a `note` field inside `data/assumptions/<T>.json` or `data/drivers/<T>.json`,
  * a sentence copied verbatim out of a research PDF, which carries the original publisher's
    typography.

So the rule needs three layers, and this file checks all three:

  1. the WRITERS (static): no em dash in the code, templates, agent instructions, data files or
     the front end - the surfaces a human edits, where a hit is a fix, not a normalisation;
  2. the FUNNEL (unit): `server/report/text_sanitize.py` rewrites every em dash on the way out,
     which is what makes the rule hold for the run-time writers above;
  3. the PAGE (artifact): `scripts/verify_house_format.py` fails the shipped PDF if one is
     printed - enforced by `test_house_format_adoption.py::test_shipped_pdf_passes_the_artifact_check`.

The en dash (U+2013) is deliberately NOT part of this rule: the house header
("Equity Research \u2013 Company Update") and the numeric range labels are printed with it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

EM_DASH = "\u2014"
HORIZONTAL_BAR = "\u2015"
EN_DASH = "\u2013"

# The surfaces that ship, plus the code that writes them. Root-level markdown notes and
# `docs/` + `references/` are internal: the research notes there QUOTE outside documents
# verbatim (publisher typography included) and are not rendered, so they are out of scope by
# design, not by oversight.
SHIPPED_PATHS = (
    "agents",
    "server",
    "scripts",
    "templates",
    "tests",
    "data",
    "docker",
    "src/fe/src",
    "src/fe/public",
    "src/fe/index.html",
    "docker-compose.yml",
    "Makefile",
)
SHIPPED_SUFFIXES = {".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".md"}
SKIP_DIRS = {"node_modules", "dist", "dist-smoke", "dist-verify", "__pycache__", ".venv", ".wrangler"}


def _shipped_files():
    for rel in SHIPPED_PATHS:
        target = REPO_ROOT / rel
        if target.is_file():
            yield target
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix in SHIPPED_SUFFIXES:
                yield path


# ----------------------------------------------------------------- 1. the writers (static)


def test_no_em_dash_in_shipped_sources() -> None:
    """A hit here is a hand-written string to fix, not something the funnel should absorb."""
    hits: list[str] = []
    for path in _shipped_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if EM_DASH in line or HORIZONTAL_BAR in line:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()[:100]}")
    assert not hits, (
        "em dash found in a shipped surface - §12 forbids it and the funnel should not have to "
        "clean up text we wrote ourselves. Use the house hyphen separator instead "
        "('A - B'):\n  " + "\n  ".join(hits[:20])
    )


def test_agent_instructions_state_the_typography_rule() -> None:
    """The writers of run-time prose are the agents, so the rule has to be in their prompt."""
    from agents.adk.agents import instructions

    rule = instructions.HOUSE_FORMAT_RULE
    assert "U+2014" in rule, (
        "HOUSE_FORMAT_RULE does not tell the agents to avoid an em dash; the LLM emits them by "
        "default, so the prompt is the only place that stops it at the source"
    )
    assert "-" in rule, "the rule must name the replacement separator, not only the ban"
    # And it must actually travel: every prompt that can put text into the document.
    src = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert src.count("+ HOUSE_FORMAT_RULE") >= 8, (
        "the typography rule rides on HOUSE_FORMAT_RULE, so the number of prompts carrying it "
        "cannot drop"
    )


# ----------------------------------------------------------------- 2. the funnel (unit)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Opsi A \u2014 DCF FCFF", "Opsi A - DCF FCFF"),           # parenthetical
        ("FY24A\u2014FY25A aktual", "FY24A-FY25A aktual"),          # range, no spaces
        ("\u2014", "-"),                                            # placeholder cell
        ("Net profit \u2014 turun", "Net profit - turun"),
        ("a \u2015 b", "a - b"),                                     # horizontal bar
        ("A - B", "A - B"),                                          # already house style
        ("Equity Research \u2013 Company Update", "Equity Research \u2013 Company Update"),
        ("Rp 5.000 \u2013 Rp 7.000", "Rp 5.000 \u2013 Rp 7.000"),   # en dash: a mandated range
        ("FCF \u2212Rp 17,74 tn", "FCF \u2212Rp 17,74 tn"),          # minus sign untouched
    ],
)
def test_normalize_dashes(raw: str, expected: str) -> None:
    from server.report.text_sanitize import normalize_dashes

    assert normalize_dashes(raw) == expected
    assert normalize_dashes(normalize_dashes(raw)) == expected, "normalisation must be idempotent"


def test_clean_text_never_returns_an_em_dash() -> None:
    from server.report.text_sanitize import clean_text

    for raw in (
        "Metode dipilih manual: Opsi A \u2014 DCF FCFF.",
        "\u2014",
        "post-build normalisation \u2014 1,424 in FY2025A",
        "RESEARCH \u2014 Sectors Hackathon 2026",
    ):
        out = clean_text(raw)
        assert EM_DASH not in out and HORIZONTAL_BAR not in out, f"{raw!r} -> {out!r}"


def test_clean_payload_walks_every_string() -> None:
    """The funnel is applied to the whole payload, so nesting cannot hide a string."""
    from server.report.text_sanitize import clean, dash_hits

    payload: dict = {
        "meta": {"sector": "Financials \u2014 Perbankan", "prepared_by": "RESEARCH \u2014 Sectors"},
        "cover": {"summary": "Update liputan \u2014 target Rp4.105", "takeaways": ["P/BV 1,60x \u2014 konsisten"]},
        "gate_verdict": {"reasons": ["Finite reserves \u2014 perpetual-growth DCF structurally wrong"]},
        "numbers": [1, 2.5, None, True],
        "table": {"rows": [["Ticker", "P/E"], ["BBCA", 4.2]]},
    }
    assert dash_hits(payload), "the fixture must actually contain em dashes"

    out = clean(payload)
    assert dash_hits(out) == [], f"an em dash survived the funnel: {dash_hits(out)}"
    # …and only strings changed: structure, keys and numbers are handed through untouched.
    assert out["numbers"] == payload["numbers"]
    assert out["table"] == payload["table"]
    assert out["cover"]["takeaways"][0].endswith("konsisten")


def test_funnel_is_applied_on_both_served_paths() -> None:
    """PDF and front end must share one funnel, or the two surfaces disagree (§12)."""
    pdf_src = (REPO_ROOT / "server" / "routers" / "pdf.py").read_text(encoding="utf-8")
    api_src = (REPO_ROOT / "server" / "routers" / "endpoints.py").read_text(encoding="utf-8")
    assert "text_sanitize.clean" in pdf_src, "the PDF render path lost the funnel"
    assert "text_sanitize import clean" in api_src, (
        "the front-end report payload (/api/report/{ticker}) is assembled separately from the PDF "
        "payload; without the funnel here the web page can print an em dash the PDF does not"
    )


def test_front_end_payload_endpoint_carries_no_em_dash() -> None:
    """The website path, checked on the payload it actually renders.

    `/api/report/{ticker}` is not the PDF payload: it is assembled in
    `server/routers/endpoints.py`, so it needs its own guard rather than the PDF one. Runs
    keyless under the suite conftest (Sectors scrubbed, isolated SQLite cache), so this costs
    nothing and cannot warm the production cache.
    """
    from fastapi.testclient import TestClient

    if not (REPO_ROOT / "data" / "assumptions" / "AMMN.json").exists():
        pytest.skip("no verified assumptions for AMMN - the endpoint would answer 422 by design")

    from server.main import app
    from server.report.text_sanitize import dash_hits

    res = TestClient(app).get("/api/report/AMMN")
    assert res.status_code == 200, f"/api/report/AMMN answered {res.status_code}: {res.text[:200]}"

    body = res.json()
    assert body.get("fair_value") is not None, (
        "the payload came back without a valuation - a green result here would be vacuous"
    )
    hits = dash_hits(body)
    assert hits == [], (
        "the front-end payload still carries an em dash, so the web page prints what the PDF no "
        "longer does:\n  " + "\n  ".join(hits[:5])
    )


# ----------------------------------------------------------------- 3. the page (artifact)


def test_artifact_check_fails_a_pdf_that_prints_one(tmp_path: Path) -> None:
    """The verifier that reads PHYSICAL pages must fail when one is printed.

    Built on a synthetic page instead of the shipped report: the shipped check needs Playwright
    and a verified assumptions file, and this guard has to fire in any environment.
    """
    import sys

    pymupdf = pytest.importorskip("pymupdf")
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import verify_house_format

    doc = pymupdf.open()
    page = doc.new_page()
    # insert_htmlbox, not insert_text: the base-14 Helvetica writer silently DROPS the em dash
    # (measured: "Opsi A - DCF"), which would make this test pass on a PDF that never had one.
    page.insert_htmlbox(pymupdf.Rect(72, 72, 500, 200), "<p>Opsi A \u2014 DCF FCFF</p>")
    out = tmp_path / "em.pdf"
    doc.save(str(out))

    result = verify_house_format.check(out)
    assert any("rule 12" in f for f in result["fails"]), (
        "verify_house_format passed a PDF that prints an em dash - the artifact layer is the only "
        f"one that sees the page, so it has to carry §12. fails={result['fails']}"
    )
    assert result["info"]["em_dashes"] == 1
