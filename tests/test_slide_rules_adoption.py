"""Adoption guards for the slide rules (docs/rules/house-report-format.md §7-§9).

The exhibit rules are renderer-owned, so they cannot be broken from the agent side. The slide
rules constrain CONTENT — the cover structure, the paragraph mandates, the Key Financials
contract and the one-page copy budget — and content is exactly what drifts silently. These
guards assert that the rule doc, the agent instructions, the shared validator and the Critic
gate all say the same thing, and that each violation class is actually caught.
"""
from __future__ import annotations

import copy
import json
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
    """One implementation, three callers — otherwise the gate and the render disagree."""
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
                    ["Previous TP (Rp)", "NA"],
                    ["Upside/Downside (%)", "+20,84%"],
                ]},
                "stats": {
                    "rows": [["No. of Shares (mn)", "72.518,2"],
                             ["Mkt Cap (Rpbn/US$mn)", "1/2"],
                             ["Free Float (%)", "26,37"]],
                    "major_shareholders": [{"name": "PT X", "pct_str": "32,17%"}],
                },
                "jci_chart": {"price": [1, 2, 3]},
                "analyst": {"name": "RESEARCH", "title": "Equity Analyst"},
                "theme_title": "Multiple 2026 di 17,99x vs mid-cycle 28,42x",
                "highlights": ["Laba Rp 2,72 tn (-61,95% qoq)", "Tembaga US$ 14.708/ton",
                               "TP Rp 5.873 (+20,84%)"],
                "financial_para": {"body": "Pendapatan Q1-2026 Rp 13,73 tn, -36,94% qoq."},
            },
            "slide2": {
                "katalis": {"body": (
                    "Katalis terverifikasi: (1) smelter selesai; Dampak: capex turun 69,6% qoq. "
                    "Dampak harga tembaga tidak dapat dikuantifikasi ke laba. "
                    "Priced-in: 24 bulan -33,40% relatif vs IHSG."
                )},
                "valuasi": {"body": (
                    "Kami menetapkan TP Rp 5.873 menggunakan EV/EBITDA. CAGR 0,0%. Pada TP, "
                    "saham dihargai 28,4x dibandingkan rata-rata historis 4 tahun 28,42x vs "
                    "subsector. Risiko terhadap pandangan ini: tembaga -10%."
                )},
                "key_financials": {
                    "headers": ["Year to 31 Dec", "2024A", "2025A", "2026F", "2027F", "2028F"],
                    "rows": [
                        ["Revenue (Rpbn)", "43.036", "30.904", "27.236", "27.236", "27.236"],
                        ["EBITDA (Rpbn)", "23.040", "16.410", "18.396", "18.396", "18.396"],
                        ["EBITDA Growth (%)", "n/a", "(28,8)", "12,1", "0,0", "0,0"],
                        ["Net Profit (Rpbn)", "10.290", "4.167", "7.004", "7.004", "7.004"],
                        ["EPS (Rp)", "141,9", "57,5", "96,6", "96,6", "96,6"],
                        ["EPS Growth (%)", "n/a", "(59,5)", "68,1", "0,0", "0,0"],
                        ["PER (x)", "34,2", "84,6", "50,3", "50,3", "50,3"],
                        ["PBV (x)", "3,8", "3,8", "3,8", "3,8", "3,8"],
                        ["EV/EBITDA (x)", "19,5", "27,4", "24,4", "24,4", "24,4"],
                    ],
                    "notes": ["Asumsi kolom F: ..."],
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
    """The shipped cover must pass the same audit the gate runs — this is the regression line
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
    split matters — a style/content defect must be visible, not fatal."""
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
    "1. Kondisi Industri",
    "2. Katalis Spesifik Emiten",
    "3. Sentimen Pasar",
)
SLIDE2_AGENTS = (
    "industry_instruction",
    "news_harvester_instruction",
    "social_sentiment_instruction",
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
    assert "Posisi relatif" in page["paragraphs"][0]["body"]
    assert "90 hari" in page["paragraphs"][2]["body"]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_industry_page_is_honest_about_what_the_data_does_not_carry() -> None:
    """No tonnage/grade/C1 in the payload and no rating endpoint: both must be named in the copy
    rather than replaced with a plausible figure."""
    from server.routers.pdf import _build_live_payload

    page = _build_live_payload("AMMN", None)["industry_page"]
    p1, p3 = page["paragraphs"][0]["body"], page["paragraphs"][2]["body"]
    assert "tidak dapat" in p1 and "C1" in p1
    assert "tidak tersedia" in p3 and "tidak diada-adakan" in p3
    assert "tidak diekstrapolasi" in p3


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
    assert any("3. Sentimen Pasar" in v for v in audit_industry_page(missing))

    empty = copy.deepcopy(clean)
    empty["paragraphs"][0]["body"] = "   "
    assert any("has no body" in v for v in audit_industry_page(empty))

    leaky = copy.deepcopy(clean)
    leaky["paragraphs"][2]["body"] = "Kami menetapkan TP Rp 5.873 dari EV/EBITDA 28,42x (WACC 13,77%)."
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
    assert "Kondisi Industri, Katalis" in html  # autoescape turns the "&" into "&amp;"
    for heading in SLIDE2_PARAGRAPHS:
        assert heading in html, f"{heading} is not rendered"
    assert html.index("Kondisi Industri, Katalis") < html.index("Ringkasan Investasi")
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
    assert "transaksi beli" in body and "transaksi jual" in body
    assert "tidak didukung datanya" in body, "the page must say the one-sided read is unsupported"
    assert "Neto" in body and "bukan angka yang" in body, "the summed net must be labelled a sum"


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_slide2_uses_the_wider_sectors_evidence() -> None:
    """Page 2 reads the subsector report, the IDX filings, corporate actions, the monthly ownership
    composition and the free-float screener — not only the four headline catalysts."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    for block in ("sector_data", "filings_digest", "corporate_actions", "ownership_mix", "free_float"):
        assert payload.get(block), f"{block} missing from the filled payload"
    body = " ".join(p["body"] for p in payload["industry_page"]["paragraphs"])
    assert "Proyeksi Sectors" in body, "the subsector report is not used"
    assert "keterbukaan IDX" in body, "the filings digest is not used"
    assert "RUPS" in body, "corporate actions are not used"
    assert "kepemilikan asing" in body, "the ownership composition is not used"
    assert "free float" in body, "the free-float screener is not used"
    assert len(payload["industry_page"]["sources"]) >= 5, payload["industry_page"]["sources"]


@pytest.mark.skipif(not ASSUM_PATH.exists(), reason="AMMN assumptions file absent")
def test_slide2_single_year_comparison_is_not_a_cumulative_move() -> None:
    """The positioning line compares one-year growth with a one-year forecast. A five-year
    cumulative move beside a forecast would flatter the issuer, so guard the choice."""
    from server.routers.pdf import _build_live_payload

    body = _build_live_payload("AMMN", None)["industry_page"]["paragraphs"][0]["body"]
    assert "pertumbuhan pendapatan tahun terakhir" in body
    assert "(aktual, tahun terakhir vs sebelumnya)" in body
    assert "periodenya berbeda" in body


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
                {"heading": "1. Kondisi Industri", "body": "x" * 250},
                {"heading": "2. Katalis Spesifik Emiten", "body": catalysts_body},
                {"heading": "3. Sentimen Pasar", "body": "y" * 250},
            ]
        }

    payload = {"filings_digest": {"buy": {"n": 11}, "sell": {"n": 9}}}
    one_sided = audit_industry_page(page("hanya transaksi beli insider yang disebut"), payload)
    assert any("omits related-party 'jual'" in v for v in one_sided), one_sided
    assert audit_industry_page(page("transaksi beli dan jual dua-duanya disebut"), payload) == []
    # an absent digest cannot trigger the check: the copy's missing-data line covers that case
    assert audit_industry_page(page("hanya transaksi beli insider yang disebut"), {}) == []


def test_cli_pipeline_builds_and_audits_the_page() -> None:
    """`scripts/render_pdf.py` renders whatever payload it is handed, so it must attach the page
    and run the same audit instead of rendering a payload that predates the slide rules."""
    import json
    import sys as _sys

    _sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import render_pdf

    payload = json.loads(
        (REPO_ROOT / "output" / "cache" / "render_ammn" / "report_data.json").read_text(
            encoding="utf-8"
        )
    )
    payload.pop("industry_page", None)  # a payload that predates the page, whatever the cache holds
    render_pdf.ensure_industry_page(payload)
    assert [p["heading"] for p in payload["industry_page"]["paragraphs"]] == list(SLIDE2_PARAGRAPHS)
    assert render_pdf.validate(payload) == []

    # and it must refuse a payload whose page breaks the rules
    broken = json.loads(json.dumps(payload))
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
    for name in ("news_harvester", "social_sentiment", "industry", "writer", "critic"):
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
        if text in ("", "—", "n/a"):
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
    assert 'pattern id="fc-1"' in html, "no forecast hatch pattern in the markup"
    assert "opacity=\"0.3\"" in html, "forecast bars are not drawn lighter than actual bars"
    quad = payload["performance_page"]["quadrants"][0]
    assert quad["actual_n"] == 2 and len(quad["labels"]) == 5
    assert "Bentuk: 3 periode proyeksi" not in html  # guard against a stale caption
