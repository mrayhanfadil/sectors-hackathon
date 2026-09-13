"""Adoption guards for the house report format.

This file proves the house format is adopted end to end by the served render path:

  - `docs/rules/house-report-format.md` exists and is canonical;
  - the data contract the agents write against cannot contradict it;
  - every ADK agent that can put an object into the report carries the rule;
  - the Critic gate rejects violations instead of inventing exhibit numbers;
  - the production render path maps to the convention templates;
  - the non-compliant legacy renderer cannot silently emit a report PDF;
  - a document built through the production loader comes out compliant.

Rule set (Fadiil, 11 Sep 2026): every visual/tabular object carries
"Exhibit N. <descriptive>" above it and the constant
"Source: Company, Team Estimates" below it; numbering is a global counter that runs
from the first page to the last and never resets; every page carries the house
header (title + Day, DD Month YYYY date + Sectors.app logo + #067647 divider) and
footer (sectors.app / disclosure pointer + page number).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RULE_DOC = REPO_ROOT / "docs" / "rules" / "house-report-format.md"
DATA_CONTRACT = REPO_ROOT / "templates" / "DATA_CONTRACT.md"
TEMPLATES_DIR = REPO_ROOT / "templates"
MACROS = TEMPLATES_DIR / "macros.html"

# Agents whose output can reach the document as an exhibit, table or chart.
AGENTS_CARRYING_THE_RULE = [
    "analyst", "industry", "kpi", "writer", "visualizer", "sotp", "critic",
    # adversarial cites exhibits in its defense and modeler's schedules become
    # exhibits, so both need the numbering rule too.
    "adversarial", "modeler",
]

CONSTANT_SOURCE = "Source: Company, Team Estimates"


# --------------------------------------------------------------- canonical spec


def test_rule_doc_exists_and_is_canonical() -> None:
    assert RULE_DOC.exists(), (
        "docs/rules/house-report-format.md is missing — the rules then live only in "
        "chat and in code, with nothing for a contributor or an agent to read"
    )
    txt = RULE_DOC.read_text(encoding="utf-8")
    for required in (
        CONSTANT_SOURCE,                      # constant source line
        "tanpa terkecuali",                   # no exceptions
        "Day, DD Month YYYY",                 # date format
        "See important disclosure at the back of this report",
        "#067647",                            # divider colour
        "global counter",                     # numbering rule
    ):
        assert required in txt, f"rule doc does not state: {required!r}"


# ------------------------------------------------------------- data contract


def test_data_contract_forbids_pre_numbered_exhibits() -> None:
    """A payload carrying `id: "Exhibit 1"` is a local variable pretending to be the
    global counter — numbering desyncs the moment a chart moves."""
    txt = DATA_CONTRACT.read_text(encoding="utf-8")
    assert not re.search(r'"id"\s*:\s*"Exhibit\s*\d', txt), (
        "DATA_CONTRACT.md still shows a pre-numbered exhibit id in its schema example"
    )
    assert CONSTANT_SOURCE in txt, (
        "DATA_CONTRACT.md does not tell agents what the printed source line is"
    )
    assert "global counter" in txt, "DATA_CONTRACT.md does not state the numbering rule"
    # the validation rule must ban the id, not just omit it from the example
    assert "must NOT carry a" in txt and "pre-numbered" in txt


def test_data_contract_source_field_is_audit_not_printed() -> None:
    txt = DATA_CONTRACT.read_text(encoding="utf-8")
    assert "internal provenance" in txt
    assert "never printed" in txt or "not printed" in txt


# ----------------------------------------------------------- agent instructions


def test_house_format_rule_is_defined_once_and_reused() -> None:
    src = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert "HOUSE_FORMAT_RULE = " in src, "the rule block must exist as a reusable constant"
    assert "docs/rules/house-report-format.md" in src, "instructions do not cite the rule doc"
    assert src.count("+ HOUSE_FORMAT_RULE") == len(AGENTS_CARRYING_THE_RULE), (
        "every content-producing agent must append the rule block exactly once"
    )


@pytest.mark.parametrize("agent", AGENTS_CARRYING_THE_RULE)
def test_each_agent_instruction_carries_the_house_format_rule(agent: str) -> None:
    instructions = _instructions_module()
    txt = getattr(instructions, f"{agent}_instruction")
    assert "HOUSE REPORT FORMAT" in txt, f"{agent} instruction does not carry the house format rule"
    for required in (
        "global counter",          # numbering
        "descriptive",             # label quality
        CONSTANT_SOURCE,           # constant printed source line
        "RENDERER-side",           # header/footer/logo are not the agent's job
    ):
        assert required in txt, f"{agent} instruction is missing: {required!r}"


def test_writer_source_instruction_is_reconciled_with_the_house_line() -> None:
    """The writer used to be told to print `Source: <outlet>, <date>`. That is the
    audit field, not the printed line — leaving both in place would put two
    contradictory instructions in the same prompt."""
    txt = _instructions_module().writer_instruction
    assert "Quote provenance per exhibit" in txt, "reconciled wording missing"
    assert "AUDIT field, not the printed line" in txt
    assert 'Quote source per exhibit as "Source: < outlet/domain >' not in txt


def test_agents_are_not_told_to_emit_layout() -> None:
    """Header, footer, page numbers and labels belong to the renderer."""
    for agent in AGENTS_CARRYING_THE_RULE:
        txt = getattr(_instructions_module(), f"{agent}_instruction")
        assert "Never emit them yourself" in txt or "do not emit them" in txt.lower(), (
            f"{agent} is not told that page furniture is renderer-side"
        )


def _instructions_module():
    sys.path.insert(0, str(REPO_ROOT))
    from agents.adk.agents import instructions

    return instructions


# ------------------------------------------------------------------ critic gate


def test_critic_rejects_pre_numbered_ids_and_generic_titles() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from agents.critic import audit_report_payload

    verdict = audit_report_payload({
        "exhibits": [
            {"id": "Exhibit 1", "title": "Chart", "source": "SKK Migas"},
            {"title": "Revenue and Revenue Growth (2024A-2028F)", "source": "IDX filings"},
        ]
    })
    joined = " ".join(verdict["reasons"])
    assert "pre-numbered id" in joined, "Critic does not reject a pre-numbered exhibit id"
    assert "generic title" in joined, "Critic does not reject a generic exhibit title"
    assert verdict["verdict"] == "REJECT"


def test_critic_does_not_synthesise_exhibit_numbers() -> None:
    """Inventing 'Exhibit N' in a gate message reintroduces the manual numbering the
    rule bans and hands the reader a number that will not match the PDF."""
    src = (REPO_ROOT / "agents" / "critic.py").read_text(encoding="utf-8")
    assert 'f"Exhibit {i}"' not in src and "f'Exhibit {i}'" not in src, (
        "critic.py still synthesises Exhibit N labels in its diagnostics"
    )


def test_critic_accepts_a_compliant_payload() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from agents.critic import audit_report_payload

    verdict = audit_report_payload({
        "exhibits": [
            {"title": "Revenue and Revenue Growth (2024A-2028F)", "source": "IDX filings url+date"},
        ]
    })
    joined = " ".join(verdict["reasons"])
    assert "pre-numbered id" not in joined
    assert "generic title" not in joined


# ----------------------------------------------------------------- render path


def test_production_renderer_maps_every_archetype_to_a_convention_template() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from server.routers.pdf import TEMPLATE_FILES

    assert set(TEMPLATE_FILES) >= {"single", "sotp", "infra", "strategy"}
    for archetype, filename in TEMPLATE_FILES.items():
        template = TEMPLATES_DIR / filename
        assert template.exists(), f"archetype {archetype!r} maps to a missing {filename!r}"
        txt = template.read_text(encoding="utf-8")
        assert "exhibit-id" in txt or "exhibit" in txt, (
            f"{filename} has no house-formatted exhibits"
        )


def test_challenge_engine_does_not_hand_number_exhibits() -> None:
    """`scripts/adversarial.py` is reachable from the /challenge endpoint, so its
    exhibit references are user-facing. A literal number there drifts from the PDF."""
    src = (REPO_ROOT / "scripts" / "adversarial.py").read_text(encoding="utf-8")
    # Match any string literal that OPENS with an exhibit number, followed by whatever
    # the old code appended (": Valuation Methodology", "1-5", ...). Anchoring on the
    # closing quote would miss the real shape `"Exhibit 4: <title>"` entirely.
    offenders = re.findall(r'"[^"]*?Exhibit\s+\d[^"]*"', src)
    assert not offenders, (
        f"challenge engine still hand-numbers exhibits: {offenders} — cite them by title"
    )


def test_front_end_never_hand_numbers_exhibits() -> None:
    """Same rule, one surface further out: the FE is user-facing too.

    The challenge form falls back to a hard-coded reference when the backend does not
    return one. A literal `Exhibit 3.1` there keeps pointing at a chart that has moved
    (or no longer exists) the moment the report is revised — the PDF counter is owned by
    the renderer and the FE cannot see it. Cite the exhibit by title instead.
    """
    fe_src = REPO_ROOT / "src" / "fe" / "src"
    if not fe_src.exists():  # FE not checked out (backend-only test run)
        pytest.skip("src/fe not present")
    offenders: list[str] = []
    for path in list(fe_src.rglob("*.ts")) + list(fe_src.rglob("*.tsx")):
        if "node_modules" in path.parts:
            continue
        src = path.read_text(encoding="utf-8")
        for m in re.finditer(r"""["'`][^"'`]*?Exhibit\s+\d[^"'`]*["'`]""", src):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {m.group(0)}")
    assert not offenders, (
        "the front end hand-numbers exhibits (drifts from the PDF counter) — cite by title:\n  "
        + "\n  ".join(offenders)
    )


def test_any_agent_that_mentions_exhibits_carries_the_rule() -> None:
    """Self-maintaining invariant. The rule is bound to WHAT an agent produces, not to a
    hard-coded roster: the moment someone adds an agent that talks about exhibits, this
    fails until that agent is given the rule. Data-producing agents (collector, news
    harvester, social sentiment, risk) mention exhibits zero times and are correctly
    absent from the list — they hand payloads to the agents above, they do not label them."""
    instructions = _instructions_module()
    offenders = []
    for name in dir(instructions):
        if not name.endswith("_instruction"):
            continue
        txt = getattr(instructions, name)
        if not isinstance(txt, str):
            continue
        if re.search(r"\bexhibit", txt, re.I) and "HOUSE REPORT FORMAT" not in txt:
            offenders.append(name)
    assert not offenders, (
        "these agents talk about exhibits but do not carry the house format rule: "
        f"{offenders}"
    )


def test_agents_that_do_not_produce_exhibits_are_not_given_the_rule() -> None:
    """The complement: the rule must not be sprinkled where it has no referent, or it
    stops meaning anything."""
    instructions = _instructions_module()
    data_only = ["collector", "news_harvester", "social_sentiment", "risk"]
    for name in data_only:
        txt = getattr(instructions, f"{name}_instruction")
        assert "HOUSE REPORT FORMAT" not in txt, (
            f"{name} produces data for other agents, not exhibits — it should not carry "
            "the house format rule"
        )
        assert not re.search(r"\bexhibit", txt, re.I)


# ------------------------------------------------- theme constants vs the rule doc

HOUSE_HEADER = "Equity Research \u2013 Company Update"
HOUSE_FOOTER_LEFT = "sectors.app"
HOUSE_FOOTER_RIGHT = "See important disclosure at the back of this report"
HOUSE_DIVIDER = "#067647"


_TEMPLATE_CONSTANT_KEYS = {
    "header_title": "HEADER_TITLE",
    "footer_left": "FOOTER_LEFT",
    "footer_right": "FOOTER_RIGHT",
    "source_line": "SOURCE_LINE",
    "divider_color": "DIVIDER_COLOR",
}


def _theme_constants() -> dict:
    """Read the fixed strings out of the template that renders them, so the assertion is
    against what actually ships rather than against a Python copy of it."""
    txt = MACROS.read_text(encoding="utf-8")
    out = {}
    for key in _TEMPLATE_CONSTANT_KEYS:
        m = re.search(r'\{\{ HOUSE\.' + key + r' \| default\("([^"]*)"\)', txt)
        assert m, f"macros.html no longer declares a default for HOUSE.{key}"
        out[key] = m.group(1)
    return out


def test_theme_furniture_matches_the_rule_doc() -> None:
    c = _theme_constants()
    assert c["header_title"] == HOUSE_HEADER, c["header_title"]
    assert c["footer_left"] == HOUSE_FOOTER_LEFT
    assert c["footer_right"] == HOUSE_FOOTER_RIGHT
    assert c["divider_color"] == HOUSE_DIVIDER, c["divider_color"]
    assert c["source_line"] == "Company, Team Estimates"

    # the derived printed source line is exactly what the rule doc mandates
    assert f"Source: {c['source_line']}" == CONSTANT_SOURCE

    doc = RULE_DOC.read_text(encoding="utf-8")
    for value in (HOUSE_HEADER, HOUSE_FOOTER_LEFT, HOUSE_FOOTER_RIGHT, HOUSE_DIVIDER):
        assert value in doc, f"rule doc does not state {value!r}"
    assert CONSTANT_SOURCE in doc


def test_theme_carries_the_brand_mark() -> None:
    """The header right carries the Sectors.app mark: the template must reference it and the
    asset it points at must exist."""
    from server.report import house_format

    assert "HOUSE.logo" in MACROS.read_text(encoding="utf-8"), "macros.html no longer renders the mark"
    assert house_format.LOGO_PATH.exists(), f"brand mark missing: {house_format.LOGO_PATH}"


_JINJA_PAYLOAD = {
    "meta": {
        "template": "single", "ticker": "TEST", "company_name": "Test Persero",
        "sector": "Energi — Uji", "report_type": "Initiation",
        "date": "31 Agt 2026", "language": "id",
    },
    "cover": {
        "rating_box": {"action": "BUY", "tp": 1000, "prev_tp": None, "price": 900,
                       "upside_pct": 11.1, "key_takeaways": []},
        "vs_jci": {"ytd_abs": 1.0, "ytd_rel": 0.5, "source": "Sectors",
                   "chart": {"labels": ["Jan", "Feb"], "series": [[1, 2], [1, 1]]}},
        "shares": {"outstanding": 1.0, "unit": "bn", "free_float_pct": 25.0},
        "shareholders": [{"name": "Publik", "pct": 40.0}],
        "shareholders_src": "KSEI test-only",
        "esg": {"found": False},
    },
    "financial_highlights": {"source": "test-only", "years": ["FY24A", "FY25A"],
                             "rows": [["Revenue", 100, 110]]},
    "segments": [],
    "kpis": [],
    "thesis": [{"headline": "Scale", "detail": "test-only", "source": "test-only provenance"}],
    "valuation": {
        "methods": [{"method": "DCF", "fv": 1000, "source": "test-only engine",
                     "table": {"headers": ["Item", "FY26F"], "rows": [["FCF", 10]]}}],
        "blended": None, "bands": None,
    },
    "financials": [
        {"title": "Laba Rugi Ringkas", "source": "test-only provenance",
         "headers": ["Rp bn", "FY24A"], "rows": [["Revenue", 100]]},
    ],
    "risks": [{"bucket": "Harga", "detail": "test-only", "source": "test-only provenance"}],
    "peers": {"tables": [{"pillar": "Peers energi", "source": "test-only provenance",
                          "headers": ["Ticker", "P/E"], "rows": [["XXXX", 8.0]]}]},
    "exhibits": [],
}


def _render_jinja_html(payload: dict) -> str:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT))
    from render_pdf import render_html

    _name, html = render_html(payload)
    return html


def test_live_html_path_labels_every_object_and_numbers_globally() -> None:
    """The strongest guard on the live path: what the templates actually emit."""
    html = _render_jinja_html(dict(_JINJA_PAYLOAD))

    labels = [
        int(m.group(1))
        for m in re.finditer(r'class="exhibit-id">Exhibit (\d+)\.</span>', html)
    ]
    assert labels, "the live HTML report emitted no exhibit labels at all"
    assert sorted(labels) == list(range(1, len(labels) + 1)), (
        f"live HTML exhibit counter is not 1..N with no gaps/repeats: {sorted(labels)}"
    )

    # the label carries a period and a descriptive title, not a bare number
    titled = re.findall(
        r'class="exhibit-id">Exhibit \d+\.</span> <span class="exhibit-name">([^<]*)</span>',
        html,
    )
    assert len(titled) == len(labels), "an exhibit label has no title span"
    for title in titled:
        assert title.strip() and title.strip().lower() not in {
            "chart", "table", "graph", "data", "figure",
        }, f"generic exhibit title rendered: {title!r}"


def test_live_html_path_prints_the_constant_source_line_below_every_object() -> None:
    html = _render_jinja_html(dict(_JINJA_PAYLOAD))
    labels = len(re.findall(r'class="exhibit-id">Exhibit \d+\.</span>', html))
    assert html.count(CONSTANT_SOURCE) == labels, (
        f"{labels} exhibits but {html.count(CONSTANT_SOURCE)} constant source lines — "
        "one exhibit never had its source flushed (check pagefoot(ns=...))"
    )
    # the source line is a sibling AFTER the label, never inside the label row
    assert not re.search(r'class="exhibit-head">[^<]*<[^>]*>[^<]*Source:', html)
    # and no ad-hoc per-object source is printed anywhere
    assert not re.search(r'<div class="src-tag">', html)
    assert "Sumber:" not in html


def test_live_html_path_carries_the_house_furniture_on_every_page() -> None:
    html = _render_jinja_html(dict(_JINJA_PAYLOAD))
    pages = html.count('class="rhdr"')
    assert pages >= 1
    assert html.count(HOUSE_HEADER) == pages, "header title missing from some page"
    assert html.count('class="rhdr-logo"') == pages, "logo missing from some page"
    assert html.count('class="rhdr-rule"') == pages, "header divider missing from some page"
    assert html.count(">sectors.app<") == pages, "footer left missing from some page"
    assert html.count(HOUSE_FOOTER_RIGHT) == pages, "footer right missing from some page"
    # the date is rendered in house format, from the payload's raw date
    assert "31 Aug 2026" in html, "publication date not in `DD Mon YYYY`"
    assert "31 Agt 2026" not in html, "raw date string still rendered"


def test_live_html_path_provenance_is_kept_but_not_printed() -> None:
    html = _render_jinja_html(dict(_JINJA_PAYLOAD))
    # the audit trail survives for the /html debug endpoint...
    assert "test-only provenance" in html
    # ...but only inside comments
    for line in html.splitlines():
        if "test-only provenance" in line:
            assert line.strip().startswith("<!--"), f"provenance printed: {line.strip()[:80]}"


def test_house_format_module_matches_the_template_defaults() -> None:
    """The template defaults and the Python constants describe the same furniture; a value
    edited in one place only must not be able to drift."""
    from server.report import house_format

    c = _theme_constants()
    assert c["header_title"] == house_format.HEADER_TITLE
    assert c["footer_left"] == house_format.FOOTER_LEFT
    assert c["footer_right"] == house_format.FOOTER_RIGHT
    assert c["source_line"] == house_format.SOURCE_LINE
    assert c["divider_color"] == house_format.DIVIDER_COLOR


@pytest.mark.parametrize("tpl_file", ["report_single", "report_sotp", "report_infra",
                                      "report_strategy"])
def test_every_template_flushes_a_pending_source_line_on_every_page(tpl_file: str) -> None:
    """A page's last exhibit is flushed by the footer, so every page must both pass the
    namespace to pagefoot() and end with one. A page missing its footer silently drops
    the source line of its last exhibit."""
    src = (REPO_ROOT / "templates" / f"{tpl_file}.html").read_text(encoding="utf-8")
    pages = src.count('class="page"')
    foots = len(re.findall(r"\{\{ m\.pagefoot\(", src))
    with_ns = len(re.findall(r"\{\{ m\.pagefoot\(\d+, ns\) \}\}", src))
    assert pages == foots, f"{tpl_file}: {pages} pages but {foots} pagefoot calls"
    assert foots == with_ns, (
        f"{tpl_file}: {foots - with_ns} pagefoot call(s) do not pass the namespace, so a "
        "pending source line would be dropped"
    )
    assert "namespace(ex=0" in src, f"{tpl_file}: exhibit counter not initialised"


@pytest.mark.parametrize("tpl_file", ["report_single", "report_sotp", "report_infra",
                                      "report_strategy"])
def test_no_template_prints_its_own_source_line(tpl_file: str) -> None:
    src = (REPO_ROOT / "templates" / f"{tpl_file}.html").read_text(encoding="utf-8")
    assert "src-tag" not in src, f"{tpl_file} still styles a per-object source tag"
    assert "Sumber:" not in src, f"{tpl_file} still prints a per-object source line"


def test_shipped_pdf_passes_the_artifact_check(tmp_path: Path) -> None:
    """The strongest guard on the live path: the PDF a reader actually downloads.

    Every source-level guard above can pass while the shipped document is still wrong on
    paper, because none of them can see a PHYSICAL page:

    * per-`<div class="page">` furniture is lost to a page overflow, so a continuation
      page ships with no header and the previous logical page's footer (measured: 3 of 8
      pages, footer page numbers `[1,2,-,3,-,4,-,5]`);
    * an exhibit label is orphaned at the bottom of one page while its chart renders on
      the next, so the label is no longer ABOVE its object;
    * the footer page numbers repeat.

    So render the real thing through the real entrypoint and run the artifact verifier on
    it. Skips honestly when the only renderable ticker has no verified assumptions file.
    """
    if not (REPO_ROOT / "data" / "assumptions" / "AMMN.json").exists():
        pytest.skip("no verified assumptions for AMMN — nothing to render")

    import asyncio

    from server.routers.pdf import render_pdf_bytes_for_ticker

    pdf_bytes, engine, _tpl, _data = asyncio.run(render_pdf_bytes_for_ticker("AMMN"))
    assert engine == "playwright", (
        f"the shipped path fell back to {engine!r}: the Chromium furniture (header/footer on "
        "every physical page) is the only variant that satisfies house-report-format.md §3-4"
    )

    out = tmp_path / "live.pdf"
    out.write_bytes(pdf_bytes)

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import verify_house_format

    result = verify_house_format.check(out)
    assert result["info"]["exhibits"] > 0, "the shipped PDF carries no exhibit at all"
    assert not result["fails"], (
        "the shipped PDF breaks the house format:\n  " + "\n  ".join(result["fails"])
    )

    # Deck page 2 is the industry / catalysts / sentiment page (docs/ammn-slides/
    # slide2-industry-spec.md): three narrative paragraphs, no mandatory object. This is checked
    # on the PHYSICAL page, because the ordering guard in test_slide_rules_adoption can pass on
    # HTML while the page still overflows on paper and drops a paragraph with it.
    import pymupdf

    doc = pymupdf.open(out)
    page2 = doc[1].get_text()
    for heading in ("1. Kondisi Industri", "2. Katalis Spesifik Emiten", "3. Sentimen Pasar"):
        assert heading in page2, f"deck page 2 lost {heading!r} on paper"
    assert "Ringkasan Investasi" in doc[2].get_text(), "the summary page is no longer page 3"

    # Deck slide 3 (docs/ammn-slides/slide3-visual-spec.md) is a 2x2 grid on ONE physical page, and
    # its four charts take exhibits 4-7 -- the numbering the owner's spec assumes.
    page4 = doc[3].get_text()
    for quadrant in ("Revenue & Revenue Growth", "EBITDA & EBITDA Margin",
                     "Net Profit & EPS Growth", "DER vs ROE"):
        assert quadrant in page4, f"slide 3 lost {quadrant!r} on paper"
    for number in (4, 5, 6, 7):
        assert f"Exhibit {number}." in page4, f"Exhibit {number} is not on the slide-3 page"
    assert "Exhibit 8." in doc[4].get_text(), "the valuation page no longer opens at Exhibit 8"

    # Deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md): the DCF page carries the three blocks
    # and the WACC components, and the sensitivity grid with its narrative lands on the following page.
    val = doc[4].get_text()
    for marker in ("Blok 1 — Periode proyeksi eksplisit", "Blok 2 — Terminal value",
                   "Blok 3 — Bridge ke equity value", "WACC Components", "Fair Value per Share"):
        assert marker in val, f"slide 4 lost {marker!r} on paper"
    val2 = doc[5].get_text()
    assert "Sensitivity Analysis" in val2, "the sensitivity grid moved off the valuation spread"
    assert "Parameter paling sensitif" in val2, "the slide-4 narrative is missing"
    assert "UNRESOLVED" in val2, "the terminal-method gap is not disclosed on paper"


# --------------------------------------------- template call-site hygiene
# These three guards used to live in tests/test_exhibit_convention.py, which policed the
# deleted Typst template dialect. The properties are dialect-independent, so they now run
# against the templates the report API actually renders.


@pytest.mark.parametrize(
    "template", sorted(TEMPLATES_DIR.glob("report_*.html")), ids=lambda p: p.name
)
def test_no_template_hardcodes_an_exhibit_number(template: Path) -> None:
    """A literal 'Exhibit N' argument means numbering went manual again; the exhibit macro
    numbers itself from the document's global figure counter."""
    offenders = re.findall(r'exhibit_auto\(\s*"Exhibit\s+\d', template.read_text(encoding="utf-8"))
    assert not offenders, (
        f"{template.name}: {len(offenders)} call site(s) hardcode the exhibit number"
    )


@pytest.mark.parametrize(
    "template", sorted(TEMPLATES_DIR.glob("report_*.html")), ids=lambda p: p.name
)
def test_no_template_renders_its_own_source_label(template: Path) -> None:
    """Only one source label exists — the constant house line. A template that prints its own
    drifts the moment the rule changes."""
    assert "Sumber:" not in template.read_text(encoding="utf-8"), (
        f"{template.name} still renders a 'Sumber:' source line"
    )


@pytest.mark.parametrize(
    "template", sorted(TEMPLATES_DIR.glob("report_*.html")), ids=lambda p: p.name
)
def test_no_template_names_an_exhibit_number_in_prose(template: Path) -> None:
    """Prose that names an exhibit number by hand drifts the moment a page is revised; the
    label belongs to the object's own exhibit macro."""
    offenders = re.findall(
        r"(?:pada|lihat|Lihat|see|See)\s+Exhibit\s+\d+", template.read_text(encoding="utf-8")
    )
    assert not offenders, f"{template.name}: hardcoded prose exhibit reference(s) {offenders}"


def test_running_header_keeps_the_short_date():
    """The header repeats on every page; the owner asked for `11 Sep 2026` there and the long form in the body."""
    from server.report import house_format as hf

    tpl = hf.header_template(
        hf.format_house_date("2026-09-11", short=True),
        {"issuer": "AMMN IJ · PT Amman Mineral Internasional Tbk.", "status": "BUY · TP Rp 5.667"},
    )
    assert "11 Sep 2026" in tpl, "running header carries the house date form"
    assert "Friday" not in tpl, "no weekday in the furniture"
    assert hf.format_house_date("2026-09-11", short=False) == "Friday, 11 September 2026", "long form stays available"
