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
    for heading in ("## 7.", "## 8.", "## 9.", "## 10.", "## 11."):
        assert heading in text, f"rule doc is missing section {heading}"
    assert "2.600 characters" in text, "the copy budget must be stated in the rule doc"
    assert "Previous TP (Rp)" in text
    assert "Year to 31 Dec" in text


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
