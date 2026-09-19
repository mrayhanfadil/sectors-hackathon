"""Paragraph 2 as written prose: the fact sheet, the freeze contract, the gate.

The section is the one place where a language model writes reader-facing copy, so the
tests here are about the two things that can go wrong and neither is style:

  * the prose prints a figure the fact sheet never carried (fabrication), and
  * the prose is not prose at all - a planning dump frozen as if it were the paragraph.

Everything else (jargon, plumbing words, deck self-reference, page budget) is enforced
by `server.report.house_rules.audit_katalis_narrative`, which these tests exercise both
ways: a good narrative passes, and each named failure class fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.report import narrative_facts as nf  # noqa: E402
from server.report.house_rules import (NARRATIVE_MAX_CHARS, audit_house_rules,  # noqa: E402
                                       audit_katalis_narrative)
from server.report.slide2 import build_katalis  # noqa: E402


def _facts() -> dict:
    payload = {
        "meta": {"ticker": "TEST"},
        "catalysts": [
            {"name": "Direksi membeli saham serentak Jul-2026",
             "quantified": {"shares": "+12.961.700", "avg_price": "Rp 3.548"},
             "effect": "tanda orang dalam yakin", "source": "IDX keterbukaan via Sectors filings"},
        ],
        "cover": {"slide1": {"jci_chart": {"rel_pct": [-33.40], "abs_chg_pct": -47.03,
                                           "idx_chg_pct": -13.63}},
                  "vs_jci": {"note": "90d X +28,57% vs IHSG +4,58% (rel +23,99 pp)"},
                  # EV/EBITDA lands on 18,38 so the fixture's prose can quote it
                  "meta": {"net_debt_after_cash": 1.0e9, "ebitda_ttm": 1.9708e13}},
        "canonical_metrics": {"market_cap_rpbn": {"value": 362235.7}},
    }
    return nf.build_katalis_facts(payload, payload["cover"]["slide1"]["jci_chart"])


def _written(body: str, facts: dict) -> dict:
    return {"narrative_source": "writer_frozen", "body": body,
            "narrative_provenance": {"allowed_numbers": sorted(nf.fact_numbers(facts))}}


GOOD = ("Manajemen membeli saham sendiri pada Juli 2026 - 12.961.700 lembar di harga rata-rata "
        "Rp 3.548, tanda orang dalam yakin pada prospek perusahaan. Katalis lain: harga tembaga "
        "dunia naik ke rekor. Priced-in: EV/EBITDA pasar kini 18,38 kali, masih di bawah "
        "rata-rata 4 tahun 28,42 kali.")


# --------------------------------------------------------------------------- fact sheet

def test_fact_sheet_hands_over_statements_not_bare_pairs():
    """A sheet of bare key/value pairs invites a writer to recombine them into a claim
    the data never made. The writer-facing half carries complete sentences only."""
    facts = _facts()
    assert facts["catalysts"] and all("detail" in c and "quantified" not in c
                                      for c in facts["catalysts"])
    assert facts["impact_statements"] and all(len(s) > 30 for s in facts["impact_statements"])
    assert facts["priced_in_statements"]
    assert "impact" not in facts          # raw pairs are behind facts["raw"]
    assert facts["raw"]["impact"]["capex_from"] == "Rp 5,26 tn"


def test_fact_numbers_cover_what_the_template_prints():
    facts = _facts()
    allowed = nf.fact_numbers(facts)
    for token in ("5,26", "1,60", "12.961.700", "3.548", "18,38", "28,42", "23,99"):
        assert token in allowed, token


# --------------------------------------------------------------------------- freeze contract

def test_no_frozen_narrative_uses_the_template(tmp_path, monkeypatch):
    monkeypatch.setattr(nf, "NARRATIVE_DIR", tmp_path)
    facts = _facts()
    assert nf.load_frozen_narrative("TEST", facts) is None
    out = build_katalis({"meta": {"ticker": "TEST"}, "catalysts": []})
    assert out["narrative_source"] == "template_fallback"


def test_frozen_narrative_is_used_only_while_the_facts_match(tmp_path, monkeypatch):
    monkeypatch.setattr(nf, "NARRATIVE_DIR", tmp_path)
    facts = _facts()
    doc = {"section": "katalis", "ticker": "TEST", "paragraphs": [GOOD],
           "facts_hash": nf.facts_hash(facts), "generated_by": "test", "model": "test"}
    nf.narrative_path("TEST", "katalis").write_text(json.dumps(doc), encoding="utf-8")

    loaded = nf.load_frozen_narrative("TEST", facts)
    assert loaded and loaded["body"] == GOOD

    # Same artifact, different facts: stale by definition, so it must not be used.
    other = dict(facts)
    other["raw"] = {**facts["raw"], "ev_ebitda_market": "19,99"}
    assert nf.load_frozen_narrative("TEST", other) is None


def test_live_render_path_agrees_with_the_freeze_contract(tmp_path, monkeypatch):
    """Regression: the runner once derived its own fact sheet, got a different hash than the
    render path (the render strips the internal gap code), and every frozen narrative was
    silently ignored. The render path now publishes the sheet it used, and this pins that a
    narrative frozen against THAT sheet is picked up."""
    from server.routers.pdf import _build_live_payload

    monkeypatch.setattr(nf, "NARRATIVE_DIR", tmp_path)
    payload = _build_live_payload("AMMN", None)
    katalis = payload["cover"]["slide2"]["katalis"]
    assert katalis.get("facts") and katalis.get("facts_hash"), "render path must publish its sheet"

    doc = {"section": "katalis", "ticker": "AMMN", "paragraphs": [GOOD],
           "facts_hash": katalis["facts_hash"], "generated_by": "test", "model": "test"}
    nf.narrative_path("AMMN", "katalis").write_text(json.dumps(doc), encoding="utf-8")

    assert nf.load_frozen_narrative("AMMN", katalis["facts"]) is not None
    assert nf.load_frozen_narrative("AMMN", nf.build_katalis_facts(payload, None)) is None, \
        "a re-derived sheet must NOT be treated as the renderer's sheet"


# --------------------------------------------------------------------------- the gate

def test_gate_ignores_the_template_path():
    assert audit_katalis_narrative({"narrative_source": "template_fallback",
                                    "body": "anything"}) == []


def test_gate_accepts_a_narrative_inside_its_fact_sheet():
    facts = _facts()
    assert audit_katalis_narrative(_written(GOOD, facts)) == []


def test_gate_rejects_an_invented_figure():
    """The whole point: a writer that prints a number the sheet never carried cannot ship."""
    facts = _facts()
    out = audit_katalis_narrative(_written(GOOD + " Laba naik Rp 9,99 tn.", facts))
    assert any("not in the fact sheet" in v and "9,99" in v for v in out), out


def test_gate_rejects_method_jargon():
    facts = _facts()
    out = audit_katalis_narrative(_written(GOOD + " Capex turun tajam.", facts))
    assert any("method jargon" in v for v in out), out


def test_gate_rejects_deck_talk_and_pipeline_plumbing():
    facts = _facts()
    out = audit_katalis_narrative(_written(GOOD + " Di slide ini, payload kami bersih.", facts))
    assert any("talks about the deck" in v for v in out), out
    assert any("pipeline plumbing" in v for v in out), out


def test_gate_rejects_a_narrative_over_the_page_budget():
    facts = _facts()
    long_body = GOOD + " " + ("kata " * 300)
    out = audit_katalis_narrative(_written(long_body, facts))
    assert any("over the" in v for v in out), out
    assert len(GOOD) < NARRATIVE_MAX_CHARS


def test_gate_rejects_a_written_narrative_without_the_priced_in_mandate():
    """The mandate lives in `audit_katalis` (it runs on whichever body the payload has),
    and the written narrative is no exception."""
    from server.report.house_rules import audit_katalis

    body = GOOD.replace("Priced-in: EV/EBITDA pasar kini 18,38 kali, masih di bawah "
                        "rata-rata 4 tahun 28,42 kali.", "")
    assert any("priced the" in v for v in audit_katalis(body)), audit_katalis(body)
    # and the section still has to be about the period's catalysts: the check asks whether
    # the copy mentions one of them, not whether it prints the literal word "Katalis"
    facts = _facts()
    written = _written(GOOD, facts)
    written["narrative_provenance"]["catalyst_names"] = ["Dana asing lewat indeks GDX"]
    out = audit_katalis_narrative(written)
    assert any("mentions none of the period's catalysts" in v for v in out), out
    # ... and a narrative that does mention one passes that arm
    written["body"] = GOOD + " Dana asing lewat indeks GDX masuk kembali."
    assert not any("mentions none" in v for v in audit_katalis_narrative(written))


def test_gate_refuses_to_run_without_the_fact_sheet_numbers():
    """No allowed-number list means the anti-fabrication check cannot run - that is a
    violation, not a pass: a missing check must never read as compliance."""
    out = audit_katalis_narrative({"narrative_source": "writer_frozen", "body": GOOD,
                                   "narrative_provenance": {}})
    assert any("anti-fabrication check cannot run" in v for v in out), out


# --------------------------------------------------------------------------- the parser

def test_parser_accepts_the_instructed_json():
    from agents.adk.narrative_runner import parse_paragraphs

    raw = 'Here you go:\n{"paragraphs": ["' + GOOD + '"]}\n'
    assert parse_paragraphs(raw) == [GOOD]


def test_parser_accepts_clean_prose():
    from agents.adk.narrative_runner import parse_paragraphs

    assert parse_paragraphs(GOOD) == [GOOD]


def test_parser_refuses_a_planning_dump():
    """Regression: a 28k planning dump once passed a looser parser and reached the gate
    as if it were the paragraph. Character-count bookkeeping is not copy."""
    from agents.adk.narrative_runner import parse_paragraphs

    dump = ("Paragraph 1: ... (1.137 chars)\n\n- bullet one\n- bullet two\n\n"
            "Total: 1.255 chars\n" + ("planning text " * 900))
    assert parse_paragraphs(dump) == []


def test_parser_refuses_a_refusal():
    from agents.adk.narrative_runner import parse_paragraphs

    assert parse_paragraphs("I cannot write this section without more data.") == []


# --------------------------------------------------------------------------- shipped deck

def test_shipped_payload_passes_with_either_path():
    """Whatever path the payload took (frozen prose or template), the deck's own gate is
    green and the copy still fits the one-page budget."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    audit = audit_house_rules(payload)
    assert audit["ok"], audit["violations"][:4]
    assert audit["copy_chars"] <= audit["copy_budget"]
    assert payload["cover"]["slide2"]["katalis"]["narrative_source"] in (
        "template_fallback", "writer_frozen")
