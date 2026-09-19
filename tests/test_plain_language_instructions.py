"""The ADK agents get the plain-language rule as one shared, drift-proof instruction.

The owner's ask ("pastiin ADK agents di pipeline kita dikasih instruksi yang bener juga untuk
pake bahasa yang mudah dimengerti") is a roster question plus a sync question:

  * roster - every agent that writes or judges PRINTED prose carries the rule, and the pure
    data agents do not (they calculate; a narrative rule on them is noise that dilutes the
    agents that matter).
  * sync   - the rule's banned-token list is the same list the render gate enforces, so the
    instruction cannot promise one thing while the gate rejects another.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.adk.agents import instructions as I
from server.report.house_rules import PLAIN_JARGON, PLAIN_JARGON_PATTERNS, VALUASI_MANDATE_TOKENS

#: Agents that write or judge reader-facing prose. All of them must carry the rule.
MUST_CARRY = (
    "writer_instruction",
    "critic_instruction",
    "industry_instruction",
    "kpi_instruction",
    "analyst_instruction",
    "risk_instruction",
    "sotp_instruction",
)

#: Agents that gather, compute or design. They must NOT carry it: narrative rules on
#: calculators dilute the agents whose output actually reaches a reader.
MUST_NOT_CARRY = (
    "collector_instruction",
    "modeler_instruction",
    "news_harvester_instruction",
    "news_search_sub_instruction",
    "industry_search_sub_instruction",
    "visualizer_instruction",
    "adversarial_instruction",
)


def test_the_rule_exists_as_one_shared_constant() -> None:
    assert len(I.PLAIN_LANGUAGE_RULE) > 1500, "the rule is too thin to guide a writer"
    assert I.PLAIN_LANGUAGE_RULE.lstrip().startswith("PLAIN-LANGUAGE RULE")


@pytest.mark.parametrize("name", MUST_CARRY)
def test_agents_that_write_or_judge_prose_carry_the_rule(name: str) -> None:
    text = getattr(I, name)
    assert "PLAIN-LANGUAGE RULE" in text, f"{name} does not carry the plain-language rule"


@pytest.mark.parametrize("name", MUST_NOT_CARRY)
def test_data_agents_do_not_carry_a_narrative_rule(name: str) -> None:
    text = getattr(I, name)
    assert "PLAIN-LANGUAGE RULE" not in text, f"{name} calculates - it should not carry it"


def test_the_rule_and_the_render_gate_share_one_token_list() -> None:
    """Anti-drift: a token added to the gate must be added to the instruction, or agents get
    told one thing and rejected for another."""
    rule = I.PLAIN_LANGUAGE_RULE.lower()
    missing = sorted({t.strip().lower() for t in PLAIN_JARGON
                      if t.strip() and t.strip().lower() not in rule})
    assert missing == [], f"gate tokens missing from the agent rule: {missing}"


def test_the_rule_names_the_code_tags_the_gate_catches() -> None:
    assert len(PLAIN_JARGON_PATTERNS) == 2
    assert "FY26F" in I.PLAIN_LANGUAGE_RULE
    assert "Q1-2026" in I.PLAIN_LANGUAGE_RULE
    assert "2026-2028" in I.PLAIN_LANGUAGE_RULE, "the plain form must be shown, not just banned"


def test_the_rule_tells_agents_what_the_gate_enforces() -> None:
    assert "audit_plain_language" in I.PLAIN_LANGUAGE_RULE
    assert "REJECT" in I.PLAIN_LANGUAGE_RULE


def test_the_rule_does_not_claim_p3_is_exempt() -> None:
    """P3 joined the scan; the instruction must describe the carve-out, not an exemption."""
    rule = I.PLAIN_LANGUAGE_RULE
    assert "Exempt by design" not in rule
    for token in VALUASI_MANDATE_TOKENS:
        if token in ("CAGR", "FY26F-FY28F"):
            assert token in rule, f"the carve-out must name {token!r} explicitly"
    assert "BY NAME" in rule


def test_the_writer_keeps_no_second_copy_of_the_glossary() -> None:
    """One definition only: a duplicated glossary in the writer's body drifts from the shared
    rule the moment either is edited."""
    assert I.writer_instruction.count("CAGR -> tumbuh X% per tahun") == 1
    assert I.PLAIN_LANGUAGE_RULE.count("CAGR -> tumbuh X% per tahun") == 1


def test_the_critic_checklist_points_at_the_gate_and_the_carve_out() -> None:
    critic = I.critic_instruction
    assert "audit_plain_language" in critic
    assert "carved out BY NAME" in critic
    assert "kept in sync by a test" in critic


def test_the_rule_doc_states_the_roster_and_the_sync() -> None:
    """The binding doc, the instruction and the gate move together - the repo's convention."""
    doc = (REPO_ROOT / "docs" / "rules" / "house-report-format.md").read_text(encoding="utf-8")
    assert "## 14. Plain language" in doc
    section = doc.split("## 14. Plain language", 1)[1]
    for name in ("writer", "critic", "industry", "kpi", "analyst", "risk", "sotp"):
        assert name in section, f"{name} is missing from the doc's roster"
    assert "PLAIN_JARGON" in section and "VALUASI_MANDATE_TOKENS" in section
    assert "audit_plain_language" in section
