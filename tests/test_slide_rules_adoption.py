"""Adoption guards for the slide rules (docs/rules/house-report-format.md §7-§9).

The exhibit rules are renderer-owned, so they cannot be broken from the agent side. The slide
rules constrain CONTENT - the cover structure, the paragraph mandates, the Key Financials
contract and the one-page copy budget - and content is exactly what drifts silently. These
guards assert that the rule doc, the agent instructions, the shared validator and the Critic
gate all say the same thing, and that each violation class is actually caught.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RULE_DOC = REPO_ROOT / "docs" / "rules" / "house-report-format.md"
INSTRUCTIONS = REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py"
HOUSE_RULES_PY = REPO_ROOT / "server" / "report" / "house_rules.py"
ASSUM_PATH = REPO_ROOT / "data" / "assumptions" / "AMMN.json"


# --------------------------------------------------------------------- doc / instruction sync
def test_rule_doc_carries_the_slide_sections() -> None:
    text = RULE_DOC.read_text(encoding="utf-8")
    for heading in ("## 6.", "## 7.", "## 8.", "## 9.", "## 10.", "## 11."):
        assert heading in text, f"rule doc is missing section {heading}"
    assert "2.600 characters" in text, "the copy budget must be stated in the rule doc"
    assert "Previous TP (Rp)" in text
    assert "Year to 31 Dec" in text
    # the deck page order is stated once, with page 2 named as the industry page
    assert "## 6. Deck page order" in text
    assert "audit_industry_page" in text and "slide2-industry-spec.md" in text


def test_agent_instructions_carry_the_slide_rules() -> None:
    text = INSTRUCTIONS.read_text(encoding="utf-8")
    # the block every content-producing agent receives
    block = text.split("HOUSE_FORMAT_RULE = \"\"\"", 1)[1].split('"""', 1)[0]
    for marker in (
        "SLIDE RULES",
        "2.600 characters",          # copy budget
        "QUANTITATIVE claim",        # highlights
        "theme title",               # thesis, not a product name
        "catalyst",                  # paragraph 2
        "four blocks",               # paragraph 3
        "Key Financials",            # exhibit contract
        "house_rules.py",
    ):
        assert marker in block, f"HOUSE_FORMAT_RULE does not state {marker!r}"


def test_shared_validator_is_imported_by_the_gate_and_the_renderer() -> None:
    """One implementation, three callers - otherwise the gate and the render disagree."""
    critic = (REPO_ROOT / "agents" / "critic.py").read_text(encoding="utf-8")
    renderer = (REPO_ROOT / "server" / "report" / "slide2.py").read_text(encoding="utf-8")
    assert "audit_house_rules" in critic
    assert "audit_house_rules" in renderer
    assert HOUSE_RULES_PY.exists()


# --------------------------------------------------------------------- validator behaviour
def _compliant_payload() -> dict:
    return {
        "cover": {
            "slide1": {
                "rating": {"action": "Buy", "action_status": "(Initiation)"},
                "price_box": {"rows": [
                    ["Last Price (Rp)", "4.860"],
                    ["Target Price (Rp)", "5.873"],
                    ["Previous TP (Rp)", "Initiation"],
                    ["Potential gain/loss (%)", "+20,84%"],
                ]},
                "stats": {
                    "rows": [["No. of Shares (mn)", "72.518,2"],
                             ["Mkt Cap (Rpbn/US$mn)", "1/2"],
                             ["Free Float (%)", "26,37"]],
                    "major_shareholders": [{"name": "PT X", "pct_str": "32,17%"}],
                },
                "jci_chart": {"price": [1, 2, 3]},
                "analyst": {"name": "RESEARCH", "title": "Equity Analyst"},
                "theme_title": "Smelter ramp lifts free cash flow into 2028",
                "highlights": ["Laba Rp 2,72 tn (turun 61,95% dari kuartal sebelumnya)", "Tembaga US$ 14.708/ton",
                               "TP Rp 5.873 (+20,84%)"],
                "financial_para": {"body": "Penjualan kuartal I 2026 Rp 13,73 tn, turun 36,94% dari kuartal sebelumnya."},
            },
            "slide2": {
                "katalis": {"body": (
                    "Verified Catalysts: (1) smelter done; Impact: capital spending down 69,6% "
                    "from the prior quarter. "
                    "The copper-price impact cannot be quantified into earnings. "
                    "Priced-in: 24 months -33,40% relative vs JCI."
                )},
                "valuasi": {"body": (
                    "We set TP Rp 5.873 using EV/EBITDA. CAGR 0,0%. At TP, "
                    "the stock is priced at 28,4× versus the 4-year historic average 28,42× vs "
                    "subsector. Risk to this view: copper -10%."
                )},
                "key_financials": {
                    "headers": ["Year to 31 Dec", "2024A", "2025A", "2026F", "2027F", "2028F"],
                    # G2.6 (handed-over ruleset): every forecast year differs from the one before
                    # it. The fixture used to hold 27.236 across all three forecast columns, which
                    # the ruleset bans without a declared flat reason - the pin moved to the new
                    # behaviour rather than the arm being softened.
                    "rows": [
                        ["Revenue (Rpbn)", "43.036", "30.904", "27.236", "29.100", "31.400"],
                        ["EBITDA (Rpbn)", "23.040", "16.410", "18.396", "19.900", "21.500"],
                        ["EBITDA Growth (%)", "n/a", "(28,8)", "12,1", "8,2", "8,0"],
                        ["Net Profit (Rpbn)", "10.290", "4.167", "7.004", "7.500", "8.100"],
                        ["EPS (Rp)", "141,9", "57,5", "96,6", "103,4", "111,7"],
                        ["EPS Growth (%)", "n/a", "(59,5)", "68,1", "7,0", "8,0"],
                        ["PER (x)", "34,2", "84,6", "50,3", "47,0", "43,5"],
                        ["PBV (x)", "3,8", "3,8", "3,8", "3,5", "3,2"],
                        ["EV/EBITDA (x)", "19,5", "27,4", "24,4", "22,5", "20,8"],
                    ],
                    "forecast_basis": "midcycle-normalised",
                    # §15: the fixture mirrors the shipped wording, so it carries no machine trace.
                    "notes": ["Catatan proyeksi: dasar normal, bukan kurva pertumbuhan ..."],
                },
            },
        },
    }


def test_validator_accepts_a_compliant_payload() -> None:
    from server.report.house_rules import audit_house_rules

    audit = audit_house_rules(_compliant_payload())
    assert audit["applicable"] is True
    assert audit["violations"] == [], audit["violations"]
    assert audit["ok"] is True


def test_validator_ignores_documents_without_a_cover() -> None:
    """A non-`single` archetype never had these sections; the gate must not invent a failure."""
    from server.report.house_rules import audit_house_rules

    audit = audit_house_rules({"meta": {"template": "infra"}, "valuation": {}})
    assert audit["applicable"] is False
    assert audit["ok"] is True


@pytest.mark.parametrize("mutate,expected", [
    (lambda p: p["cover"]["slide1"]["highlights"].__setitem__(0, "kinerja membaik"),
     "no number"),
    (lambda p: p["cover"]["slide1"].__setitem__("theme_title", "Company Update"),
     "generic"),
    (lambda p: p["cover"]["slide1"]["price_box"].__setitem__(
        "rows", [["Last Price (Rp)", "1"], ["Target Price (Rp)", "2"]]),
     "Previous TP"),
    (lambda p: p["cover"]["slide2"]["katalis"].__setitem__("body", "Berita bagus semua."),
     "paragraph 2"),
    (lambda p: p["cover"]["slide2"]["valuasi"].__setitem__("body", "TP Rp 5.873."),
     "forecast linkage"),
    (lambda p: p["cover"]["slide2"]["key_financials"].__setitem__(
        "headers", ["Metrik Finansial", "2024A", "2025A", "2026F", "2027F", "2028F"]),
     "first header cell"),
    (lambda p: p["cover"]["slide2"]["key_financials"]["rows"].__setitem__(
        0, ["Revenue", "43.036", "30.904", "27.236", "27.236", "27.236"]),
     "no unit"),
    (lambda p: p["cover"]["slide2"]["key_financials"]["rows"].__setitem__(
        1, ["EBITDA (Rpbn)", "23.040", "16.410", "18.396", "18.396", "-1"]),
     "parenthesis"),
    (lambda p: p["cover"]["slide2"]["key_financials"]["rows"].__setitem__(
        0, ["Revenue (Rpbn)", "43.036,4", "1", "1", "1", "1"]),
     "no decimals"),
    (lambda p: p["cover"]["slide1"]["financial_para"].__setitem__("body", "x" * 3000),
     "one-page budget"),
    # AWAM RULE (19 Sep 2026): the plain-language denylist has to bite on the tokens that
    # reached the shipped cover before this pass - a method-jargon literal, a code-shaped
    # fiscal-year tag, and the compact quarter tag. Each mutation is the exact string the
    # deck used to print, so the guard is proven on the real regression, not a synthetic one.
    (lambda p: p["cover"]["slide1"].__setitem__(
        "theme_title", "Pasar pakai 18,38 kali laba 2026 vs mid-cycle 28,42 kali"),
     "mid-cycle"),
    (lambda p: p["cover"]["slide1"].__setitem__(
        "highlights", ["EBITDA FY26F-28F Rp 33,9 tn", "Tembaga US$ 14.708/ton", "TP Rp 5.873 (+20,84%)"]),
     "code-shaped tag"),
    (lambda p: p["cover"]["slide1"]["financial_para"].__setitem__(
        "body", "Penjualan Q1-2026 Rp 13,73 tn."),
     "code-shaped tag"),
    (lambda p: p["cover"]["slide1"]["financial_para"].__setitem__(
        "body", "Basis kuartal I 2026: penjualan Rp 13,73 tn."),
     "'Basis '"),
])
def test_validator_catches_each_violation_class(mutate, expected: str) -> None:
    from server.report.house_rules import audit_house_rules

    payload = _compliant_payload()
    mutate(payload)
    violations = audit_house_rules(payload)["violations"]
    assert violations, "mutation went undetected"
    assert any(expected in v for v in violations), (expected, violations)


def test_critic_gate_rejects_a_cover_that_breaks_the_slide_rules() -> None:
    """The gate has to flip its verdict, not merely log a warning."""
    from agents.critic import audit_report_payload

    good = audit_report_payload(_compliant_payload())
    bad_payload = _compliant_payload()
    bad_payload["cover"]["slide1"]["highlights"] = ["pertumbuhan solid", "margin naik",
                                                    "prospek cerah"]
    bad = audit_report_payload(bad_payload)
    assert good["verdict"] == "PASS", good["reasons"]
    assert bad["verdict"] == "REJECT"
    assert bad["ready_for_pdf"] is False
    assert any("house slide rules" in r for r in bad["reasons"])


# --------------------------------------------------------------------- the real artifact
@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_live_cover_payload_passes_the_slide_rules() -> None:
    """The shipped cover must pass the same audit the gate runs - this is the regression line
    for the one-pager layout and for the forecast derivation notes."""
    from server.report.house_rules import audit_house_rules
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    audit = audit_house_rules(payload)
    assert audit["violations"] == [], audit["violations"]
    assert audit["copy_chars"] <= audit["copy_budget"]
    # and it is on the payload the API serves, so a human sees the same verdict
    assert payload.get("house_rules", {}).get("ok") is True
    assert json.dumps(payload["house_rules"])  # JSON-serialisable for the API response


# --------------------------------------------------------------------- render gate
def test_render_gate_reports_structural_violations_on_the_payload(monkeypatch) -> None:
    """A missing mandated section is reported on the payload (and REJECTed by the Critic gate),
    not thrown: a sparse ticker legitimately renders an honest "n/a" cover, so the severity
    split matters - a style/content defect must be visible, not fatal."""
    import server.report.house_rules as house_rules
    import server.routers.pdf as pdf_router

    stub = {"ok": False, "applicable": True, "copy_chars": 0, "copy_budget": 2600,
            "violations": ["cover: paragraph 3 (valuation) missing"]}
    monkeypatch.setattr(house_rules, "audit_house_rules", lambda payload=None: stub)
    payload = pdf_router._build_live_payload("AMMN", None)
    assert payload["house_rules"]["ok"] is False
    assert "paragraph 3" in payload["house_rules"]["violations"][0]


def test_render_gate_reports_but_does_not_block_style_violations(monkeypatch) -> None:
    """A misplaced decimal is imperfect, not incomplete: it must be visible on the document
    payload (report_data.json) without taking the report offline."""
    import server.report.house_rules as house_rules
    import server.routers.pdf as pdf_router

    stub = {"ok": False, "applicable": True, "copy_chars": 10, "copy_budget": 2600,
            "violations": ["Key Financials 'Revenue (Rpbn)' carries no unit"]}
    monkeypatch.setattr(house_rules, "audit_house_rules", lambda payload=None: stub)
    payload = pdf_router._build_live_payload("AMMN", None)
    assert payload["house_rules"]["ok"] is False
    assert payload["house_rules"]["violations"]


def test_builder_failures_are_recorded_not_swallowed(monkeypatch) -> None:
    """The slide builders used to fail into `except: pass`, which made the audit
    'not applicable' and let a broken cover through. A crash now blocks."""
    import server.report.slide2 as slide2
    import server.routers.pdf as pdf_router

    def boom(*_a, **_k):
        raise ValueError("builder exploded")

    monkeypatch.setattr(slide2, "build", boom)
    with pytest.raises(RuntimeError, match="cover builders failed"):
        pdf_router._build_live_payload("AMMN", None)


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_live_payload_carries_both_verdicts() -> None:
    """The served payload must expose the Critic verdict and the slide audit, so the gate,
    the guards and a human reading the JSON agree."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    assert payload["critic"]["verdict"] == "PASS", payload["critic"]["reasons"]
    assert payload["critic"]["ready_for_pdf"] is True
    assert payload["house_rules"]["ok"] is True
    assert payload["house_rules"]["applicable"] is True


# ------------------------------------------------- deck page 2 (docs/ammn-slides/slide2-industry-spec.md)
SLIDE2_SPEC = REPO_ROOT / "docs" / "ammn-slides" / "slide2-industry-spec.md"
SLIDE2_PARAGRAPHS = (
    "1. Industry Conditions",
    "2. Issuer-Specific Catalysts",
    "3. Market Sentiment",
)
SLIDE2_AGENTS = (
    "industry_instruction",
    "news_harvester_instruction",
    "writer_instruction",
    "critic_instruction",
)


def test_slide2_spec_carries_the_binding_rule_text() -> None:
    """The owner's wording has to be in the spec, not only a paraphrase of it."""
    text = SLIDE2_SPEC.read_text(encoding="utf-8")
    assert "### 1.3 Binding rule text" in text
    assert "Tidak ada tabel/chart wajib di slide ini secara default" in text
    for marker in (
        "outperform",
        "kualitatif eksplisit, jangan dipaksa kasih angka",
        "tanpa menyentuh valuasi atau target price",
        "consensus rating",
    ):
        assert marker in text, f"slide-2 spec lost the owner's requirement: {marker}"
    # the page contract must name its implementation, or the rule and the code drift apart
    assert "server/report/industry_page.py" in text
    assert "audit_industry_page" in text


def test_agent_instructions_carry_the_page2_contract() -> None:
    """Every agent whose output lands on the page must be told the page's contract."""
    text = INSTRUCTIONS.read_text(encoding="utf-8")
    assert "SLIDE_PAGES_RULE" in text
    for name in SLIDE2_AGENTS:
        idx = text.find(f"{name} = ")
        assert idx > 0, f"{name} is gone"
        tail = text[idx : idx + 12000]
        end = tail.find("\n\n\n")  # next constant block
        block = tail[: end if end > 0 else len(tail)]
        assert "SLIDE_PAGES_RULE" in block, f"{name} does not carry the deck-page contract"
    # the modeler calculates and never narrates, so it must not collect narrative page rules
    modeler = text[text.find("modeler_instruction = ") : text.find("analyst_instruction = ")]
    assert "SLIDE_PAGES_RULE" not in modeler, "the modeler must not carry narrative page rules"


def test_page2_contract_states_the_three_paragraphs_and_the_valuation_ban() -> None:
    block = " ".join(
        INSTRUCTIONS.read_text(encoding="utf-8")
        .split('SLIDE_PAGES_RULE = """', 1)[1]
        .split('"""', 1)[0]
        .split()
    )
    for marker in (
        "Page 2",
        "Paragraph 1 (Kondisi Industri)",
        "Paragraph 2 (Katalis Spesifik Emiten)",
        "Paragraph 3 (Sentimen Pasar)",
        "VALUATION IS FORBIDDEN HERE",
        "A forced number is a REJECT",
        "never fill the gap with a plausible figure",
    ):
        assert marker in block, f"page-2 contract lost: {marker}"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_industry_page_builder_emits_three_traceable_paragraphs() -> None:
    """The builder must fill all three paragraphs, and every paragraph must carry its basis."""
    from server.routers.pdf import _build_live_payload

    page = _build_live_payload("AMMN", None).get("industry_page")
    assert page, "the served payload must carry the deck page 2"
    assert [p["heading"] for p in page["paragraphs"]] == list(SLIDE2_PARAGRAPHS)
    for paragraph in page["paragraphs"]:
        assert len(paragraph["body"]) > 200, f"{paragraph['heading']} is too thin to be a paragraph"
        assert paragraph["basis"], f"{paragraph['heading']} carries no traceable basis"
    assert page["sources"], "the page must list the outlets its numbers came from"
    assert "Relative position" in page["paragraphs"][0]["body"]
    assert "90 days" in page["paragraphs"][2]["body"]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_industry_page_is_honest_about_what_the_data_does_not_carry() -> None:
    """No tonnage/grade/C1 in the payload and no rating endpoint: both must be named in the copy
    rather than replaced with a plausible figure."""
    from server.routers.pdf import _build_live_payload

    page = _build_live_payload("AMMN", None)["industry_page"]
    p1, p3 = page["paragraphs"][0]["body"], page["paragraphs"][2]["body"]
    assert "cannot" in p1 and "C1" in p1
    assert "neither stated nor invented" in p3
    assert "not extrapolated" in p3


def test_house_gate_catches_each_slide2_violation_class() -> None:
    """Three paragraph mandates, an empty body, and valuation language in paragraph 3."""
    from server.report.house_rules import audit_industry_page

    clean = {
        "paragraphs": [
            {"heading": h, "body": "Isi paragraf yang cukup panjang untuk lolos audit ini."}
            for h in SLIDE2_PARAGRAPHS
        ]
    }
    assert audit_industry_page(clean) == []
    assert audit_industry_page(None) == []  # absent page = not applicable, never a violation

    missing = copy.deepcopy(clean)
    missing["paragraphs"] = missing["paragraphs"][:2]
    assert any("3. Market Sentiment" in v for v in audit_industry_page(missing))

    empty = copy.deepcopy(clean)
    empty["paragraphs"][0]["body"] = "   "
    assert any("has no body" in v for v in audit_industry_page(empty))

    leaky = copy.deepcopy(clean)
    leaky["paragraphs"][2]["body"] = "Kami menetapkan TP Rp 5.873 dari EV/EBITDA 28,42× (WACC 13,77%)."
    caught = audit_industry_page(leaky)
    assert any("valuation language" in v for v in caught), caught
    assert "tp" in caught[0] and "ev/ebitda" in caught[0]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_live_slide2_page_passes_its_own_gate() -> None:
    from server.report.house_rules import audit_industry_page
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    assert audit_industry_page(payload["industry_page"]) == []
    assert "slide2-industry" in payload["house_rules"]["sections"]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_served_html_renders_page2_before_the_summary_page() -> None:
    """Deck order: the industry page is page 2, the summary follows it, and the footer page
    numbers stay sequential after the insertion."""
    import re

    from server.routers.pdf import render_html_for_ticker

    _tpl, html, payload = render_html_for_ticker("AMMN", None)
    assert "Industry, Catalysts" in html  # autoescape turns the "&" into "&amp;"
    for heading in SLIDE2_PARAGRAPHS:
        assert heading in html, f"{heading} is not rendered"
    assert html.index("Industry, Catalysts") < html.index("Investment Summary")
    # every later page shifted by one: the summary page is now page 3
    numbers = sorted({int(n) for n in re.findall(r"back of this report · (\d+)", html)})
    assert numbers == list(range(1, len(numbers) + 1)), f"footer page numbers not sequential: {numbers}"
    assert html.count('<div class="page">') == len(numbers), "one footer per rendered page"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_slide2_reports_both_directions_of_insider_activity() -> None:
    """The catalyst ledger leads with insider buying; the filings carry selling too. A page that
    prints one direction is fully sourced and still misleading, so both must reach the reader."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    digest = payload["filings_digest"]
    assert digest["buy"]["n"] and digest["sell"]["n"], "the filings digest lost one side"
    body = payload["industry_page"]["paragraphs"][1]["body"]
    assert "buy transactions" in body and "sell transactions" in body
    assert "not supported by the data" in body, "the page must say the one-sided read is unsupported"
    assert "The net" in body and "not a figure" in body, "the summed net must be labelled a sum"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_slide2_uses_the_wider_sectors_evidence() -> None:
    """Page 2 reads the subsector report, the IDX filings, corporate actions, the monthly ownership
    composition and the free-float screener - not only the four headline catalysts."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    for block in ("sector_data", "filings_digest", "corporate_actions", "ownership_mix", "free_float"):
        assert payload.get(block), f"{block} missing from the filled payload"
    body = " ".join(p["body"] for p in payload["industry_page"]["paragraphs"])
    assert "Sectors projects" in body, "the subsector report is not used"
    assert "IDX disclosures" in body, "the filings digest is not used"
    assert "AGM" in body, "corporate actions are not used"
    assert "foreign ownership" in body, "the ownership composition is not used"
    assert "public float" in body, "the free-float screener is not used"
    assert len(payload["industry_page"]["sources"]) >= 5, payload["industry_page"]["sources"]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_slide2_single_year_comparison_is_not_a_cumulative_move() -> None:
    """The positioning line compares one-year growth with a one-year forecast. A five-year
    cumulative move beside a forecast would flatter the issuer, so guard the choice."""
    from server.routers.pdf import _build_live_payload

    body = _build_live_payload("AMMN", None)["industry_page"]["paragraphs"][0]["body"]
    assert "latest-year revenue growth" in body
    assert "(actual, latest year vs the prior one)" in body
    assert "the periods differ" in body


# ------------------------------------------------- rules in the ADK prompt, the gate and the CLI
def test_agent_prompt_states_the_evidence_discipline() -> None:
    """The prompt, not only the reference doc, has to carry the evidence rules the gate enforces."""
    block = " ".join(
        INSTRUCTIONS.read_text(encoding="utf-8")
        .split('SLIDE_PAGES_RULE = """', 1)[1]
        .split('"""', 1)[0]
        .split()
    )
    for marker in (
        "WIDEST Sectors evidence",
        "subsector report",
        "Related-party flow is reported in BOTH directions",
        "is a REJECT",
        "Compare like with like",
        "tonnage, grade, C1, AISC",
    ):
        assert marker in block, f"the agent prompt lost: {marker}"


def test_gate_rejects_a_one_sided_related_party_read() -> None:
    """The press leads with the buys and the filings also carry sells: the gate refuses a page that
    reports one direction while the payload holds both."""
    from server.report.house_rules import audit_industry_page

    def page(catalysts_body: str) -> dict:
        return {
            "paragraphs": [
                {"heading": "1. Industry Conditions", "body": "x" * 250},
                {"heading": "2. Issuer-Specific Catalysts", "body": catalysts_body},
                {"heading": "3. Market Sentiment", "body": "y" * 250},
            ]
        }

    payload = {"filings_digest": {"buy": {"n": 11}, "sell": {"n": 9}}}
    one_sided = audit_industry_page(page("only insider buy transactions mentioned"), payload)
    assert any("omits related-party 'sell'" in v for v in one_sided), one_sided
    assert audit_industry_page(page("buy and sell transactions both mentioned"), payload) == []
    # an absent digest cannot trigger the check: the copy's missing-data line covers that case
    assert audit_industry_page(page("only insider buy transactions mentioned"), {}) == []


def test_cli_pipeline_builds_and_audits_the_page() -> None:
    """`scripts/render_pdf.py` renders whatever payload it is handed, so it must attach the page
    and run the same audit instead of rendering a payload that predates the slide rules."""
    import json
    import sys as _sys

    _sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import render_pdf

    # built live rather than read from output/cache/render_ammn/report_data.json: that file is an
    # untracked snapshot and went stale the moment the forecast basis changed, which made this test
    # assert about a payload the pipeline no longer produces.
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    payload.pop("industry_page", None)  # a payload that predates the page, whatever the cache holds
    render_pdf.ensure_industry_page(payload)
    assert [p["heading"] for p in payload["industry_page"]["paragraphs"]] == list(SLIDE2_PARAGRAPHS)
    assert render_pdf.validate(payload) == []

    # and it must refuse a payload whose page breaks the rules
    import copy

    broken = copy.deepcopy(payload)   # the live payload carries a DataFrame, so deep-copy not JSON round-trip
    broken["industry_page"]["paragraphs"] = broken["industry_page"]["paragraphs"][:2]
    assert any("house rules" in e for e in render_pdf.validate(broken))


def test_adk_agents_carry_the_page2_rules_at_runtime() -> None:
    """The composition can be right in the constant and still not reach an agent. Build the real
    ADK tree and read the instruction the framework will actually send, then check the roster:
    the narrative agents carry the rule and the calculating agents do not."""
    import os

    from agents.adk.app import build_graph

    os.environ.setdefault("GOOGLE_API_KEY", "structure-only")
    os.environ.setdefault("DEEPSEEK_API_KEY", "structure-only")
    root = build_graph(ticker="AMMN")

    carried: dict[str, str] = {}

    def walk(agent) -> None:
        carried[str(getattr(agent, "name", "?"))] = str(getattr(agent, "instruction", "") or "")
        for sub in getattr(agent, "sub_agents", []) or []:
            walk(sub)

    walk(root)
    marker = "Related-party flow is reported in BOTH directions"
    for name in ("news_harvester", "industry", "writer", "critic"):
        assert name in carried, f"the ADK graph no longer builds a {name} agent"
        assert marker in carried[name], f"{name} does not receive the page-2 evidence rules"
        assert "WIDEST Sectors evidence" in carried[name], f"{name} lost the evidence instruction"
    for name in ("collector", "modeler", "risk", "visualizer", "sotp"):
        assert marker not in carried[name], f"{name} calculates, it should not carry narrative rules"


# ------------------------------------------------- deck slide 3 (docs/ammn-slides/slide3-visual-spec.md)
SLIDE3_SPEC = REPO_ROOT / "docs" / "ammn-slides" / "slide3-visual-spec.md"
SLIDE3_QUADRANTS = (
    "Revenue & Revenue Growth",
    "EBITDA & EBITDA Margin",
    "Net Profit & EPS Growth",
    "DER vs ROE",
)


def test_slide3_spec_carries_the_binding_rule_text() -> None:
    text = SLIDE3_SPEC.read_text(encoding="utf-8")
    for marker in (
        "## 0. Binding rule text",
        "Layout grid 2x2",
        "harus menempel visual dengan chart-nya masing-masing",
        "navy solid untuk data aktual",
        "switchable by sector",
        "sanity check apakah asumsi margin forecast realistis",
        "tie-out langsung dengan Exhibit 3",
        "didiskusikan case-by-case saat build",
    ):
        assert marker in text, f"slide-3 spec lost: {marker}"
    assert "audit_performance_page" in text and "performance_page.py" in text


def test_slide3_agent_contract_is_in_the_prompt() -> None:
    block = " ".join(
        INSTRUCTIONS.read_text(encoding="utf-8")
        .split('SLIDE_PAGES_RULE = """', 1)[1]
        .split('"""', 1)[0]
        .split()
    )
    for marker in (
        "Page 3",
        "2x2 grid",
        "must sit WITH that chart",
        "Actual bars and forecast bars must be visually distinguishable",
        "explained by name (interest, tax, minority interest, FX)",
        "SAY SO on the page",
        "Two pages stating different numbers for one period is a REJECT",
    ):
        assert marker in block, f"the prompt lost: {marker}"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_performance_page_emits_four_complete_quadrants() -> None:
    from server.routers.pdf import _build_live_payload
    from server.report.house_rules import audit_performance_page

    payload = _build_live_payload("AMMN", None)
    page = payload.get("performance_page")
    assert page, "the served payload must carry deck slide 3"
    assert [q["title"] for q in page["quadrants"]] == list(SLIDE3_QUADRANTS)
    for q in page["quadrants"]:
        assert len(q["labels"]) == len(q["bars"]) == len(q["line"]), q["title"]
        assert len([v for v in q["bars"] if v is not None]) >= 2, f"{q['title']} has no bars"
        assert any(v is not None for v in q["line"]), f"{q['title']} has no line series"
        assert len(q["narrative"]) >= 120, f"{q['title']} narrative is too thin"
        assert 0 < q["actual_n"] <= len(q["labels"]), f"{q['title']} mislabels actual periods"
        assert q["bar_fmt"] and q["line_fmt"], f"{q['title']} has no axis labels"
    assert audit_performance_page(page, payload) == []


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_performance_numbers_tie_out_with_the_key_financials_exhibit() -> None:
    """Recompute the tie-out in the test with its own parser: every bar on slide 3 must equal the
    cover table's cell for the same period, read the Indonesian way ("43.036" = 43036)."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    kf = (payload["cover"]["slide2"])["key_financials"]
    periods = [str(h) for h in kf["headers"]][1:]

    def parse(cell):
        if isinstance(cell, (int, float)):
            return float(cell)
        text = str(cell).strip().strip("()").replace("%", "")
        if text in ("", "-", "n/a"):
            return None
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        elif text.count(".") == 1 and len(text.split(".")[1]) == 3:
            text = text.replace(".", "")
        try:
            return float(text)
        except ValueError:
            return None

    def cover_row(needle: str) -> list:
        for row in kf["rows"]:
            if needle in str(row[0]).lower():
                return [parse(c) for c in row[1:]]
        raise AssertionError(f"no Key Financials row matches {needle!r}")

    pairs = (
        ("Revenue & Revenue Growth", cover_row("revenue")),
        ("EBITDA & EBITDA Margin", cover_row("ebitda")),
        ("Net Profit & EPS Growth", cover_row("net profit")),
    )
    for title, reference in pairs:
        quad = next(q for q in payload["performance_page"]["quadrants"] if q["title"] == title)
        assert quad["labels"] == periods, f"{title} does not use the Key Financials periods"
        for label, value, ref in zip(periods, quad["bars"], reference):
            assert value is not None and ref is not None, f"{title} {label} is blank on one side"
            assert abs(value - ref) < 0.51, f"{title} {label}: slide 3 says {value}, cover says {ref}"


def test_gate_catches_each_slide3_violation_class() -> None:
    import copy

    from server.report.house_rules import audit_performance_page

    quad = lambda t: {  # noqa: E731
        "title": t,
        "labels": ["2024A", "2025A"],
        "bars": [100.0, 90.0],
        "line": [None, -10.0],
        "actual_n": 2,
        # comfortably over the audit's 120-character floor
        "narrative": (
            "Narasi kuadran yang sengaja dibuat panjang supaya melewati ambang seratus dua puluh "
            "karakter yang dipakai audit, sekaligus menyebut angka aktual dan proyeksi."
        ),
        "bar_fmt": ["100", "90"],
        "line_fmt": ["", "-10"],
    }
    clean = {"quadrants": [quad(t) for t in SLIDE3_QUADRANTS]}
    assert audit_performance_page(clean) == []
    assert audit_performance_page(None) == []

    thin = copy.deepcopy(clean)
    thin["quadrants"][1]["narrative"] = "terlalu pendek"
    assert any("no attached narrative" in v for v in audit_performance_page(thin))

    missing = copy.deepcopy(clean)
    missing["quadrants"] = missing["quadrants"][:3]
    assert any("DER vs ROE" in v for v in audit_performance_page(missing))

    unmarked = copy.deepcopy(clean)
    unmarked["quadrants"][0]["actual_n"] = None
    assert any("does not mark which bars are actual" in v for v in audit_performance_page(unmarked))


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_gate_rejects_a_number_that_breaks_the_tie_out() -> None:
    import copy

    from server.report.house_rules import audit_performance_page
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    tampered = copy.deepcopy(payload["performance_page"])
    tampered["quadrants"][0]["bars"][1] = 9999.0
    caught = audit_performance_page(tampered, payload)
    assert any("tie-out" in v and "2025A" in v for v in caught), caught


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_served_html_marks_forecast_bars_and_numbers_the_page_exhibits() -> None:
    """Actual vs forecast must be distinguishable in the shipped markup, and the four charts must
    take exhibits 4-7 (the numbering the owner's spec assumes)."""
    from server.routers.pdf import render_html_for_ticker

    _tpl, html, payload = render_html_for_ticker("AMMN", None)
    assert "s3-grid" in html, "the 2x2 grid class is missing from the shipped page"
    # titles arrive HTML-escaped ("&" -> "&amp;"), so compare on the escaped form
    for title in SLIDE3_QUADRANTS:
        assert title.replace("&", "&amp;") in html, f"{title} is not rendered"
    # Spec: "NAVY at reduced opacity (~40%) OR diagonal hatch, consistently one of the two across the whole
    # slide (renderer picks; the two encodings never mixed)".
    assert "opacity=\"0.4\"" in html, "forecast bars are not drawn at the spec's reduced opacity"
    assert 'pattern id="fc-1"' not in html, "both encodings are in use at once; the spec allows one"
    quad = payload["performance_page"]["quadrants"][0]
    assert quad["actual_n"] == 2 and len(quad["labels"]) == 5
    assert "Bentuk: 3 periode proyeksi" not in html  # guard against a stale caption


# ------------------------------------------------- deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md)
SLIDE4_SPEC = REPO_ROOT / "docs" / "ammn-slides" / "slide4-valuation-spec.md"


def test_slide4_spec_carries_the_binding_rule_text() -> None:
    text = SLIDE4_SPEC.read_text(encoding="utf-8")
    for marker in (
        "## 0. Binding rule text",
        "Metode dipilih manual oleh analis",
        "Opsi A - DCF (FCFF-based)",
        "Blok 1 - Explicit forecast period",
        "Tax on EBIT (dihitung EBIT x (1-effective tax rate)",
        "Gordon Growth vs Exit Multiple), tampilkan berdampingan",
        "Fair Value per Share (bold, highlight)",
        "Exhibit 9. WACC Components",
        "Exhibit 10. Sensitivity Analysis",
        "di-highlight beda warna",
        "wajib di-flag eksplisit sebagai unresolved assumption",
        "Opsi B - DDM",
        "Opsi C - RNAV",
        "INDOGB 10Y untuk Rf IDR",
        "finite reserve life",
        "server/report/engines/",
        "dcf_engine/",
        "ddm_engine/",
    ):
        assert marker in text, f"slide-4 spec lost: {marker}"
    assert "audit_valuation_page" in text and "dcf_engine" in text


def test_slide4_agent_contract_is_in_the_prompt() -> None:
    block = " ".join(
        INSTRUCTIONS.read_text(encoding="utf-8")
        .split('SLIDE_PAGES_RULE = """', 1)[1]
        .split('"""', 1)[0]
        .split()
    )
    for marker in (
        "Page 4 - Valuasi Intrinsik",
        "the ANALYST picks it",
        "State on the page which option you chose and why the other two do not apply",
        "tax on EBIT at the EFFECTIVE rate",
        "two separate columns",
        "must name its source",
        "base case is highlighted",
        "UNRESOLVED assumption",
        "Never average two terminal methods quietly",
        "not defensible for a finite reserve",
    ):
        assert marker in block, f"the prompt lost: {marker}"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_valuation_page_reproduces_the_cover_dcf_leg() -> None:
    """Slide 4's bridge must be the same DCF the cover prints, not a second opinion: if the two differ,
    the deck states two different fair values for one model."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    page = payload["valuation_page"]
    assert page["available"], page.get("missing")
    assert len(page["periods"]) == 5
    cover_leg = (payload["valuation"]["legs"] or {}).get("dcf")
    assert cover_leg, "the cover no longer publishes its DCF leg"
    engine_fv = page["bridge"]["fv_gordon"]
    assert abs(engine_fv - cover_leg) / cover_leg < 0.01, (
        f"slide 4 says Rp {engine_fv:.2f}, the cover says Rp {cover_leg:.2f}"
    )
    # and the relative leg must still be the one that anchors the target price
    assert payload["valuation"]["anchor"] == "ev_ebitda"
    assert abs(page["bridge"]["fv_exit"] - page["bridge"]["fv_gordon"]) > 0


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_valuation_page_shape_and_disclosures() -> None:
    from server.routers.pdf import _build_live_payload

    page = _build_live_payload("AMMN", None)["valuation_page"]
    rows = dict(page["block1_rows"])
    for required in (
        "Revenue", "EBIT", "Tax on EBIT (tarif efektif)", "NOPAT", "(+) Depreciation & Amortization",
        "(-) Capital Expenditure", "(-/+) Increase/Decrease in Net Working Capital",
        "FCFF (build-up)", "FCFF growth (%)", "Discount factor (1/(1+WACC)^n)", "PV of FCFF",
    ):
        assert required in rows, f"block 1 lost {required}"
        assert len(rows[required]) == 5, f"{required} is not five periods wide"
    labels = [r[0] for r in page["block2_rows"]]
    assert any("Terminal Growth" in x or "Terminal growth" in x for x in labels)
    assert any("PV of Terminal Value" in x for x in labels)
    assert len(page["sensitivity"]["rows"]) == 5 and len(page["sensitivity"]["columns"]) == 5
    assert sum(1 for r in page["sensitivity"]["rows"] for c in r["cells"] if c["base"]) == 1
    notes = " ".join(page["notes"]).upper()
    assert "UNRESOLVED" in notes, "the terminal gap is not flagged as unresolved"
    # the gate accepts either token; the printed copy states the limitation as a finite reserve or a
    # perpetual terminal value, whichever the reader's language carries (see audit_valuation_page)
    assert "RESERVE" in notes or "PERPETUAL" in notes, "the finite-reserve limitation is not disclosed"
    assert "year-end" in " ".join(page["notes"]).lower() or "konvensi" in " ".join(page["notes"]).lower()
    assert any("Sectors" in s for s in page["sources"])
    # Amended: the engine provenance must still be stated, but it now names the model ("model DCF internal (FCFF)")
    # rather than the module path, so a reader is not handed an address inside the repository. Revert by restoring the
    # path form here and removing the engines/* rule from server/report/text_sanitize.py.
    assert any(re.search(r"internal DCF model|model DCF internal|engines/dcf_engine", s) for s in page["sources"]), (
        "the engine provenance is not stated"
    )


def test_gate_catches_each_slide4_violation_class() -> None:
    import copy

    import pandas as pd

    from server.report.house_rules import audit_valuation_page

    def clean_page() -> dict:
        return {
            "available": True,
            "subtitle": "DCF dipilih; DDM tidak berlaku; RNAV tidak dapat disusun",
            "periods": ["FY2026F"] * 5,
            "blocks": {"build_up": {
                "Revenue": [1.0] * 5, "EBIT": [1.0] * 5, "Tax on EBIT": [1.0] * 5, "NOPAT": [1.0] * 5,
                "(+) D&A": [1.0] * 5, "(-) Capex": [1.0] * 5, "(-/+) Delta NWC": [1.0] * 5,
                "FCFF (build-up)": [1.0] * 5, "FCFF growth (%)": [None] * 5,
                "Discount factor": [1.0] * 5, "PV of FCFF": [1.0] * 5,
            }},
            "bridge": {"pv_explicit": 1.0, "pv_tv_gordon": 1.0, "ev_gordon": 1.0, "equity_gordon": 1.0,
                       "fv_gordon": 100.0, "tv_exit": 1.0, "fv_exit": 400.0},
            "wacc_rows": [("Risk-free rate (Rf)", "7.10%", "INDOGB 10Y"), ("Beta", "1.4", "regression"),
                          ("Equity Risk Premium (ERP)", "6.69%", "Damodaran"), ("Cost of Equity", "16.5%", "calc"),
                          ("Cost of Debt pre-tax", "6.49%", "financials"), ("Effective tax rate", "22%", "financials"),
                          ("Cost of Debt after-tax", "5.06%", "calc"), ("Weight of Equity", "76%", "market cap"),
                          ("Weight of Debt", "24%", "debt"), ("WACC", "13.77%", "calc")],
            "sensitivity": {"fair_value": pd.DataFrame([[1.0] * 5] * 5), "wacc_axis": [0] * 5,
                            "g_axis": [0] * 5, "base": (2, 2)},
            "notes": ["UNRESOLVED ASSUMPTION - the two terminals differ", "Reserve finite: perpetual growth not defensible"],
        }

    assert audit_valuation_page(clean_page()) == []
    assert audit_valuation_page(None) == []
    assert audit_valuation_page({"available": False}) == []

    no_exit = clean_page()
    no_exit["bridge"]["tv_exit"] = None
    assert any("single terminal method" in v for v in audit_valuation_page(no_exit))

    short_row = clean_page()
    short_row["blocks"]["build_up"]["FCFF (build-up)"] = [1.0, 2.0]
    assert any("FCFF (build-up)" in v for v in audit_valuation_page(short_row))

    unsourced = copy.deepcopy(clean_page())
    unsourced["wacc_rows"][0] = ("Risk-free rate (Rf)", "7.10%", "")
    assert any("without naming its source" in v for v in audit_valuation_page(unsourced))

    hidden_gap = clean_page()
    hidden_gap["notes"] = ["Reserve finite only"]
    assert any("unresolved assumption" in v for v in audit_valuation_page(hidden_gap))

    unmarked = clean_page()
    unmarked["sensitivity"]["base"] = None
    assert any("base case" in v for v in audit_valuation_page(unmarked))

    opaque = clean_page()
    opaque["subtitle"] = "DCF FCFF"
    assert any("excluded" in v for v in audit_valuation_page(opaque))


# ------------------------------------------------- deck slide 4, Opsi B (DDM) branch
def _synthetic_bank_payload_and_assumptions():
    """A deliberately synthetic dividend payer. The DDM branch is exercised on made-up inputs, never on
    a real issuer's numbers dressed up as a bank report."""
    import copy
    import json

    from server.routers.pdf import _build_live_payload

    payload = copy.deepcopy(_build_live_payload("AMMN", None))
    assum = json.loads(ASSUM_PATH.read_text(encoding="utf-8"))
    assum.update({"valuation_method": "ddm", "payout": 0.45, "cost_of_equity": 0.142, "g": 0.04,
                  "shares_out": 155_000_000_000, "last_price": 9_100})
    for row in payload["financial_statements"]["balance"]["rows"]:
        if str(row[0]).startswith("Shareholders"):
            row[1:] = ["200000", "210000", "220000", "230000", "240000", "250000"]
    for row in payload["financial_statements"]["ratios"]["rows"]:
        if str(row[0]).startswith("Return on Equity"):
            row[1:] = ["17.5", "18.0", "18.2", "18.4", "18.6", "18.8"]
    for row in payload["cover"]["slide2"]["key_financials"]["rows"]:
        if str(row[0]).lower().startswith("net profit"):
            row[1:] = ["32000", "34000", "36000", "38000", "40000"]
    return payload, assum


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_ddm_branch_builds_the_rows_the_rules_require() -> None:
    from server.report.house_rules import audit_valuation_page
    from server.report.valuation_page import build_valuation_page

    payload, assum = _synthetic_bank_payload_and_assumptions()
    page = build_valuation_page(payload, assum)
    assert page["method"] == "ddm" and page["available"]
    labels = [r[0] for r in page["block1_rows"]]
    for required in ("Net Profit (Rp bn)", "Payout Ratio (%)", "DPS (Rp)", "DPS growth (%)",
                     "Discount factor (Cost of Equity)", "PV of DPS"):
        assert required in labels, f"the DDM block 1 lost {required}"
    assert all(len(r[1]) == 5 for r in page["block1_rows"])
    # the discount rate is the cost of equity, and the page says so
    assert any("cost of equity" in r[0].lower() for r in page["wacc_rows"])
    assert "wacc" in page["subtitle"].lower()
    # both methods are shown side by side, never averaged
    bridge = page["bridge"]
    assert bridge["fv_gordon"] and bridge["fv_exit"]
    assert abs(bridge["fv_exit"] - bridge["fv_gordon"]) > 0
    assert page["sensitivity"]["fair_value"].shape == (5, 5)
    assert sum(1 for r in page["sensitivity"]["rows"] for c in r["cells"] if c["base"]) == 1
    assert any("payout" in str(n).lower() for n in page["notes"])
    assert page["narrative"] and "Cost of Equity" in page["narrative"][0] or "growth" in page["narrative"][0]
    assert audit_valuation_page(page, payload) == []


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_ddm_branch_refuses_instead_of_inventing_a_dividend() -> None:
    """AMMN pays no dividend. Forcing the bank path must produce a loud empty page, not numbers."""
    import json

    from server.report.valuation_page import build_valuation_page

    from server.routers.pdf import _build_live_payload

    assum = json.loads(ASSUM_PATH.read_text(encoding="utf-8"))
    assum["valuation_method"] = "ddm"
    page = build_valuation_page(_build_live_payload("AMMN", None), assum)
    assert page["available"] is False
    assert any("payout" in m.lower() for m in page["missing"])
    assert "block1_rows" not in page


# ------------------------------------------------- deck slide 4, Opsi C (RNAV) branch
def _synthetic_property_assumptions(assum: dict) -> dict:
    """A deliberately synthetic property issuer: NAV per aset, ownership, and a balance sheet at the
    scale of that issuer - never a real issuer's figures dressed up as a landbank story."""
    import copy

    prop = copy.deepcopy(assum)
    prop.update({
        "valuation_method": "rnav", "rnav_discount": 0.35, "shares_out": 14_000_000_000,
        "last_price": 1_250, "total_debt": 3_100_000_000_000, "cash": 1_450_000_000_000,
        "corporate_overhead_pv_bn": 620.0,
        "assets": [
            {"name": "Landbank Bogor (mature)", "size": 210, "size_unit": "ha", "nav_bn": 6_400,
             "ownership_pct": 100, "nav_source": "Sectors /company/get-segments + subsector report", "discount_rate": 0.11},
            {"name": "Landbank Karawang (development)", "size": 640, "size_unit": "ha", "nav_bn": 4_100,
             "ownership_pct": 70, "nav_source": "Sectors /company/report (segments)", "discount_rate": 0.145},
            {"name": "Proyek mixed-use (JV)", "size": 3.2, "size_unit": "ha", "nav_bn": 1_800,
             "ownership_pct": 45, "nav_source": "Sectors /companies (subsector)", "discount_rate": 0.13},
        ],
    })
    return prop


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_rnav_branch_values_assets_then_bridges_to_target_price() -> None:
    import json

    from server.report.house_rules import audit_valuation_page
    from server.report.valuation_page import build_valuation_page
    from server.routers.pdf import _build_live_payload

    assum = _synthetic_property_assumptions(json.loads(ASSUM_PATH.read_text(encoding="utf-8")))
    page = build_valuation_page(_build_live_payload("AMMN", None), assum)
    assert page["method"] == "rnav" and page["available"]
    assert len(page["block1_rows"]) == 3
    # attributable NAV = NAV x ownership, per the rules
    def parsed(cell: str) -> float:
        return float(cell.replace(".", "").replace(",", "."))

    nav = {r[0]: r[1] for r in page["block1_rows"]}
    assert parsed(nav["Landbank Karawang (development)"][3]) == pytest.approx(4100 * 0.70, abs=1)
    assert parsed(nav["Proyek mixed-use (JV)"][3]) == pytest.approx(1800 * 0.45, abs=1)
    bridge = page["bridge"]
    assert bridge["sum_nav"] == pytest.approx(6400 + 4100 * 0.70 + 1800 * 0.45, abs=1)
    assert bridge["target_price"] == pytest.approx(bridge["rnav_per_share"] * 0.65, abs=1)
    assert [r[0] for r in page["block3_rows"]][1].startswith("Target Price")
    assert len(page["sensitivity"]["rows"]) == 5
    assert sum(1 for r in page["sensitivity"]["rows"] for c in r["cells"] if c["base"]) == 1
    assert audit_valuation_page(page, page and _build_live_payload("AMMN", None)) == []


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_rnav_branch_refuses_without_asset_data() -> None:
    """AMMN has no asset-level NAV anywhere in Sectors: the branch must say what is missing, not invent it."""
    import json

    from server.report.valuation_page import build_valuation_page
    from server.routers.pdf import _build_live_payload

    assum = json.loads(ASSUM_PATH.read_text(encoding="utf-8"))
    assum["valuation_method"] = "rnav"
    page = build_valuation_page(_build_live_payload("AMMN", None), assum)
    assert page["available"] is False
    missing = " ".join(page["missing"]).lower()
    assert "asset" in missing and "nav" in missing
    assert "block1_rows" not in page


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_rnav_gate_demands_a_sourced_nav_and_a_justified_discount() -> None:
    import json

    from server.report.house_rules import audit_valuation_page
    from server.report.valuation_page import build_valuation_page
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    assum = _synthetic_property_assumptions(json.loads(ASSUM_PATH.read_text(encoding="utf-8")))
    page = build_valuation_page(payload, assum)
    assert audit_valuation_page(page, payload) == []

    # project rule: an unsourced NAV, or one taken from outside Sectors, is refused at the builder -
    # the page never reaches the renderer, so there is nothing for the gate to flag.
    for bad_source in (None, "appraisal KJPP, Jun 2026"):
        refused = build_valuation_page(payload, {**assum, "assets": [
            {**assum["assets"][0], "nav_source": bad_source}] + assum["assets"][1:]})
        assert refused["available"] is False, bad_source
        assert any("luar Sectors" in m or "outside Sectors" in m for m in refused["missing"]), bad_source

    # and if a page somehow reaches the gate with an outside-Sectors NAV, the gate still catches it
    tampered = build_valuation_page(payload, assum)
    tampered["assets"][0] = {**tampered["assets"][0], "nav_source": "broker estimate"}
    assert any("outside Sectors" in v for v in audit_valuation_page(tampered, payload))

    unjustified = build_valuation_page(payload, {**assum, "rnav_discount_comparables": None})
    unjustified["notes"] = [n for n in unjustified["notes"] if "judgment" not in n.lower()]
    assert any("pure judgment" in v or "comparable" in v for v in audit_valuation_page(unjustified, payload))


def test_the_target_price_basis_is_reconciled_when_the_dcf_and_the_anchor_differ():
    """A page may carry two prices on two bases; the reader must be told which one the target price uses.

    Ticker-agnostic on purpose: the guard is about the behaviour (the note fires on the gap), not about any one
    issuer's numbers, so it runs on invented prices.
    """
    from server.report.valuation_page import _notes

    def notes_for(gordon, anchor):
        primary = {"fv_gordon": gordon, "fv_exit": gordon * 7}
        return " ".join(_notes(primary, {"equity_gordon": 5.0e12}, 15.0, 9.0e13, 0.025, 0.1377,
                              {"ev_multiple_basis": "stub"}, anchor_fv=anchor))

    far = notes_for(100.0, 3000.0)
    assert "Target-price basis" in far, "a 30x gap between the DCF and the anchor is left unexplained"
    assert "3.000" in far and "100" in far, "the reconciliation does not name both prices"

    near = notes_for(3000.0, 3100.0)
    assert "BASIS TARGET PRICE" not in near, "the note fires even when the two bases agree"


# ------------------------------------------------- PLAIN-LANGUAGE RULE (owner: lay readers)
def _live_payload_for_plain():
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


def test_plain_language_gate_passes_on_the_live_payload():
    from server.report.house_rules import audit_plain_language

    assert audit_plain_language(_live_payload_for_plain()) == []


def test_plain_language_gate_names_the_surface_and_token():
    from server.report.house_rules import audit_plain_language

    payload = _live_payload_for_plain()
    payload["cover"]["slide1"]["highlights"][0] += " CAGR test"
    violations = audit_plain_language(payload)
    assert any("highlight 1" in v and "CAGR" in v for v in violations), violations


def test_plain_language_rule_is_ticker_agnostic():
    """A rule is a procedure, never one report's arithmetic: no company name,
    no company figure inside the rule text."""
    from agents.adk.agents import instructions as ins

    text = ins.writer_instruction
    start = text.index("PLAIN-LANGUAGE RULE")
    end = text.index("Emit thesis.json")
    block = text[start:end]
    for forbidden in ("AMMN", "Amman", "Rp ", "12.961", "5.667", "27,7", "33,9"):
        assert forbidden not in block, f"rule carries report arithmetic {forbidden!r}"


def test_adk_narrative_agents_carry_the_plain_language_rule():
    """Same shape as the page-2 runtime test: the instruction must reach the
    agents that write, and stay away from the ones that calculate."""
    import os

    from agents.adk.app import build_graph

    os.environ.setdefault("GOOGLE_API_KEY", "structure-only")
    os.environ.setdefault("DEEPSEEK_API_KEY", "structure-only")
    root = build_graph(ticker="AMMN")

    carried: dict[str, str] = {}

    def walk(agent) -> None:
        carried[str(getattr(agent, "name", "?"))] = str(getattr(agent, "instruction", "") or "")
        for sub in getattr(agent, "sub_agents", []) or []:
            walk(sub)

    walk(root)
    for name in ("writer", "critic"):
        assert name in carried, f"the ADK graph no longer builds a {name} agent"
        assert "PLAIN-LANGUAGE RULE" in carried[name], f"{name} does not receive the plain-language rule"
    for name in ("collector", "modeler"):
        assert "PLAIN-LANGUAGE RULE" not in carried[name], f"{name} calculates, it should not carry narrative rules"
