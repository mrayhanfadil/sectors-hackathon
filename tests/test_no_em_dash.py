"""Typographic guard: the reader never sees an em dash (house-report-format.md §12).

Why this is a separate guard rather than a line in the format test: an em dash reaches a document
from a place no source scan can see. Three writers produce it at RUN time -

  * prose an agent wrote (the LLM emits em dashes by default, in Indonesian and English alike),
  * a `note` field inside `data/assumptions/<T>.json` or `data/drivers/<T>.json`,
  * a sentence copied verbatim out of a research PDF, which carries the original publisher's
    typography.

So the rule needs four layers, and this file checks all of them:

  1. the WRITERS (static): no em dash on any hand-edited surface, in any spelling. The literal
     character is only one way it gets in - a JSON string can carry the escape "\\u2014" and a
     template can carry "&mdash;", both of which render as the same mark. Both are scanned.
  2. the FUNNEL (unit): `server/report/text_sanitize.py` rewrites every em dash on the way out,
     which is what makes the rule hold for the run-time writers above;
  3. the SERVED PAYLOAD: the front end renders `/api/report/{ticker}`, assembled outside the PDF
     path, so it gets its own check;
  4. the PAGE and the BUNDLE (artifact): `scripts/verify_house_format.py` fails the shipped PDF,
     and the built front-end bundle is scanned when `src/fe/dist` exists.

The en dash (U+2013) is deliberately NOT part of this rule: the house header
("Equity Research \u2013 Company Update") and the numeric range labels are printed with it.

A file that must contain the character to do its job (the normaliser, the checker, the guards,
the rule doc's counter-example) is listed in EXEMPT with the reason. Nothing else is.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

EM_DASH = "\u2014"
HORIZONTAL_BAR = "\u2015"
EN_DASH = "\u2013"

# Every way the mark can be written down. The literal is the common case; the escape is how a
# JSON payload carries it (`data/assumptions/*.json` did, 50 times, while the file looked clean);
# the entity is how it travels through HTML.
PATTERNS = {
    "literal": re.compile("[\u2014\u2015]"),
    "escaped": re.compile(r"\\u201[45]|\\x2014|\\2014"),
    "entity": re.compile(r"&mdash;|&horbar;|&#8212;|&#x2014;", re.I),
}
SUFFIXES = {".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".md",
            ".toml", ".cfg", ".ini", ".sh", ".j2"}

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".worktrees", "output", "out",
             ".pytest_cache", ".ruff_cache", ".hermes", "dist", "dist-smoke", "dist-verify"}

# Files that carry the character ON PURPOSE. Each entry needs a reason.
EXEMPT = {
    "server/report/text_sanitize.py": "defines the normalisation it enforces",
    "scripts/verify_house_format.py": "counts the character on the printed page",
    "tests/test_no_em_dash.py": "this guard: fixtures and expectations",
    "tests/test_regex_literals_compile.py": "docstring shows the character class a sweep broke",
    "docs/rules/house-report-format.md": "prints the wrong form as the rule's counter-example",
}


def _files():
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if str(rel) in EXEMPT:
            continue
        yield path


# ----------------------------------------------------------------- 1. the writers (static)


def test_no_em_dash_on_any_hand_edited_surface() -> None:
    """A hit here is a string to fix, not something the funnel should absorb."""
    hits: list[str] = []
    for path in _files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                snippet = text.splitlines()[line - 1].strip()[:90]
                hits.append(f"{path.relative_to(REPO_ROOT)}:{line} ({kind}): {snippet}")
    assert not hits, (
        "em dash found - §12 forbids it and the funnel should not have to clean up text we wrote "
        "ourselves. Use the house hyphen separator instead ('A - B'), or, if the file must contain "
        "the character to do its job, add it to EXEMPT in this file with a reason:\n  "
        + "\n  ".join(hits[:20])
    )


def test_exemptions_are_real_files_with_reasons() -> None:
    for rel, reason in EXEMPT.items():
        assert (REPO_ROOT / rel).exists(), f"exemption points at a file that does not exist: {rel}"
        assert len(reason) > 15, f"exemption for {rel} needs a reason a reviewer can weigh"


def test_every_agent_is_told_the_typography_rule() -> None:
    """Three layers, because "the rule exists" is not "the agent received it".

    1. the constants: every non-retired `*_instruction` in the module carries the marker;
    2. the composition: the runtime graph is BUILT and each agent's instruction is read as the
       framework will send it - a provider that drops the block, or a new agent added without it,
       fails here rather than in a shipped deck;
    3. the legacy builder in agents/collector.py, which assembles its own prompt.
    """
    import os

    from agents.adk.agents import instructions

    # 1. constants (composition-aware: exec the module, then test the resulting strings)
    ns: dict = {}
    exec(  # noqa: S102 - the module under test, no side effects at import
        compile(open(instructions.__file__, encoding="utf-8").read(), instructions.__file__, "exec"),
        ns,
    )
    missing = []
    for name, value in ns.items():
        if not name.endswith("_instruction") or not isinstance(value, str) or not value.strip():
            continue
        if "RETIRED" in value[:200]:
            continue
        if "U+2014" not in value:
            missing.append(name)
    assert not missing, (
        "these agent instructions do not carry the typography rule (§12): "
        f"{missing}. Attach `+ TYPOGRAPHY_RULE` (agents/adk/agents/instructions.py) to each; the "
        "block is deliberately separate from HOUSE_FORMAT_RULE because the data-only agents must "
        "not receive the exhibit/label rules while still being told the typography rule."
    )

    # 2. the runtime graph
    os.environ.setdefault("GOOGLE_API_KEY", "structure-only")
    os.environ.setdefault("DEEPSEEK_API_KEY", "structure-only")
    from agents.adk.app import build_graph

    root = build_graph(ticker="AMMN")
    carried: dict[str, str] = {}

    def walk(agent) -> None:
        instruction = str(getattr(agent, "instruction", "") or "")
        if instruction:
            carried[str(getattr(agent, "name", "?"))] = instruction
        for sub in getattr(agent, "sub_agents", []) or []:
            walk(sub)

    walk(root)

    expected = {"collector", "news_harvester", "modeler", "industry", "analyst", "risk", "kpi",
                "writer", "visualizer", "sotp", "adversarial", "critic"}
    assert expected <= set(carried), (
        "the ADK graph no longer builds every agent this rule is verified against: "
        f"missing {sorted(expected - set(carried))}"
    )
    without = sorted(name for name, text in carried.items() if "U+2014" not in text)
    assert not without, (
        "these agents are built WITHOUT the typography rule, so the model can write an em dash "
        f"into their output: {without}"
    )

    # 3. the legacy collector builder assembles its own prompt
    from agents.collector import _typography_rule

    assert "U+2014" in _typography_rule()


def test_house_format_rule_still_carries_the_typography_rule() -> None:
    """The content agents get it via HOUSE_FORMAT_RULE; the block must stay attached there."""
    from agents.adk.agents import instructions

    assert "U+2014" in instructions.HOUSE_FORMAT_RULE
    src = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert re.search(r'HOUSE_FORMAT_RULE = """(?:.|\n)*?"""\s*\+\s*TYPOGRAPHY_RULE', src), (
        "HOUSE_FORMAT_RULE no longer composes TYPOGRAPHY_RULE, so the content agents would only "
        "carry the typography text by accident"
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


# ----------------------------------------------------------------- 3. the served payload


def test_front_end_payload_endpoint_carries_no_em_dash() -> None:
    """The website path, checked on the payload it actually renders.

    Runs keyless under the suite conftest (Sectors scrubbed, isolated SQLite cache), so this costs
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


# ----------------------------------------------------------------- 4. the artifacts


def test_built_front_end_bundle_carries_no_em_dash() -> None:
    """The deployed bundle is a build artefact: it only follows the source if it is REBUILT.

    Skipped when `src/fe/dist` is absent (a fresh clone has no build). When it exists it is the
    thing Cloudflare Pages serves, so it is checked directly - a stale bundle is how a sweep looks
    done while the live site still prints the mark.
    """
    dist = REPO_ROOT / "src" / "fe" / "dist"
    if not dist.exists():
        pytest.skip("no built bundle in src/fe/dist - nothing to check (run `npm run build`)")

    hits: list[str] = []
    for path in sorted(dist.rglob("*")):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for kind, pattern in PATTERNS.items():
            n = len(pattern.findall(text))
            if n:
                hits.append(f"{path.relative_to(REPO_ROOT)} ({kind}): {n}")
    assert not hits, (
        "the built bundle still carries an em dash, so the deployed site prints what the source no "
        "longer does - rebuild (`cd src/fe && npm run build`):\n  " + "\n  ".join(hits)
    )


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
