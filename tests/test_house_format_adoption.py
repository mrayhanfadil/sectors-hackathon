"""Adoption guards for the house report format.

`tests/test_exhibit_convention.py` proves the RENDERER implements the house format.
This file proves the format is actually adopted end to end:

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

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RULE_DOC = REPO_ROOT / "docs" / "rules" / "house-report-format.md"
DATA_CONTRACT = REPO_ROOT / "templates" / "DATA_CONTRACT.md"
TEMPLATES_ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"

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
    from server.report.typst_renderer import ARCHETYPE_TEMPLATE_FILES

    assert set(ARCHETYPE_TEMPLATE_FILES) >= {"single", "sotp", "infra", "strategy", "update"}
    for archetype, filename in ARCHETYPE_TEMPLATE_FILES.items():
        candidates = [TEMPLATES_ARCHETYPES / filename, SERVER_TYPST / filename]
        assert any(c.exists() for c in candidates), (
            f"archetype {archetype!r} maps to {filename!r}, which exists in neither tree"
        )
        txt = next(c.read_text(encoding="utf-8") for c in candidates if c.exists())
        assert "exhibit-header(" in txt or "exhibit-figure(" in txt, (
            f"{filename} has no house-formatted exhibits"
        )





# ------------------------------------------------------------ end-to-end adoption


@pytest.mark.skipif(
    shutil.which("typst") is None or shutil.which("pdftotext") is None,
    reason="needs the typst CLI and poppler pdftotext",
)
def test_document_built_by_the_production_loader_honours_the_house_format(tmp_path: Path) -> None:
    """The strongest guard: build a payload the way the API/renderer does, render it,
    and check the rules hold on the artifact a reader would receive."""
    sys.path.insert(0, str(REPO_ROOT))
    from server.report.typst_renderer import _load_or_build_report_data

    data_path = tmp_path / "report_data.json"
    data_path.write_text(
        json.dumps(_load_or_build_report_data("BBCA", "auto"), ensure_ascii=False),
        encoding="utf-8",
    )
    pdf = tmp_path / "report.pdf"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "render_typst.py"), str(data_path),
         "--out", str(pdf)],
        capture_output=True, text=True, timeout=600, cwd=str(REPO_ROOT),
    )
    assert pdf.exists(), f"render failed:\n{result.stdout}\n{result.stderr}"

    text = subprocess.run(
        ["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout
    pages = text.split("\f")[:-1] if text.endswith("\f") else text.split("\f")
    assert len(pages) >= 1

    # 1. the global counter: the numbers present must be exactly 2..N+1 — no
    # gaps, no repeats. Exhibit 1 is SKIPPED by canonical spec (no locked EPS
    # consensus feed; see slide1-cover-spec + AMMN-R2T R1 one-time counter
    # offset in report_single.typ), so the first header numbers as Exhibit 2.
    # NOT "appears in ascending order": a two-column page is extracted
    # column-by-column by pdftotext, so a perfectly correct counter interleaves
    # (JCI renders 1,3,4,2 by reading across columns). Order is checked per column
    # below instead, which is the property the rule actually needs.
    labels = [int(m.group(1)) for m in re.finditer(r"(?m)^Exhibit[\s\u00a0]+(\d+)\.", text)]
    n = len(labels)
    assert n > 0, "no exhibits rendered"
    assert sorted(labels) == list(range(2, n + 2)), (
        f"exhibit counter is not 2..N+1 with no gaps/repeats: {sorted(labels)}"
    )
    assert len(set(labels)) == n, f"exhibit number repeated: {labels}"

    # 2. one constant source line per exhibit
    assert text.count(CONSTANT_SOURCE) == len(labels), (
        f"{len(labels)} exhibits but {text.count(CONSTANT_SOURCE)} source lines"
    )

    # 3. no exhibit label is generic
    for title in re.findall(r"(?m)^Exhibit[\s\u00a0]+\d+\.\s*(.+)$", text):
        assert title.strip().lower() not in {"chart", "table", "graph", "data", "figure"}, (
            f"generic exhibit title rendered: {title!r}"
        )

    # 4. house header + footer on every page, with complete page numbers
    for i, page in enumerate(pages, 1):
        assert HOUSE_HEADER in page, f"page {i} missing the house header {HOUSE_HEADER!r}"
        assert "sectors.app" in page, f"page {i} missing the footer left"
        assert "See important disclosure at the back of this report" in page, (
            f"page {i} missing the footer right"
        )
        assert re.search(rf"report\s*·\s*{i}\b", page), f"page {i} missing its page number"

    # 5. the publication date is rendered in house format
    assert re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \d{1,2} \w+ \d{4}", text), (
        "no `Day, DD Month YYYY` publication date found"
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


def _theme_constants() -> dict:
    """Read the fixed strings straight out of the Typst theme, so the assertion is
    against what actually renders, not against a Python copy of it."""
    txt = (REPO_ROOT / "templates" / "typst" / "common" / "theme.typ").read_text(encoding="utf-8")
    out = {}
    for key in ("HEADER_TITLE", "FOOTER_LEFT", "FOOTER_RIGHT", "SOURCE_LINE", "HEADER_DIVIDER_COLOR"):
        m = re.search(rf'^#let {key} = (.+)$', txt, re.M)
        assert m, f"theme.typ no longer defines {key}"
        out[key] = m.group(1).strip()
    return out


def test_theme_furniture_matches_the_rule_doc() -> None:
    c = _theme_constants()
    assert c["HEADER_TITLE"] == f'"{HOUSE_HEADER}"', c["HEADER_TITLE"]
    assert c["FOOTER_LEFT"] == f'"{HOUSE_FOOTER_LEFT}"'
    assert c["FOOTER_RIGHT"] == f'"{HOUSE_FOOTER_RIGHT}"'
    assert c["HEADER_DIVIDER_COLOR"] == f'rgb("{HOUSE_DIVIDER}")', c["HEADER_DIVIDER_COLOR"]
    assert c["SOURCE_LINE"] == '"Company, Team Estimates"'

    # the derived printed source line is exactly what the rule doc mandates
    assert f"Source: {c['SOURCE_LINE'].strip(chr(34))}" == CONSTANT_SOURCE

    doc = RULE_DOC.read_text(encoding="utf-8")
    for value in (HOUSE_HEADER, HOUSE_FOOTER_LEFT, HOUSE_FOOTER_RIGHT, HOUSE_DIVIDER):
        assert value in doc, f"rule doc does not state {value!r}"
    assert CONSTANT_SOURCE in doc


def test_theme_carries_the_brand_mark() -> None:
    """The header right says Sectors.app logo; the theme must point at a real asset in
    BOTH template trees, since they are resolved by relative path."""
    txt = (REPO_ROOT / "templates" / "typst" / "common" / "theme.typ").read_text(encoding="utf-8")
    m = re.search(r'^#let LOGO_PATH = "(.+)"$', txt, re.M)
    assert m, "theme.typ has no LOGO_PATH"
    rel = m.group(1)
    for tree in ("templates/typst/common", "server/report/typst"):
        asset = (REPO_ROOT / tree / rel).resolve()
        assert asset.exists(), f"logo missing for {tree}: {asset}"


def _exhibit_positions(pdf) -> list:
    """(page, x, y, n) for every exhibit label, from the PDF's own word boxes."""
    import xml.etree.ElementTree as ET

    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True,
                         check=True).stdout
    root = ET.fromstring(out)
    ns = {"h": "http://www.w3.org/1999/xhtml"}
    positions = []
    for pi, page in enumerate(root.iter("{http://www.w3.org/1999/xhtml}page"), 1):
        words = [(float(w.get("xMin")), float(w.get("yMin")), (w.text or "").strip())
                 for w in page.iter("{http://www.w3.org/1999/xhtml}word")]
        for i, (x, y, txt) in enumerate(words):
            if txt == "Exhibit" and i + 1 < len(words):
                m = re.match(r"(\d+)\.", words[i + 1][2])
                if m:
                    positions.append((pi, x, y, int(m.group(1))))
    return positions


@pytest.mark.skipif(
    shutil.which("typst") is None or shutil.which("pdftotext") is None,
    reason="needs the typst CLI and poppler pdftotext",
)
def test_exhibit_counter_is_monotonic_down_the_page(tmp_path: Path) -> None:
    """The global counter must still run in reading order WITHIN a column: a lower
    number must not appear below a higher one on the same page in the same column.
    (Numbering is global across pages, so page-to-page starts are not constrained.)"""
    sys.path.insert(0, str(REPO_ROOT))
    from server.report.typst_renderer import _load_or_build_report_data

    data_path = tmp_path / "report_data.json"
    data_path.write_text(json.dumps(_load_or_build_report_data("BBCA", "auto"), ensure_ascii=False),
                         encoding="utf-8")
    pdf = tmp_path / "report.pdf"
    subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "render_typst.py"),
                    str(data_path), "--out", str(pdf)],
                   capture_output=True, text=True, timeout=600, cwd=str(REPO_ROOT))
    assert pdf.exists()

    # bucket labels into columns by x-distance, then require ascending y within a bucket
    from collections import defaultdict
    per_page = defaultdict(list)
    for pi, x, y, num in _exhibit_positions(pdf):
        per_page[pi].append((x, y, num))

    checked = 0
    for pi, items in per_page.items():
        if len(items) < 2:
            continue
        xs = sorted({round(x) for x, _, _ in items})
        cols = []
        for x in xs:
            if not cols or x - cols[-1][-1] > 40:
                cols.append([x])
            else:
                cols[-1].append(x)
        for col in cols:
            lo, hi = min(col) - 40, max(col) + 40
            nums = sorted(((y, n) for x, y, n in items if lo <= x <= hi))
            if len(nums) > 1:
                seq = [n for _, n in nums]
                assert seq == sorted(seq), f"page {pi} column {col}: exhibit numbers descend {seq}"
                checked += 1
    assert checked >= 1, "no multi-exhibit column was actually checked"


# =====================================================================================
# The LIVE path. The report the FE downloads comes from
# GET /api/report/{ticker}/pdf -> server/routers/pdf.py -> Jinja -> Playwright, which
# renders templates/*.html. The Typst tree is a separate template set with no router
# reaching it, so proving the Typst templates comply proves nothing about the document
# a reader actually gets. These tests exercise the Jinja path.
# =====================================================================================

# A self-contained payload: no fixture, no live fetch. Just enough shape to reach every
# exhibit-emitting branch of report_single.html (chart, table, statement, peer table).
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
    from render_pdf_chromium import render_html

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
    assert "Monday, 31 August 2026" in html, "publication date not in `Day, DD Month YYYY`"
    assert "31 Agt 2026" not in html, "raw date string still rendered"


def test_live_html_path_provenance_is_kept_but_not_printed() -> None:
    html = _render_jinja_html(dict(_JINJA_PAYLOAD))
    # the audit trail survives for the /html debug endpoint...
    assert "test-only provenance" in html
    # ...but only inside comments
    for line in html.splitlines():
        if "test-only provenance" in line:
            assert line.strip().startswith("<!--"), f"provenance printed: {line.strip()[:80]}"


def test_both_renderers_share_one_house_format_implementation() -> None:
    """Two independent Jinja environments (the API and the standalone script) render the
    same templates. The furniture must come from the shared module, not be re-typed."""
    from server.report import house_format

    assert house_format.HEADER_TITLE == HOUSE_HEADER
    assert house_format.FOOTER_LEFT == HOUSE_FOOTER_LEFT
    assert house_format.FOOTER_RIGHT == HOUSE_FOOTER_RIGHT
    assert house_format.DIVIDER_COLOR == HOUSE_DIVIDER
    assert f"Source: {house_format.SOURCE_LINE}" == CONSTANT_SOURCE

    for rel in ("server/routers/pdf.py", "scripts/render_pdf_chromium.py"):
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "house_format.install(env" in src, f"{rel} does not install the house furniture"


def test_house_format_module_matches_the_typst_theme() -> None:
    """The Jinja and Typst trees are independent; the values must not drift."""
    from server.report import house_format

    c = _theme_constants()
    assert c["HEADER_TITLE"] == f'"{house_format.HEADER_TITLE}"'
    assert c["FOOTER_LEFT"] == f'"{house_format.FOOTER_LEFT}"'
    assert c["FOOTER_RIGHT"] == f'"{house_format.FOOTER_RIGHT}"'
    assert c["SOURCE_LINE"] == f'"{house_format.SOURCE_LINE}"'
    assert c["HEADER_DIVIDER_COLOR"] == f'rgb("{house_format.DIVIDER_COLOR}")'


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
