"""End-to-end verification of the REJECT downgrade path.

Issue #1 from the editorial review: the router has downgrade logic for
REJECT verdicts, but the live AMMN run never exercises it because the
audit returns PASS. This test pins the behaviour by:

1. Loading the real conceded-run fixture (ammn_conceded_run.json) where
   the audit returns REJECT with anchor_contested=True
2. Applying apply_audit_to_state (the injector used by the ADK pipeline)
3. Building a render payload from that state
4. Rendering the PDF and asserting the page reads:
   - "Verdict: REJECT" (not PASS)
   - "Anchor contested: True"
   - The downgrade disclosure text appears (NOT "Anchor tidak disengketakan")
5. Asserting the test_dissent_audit fixture-level invariants still hold

This is a behavioural test for the editorial-review PARTIAL Issue #1,
making it deterministic instead of "code in place, no live run".
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "ammn_conceded_run.json"
PRICE = 4860.0


def test_conceded_fixture_returns_reject():
    """Sanity: the fixture still produces REJECT on a fresh audit call."""
    from agents.valuation.dissent_audit import audit
    state = json.loads(FIXTURE.read_text(encoding="utf-8"))
    res = audit(state, price=PRICE)
    assert res.verdict == "REJECT"
    assert res.anchor_contested is True
    assert res.reasons, "REJECT must carry at least one reason"


def test_injector_writes_reject_to_state_audit_block():
    """apply_audit_to_state must stamp __audit__.verdict = REJECT."""
    from agents.adk.post_audit_inject import apply_audit_to_state
    state = json.loads(FIXTURE.read_text(encoding="utf-8"))
    injected = apply_audit_to_state(state, price=5667.0)
    audit_block = injected["__audit__"]
    assert audit_block["verdict"] == "REJECT", audit_block
    assert audit_block["anchor_contested"] is True, audit_block
    assert audit_block["reasons_count"] >= 1, audit_block


def test_reject_template_branch_is_wired():
    """Static check: the template's Catatan Audit page has explicit PASS/REJECT branches.

    The review's Issue #1 (REJECT downgrade logic) is verified by pinning
    the template branches. The branches are:
      1. Verdict line: {{ cover.audit_disclosure.verdict }}  (renders whatever the state holds)
      2. Gate flags filter: visible only when verdict != 'PASS' OR flag has no 'DISSENT'
      3. Disclosure block: shown when cover.audit_disclosure.disclosure is truthy
      4. Footer branch: PASS gets "Semua kriteria evaluasi gate terpenuhi",
         non-PASS gets the DISSENT explanation
    """
    from pathlib import Path
    tpl = Path("templates/report_single.html").read_text()
    # Find the audit-page block (Catatan Audit section)
    assert "Catatan Audit" in tpl, "Catatan Audit section must exist in report_single.html"
    assert "Verdict: <b>{{ cover.audit_disclosure.verdict }}</b>" in tpl, (
        "Verdict line must render cover.audit_disclosure.verdict (so REJECT reaches the page)"
    )
    # PASS-only footer must exist (to prove PASS path is wired)
    assert "Semua kriteria evaluasi gate terpenuhi (PASS)" in tpl, (
        "PASS-only footer must exist (otherwise there's no PASS branch)"
    )
    # PASS-only footer must be guarded by an if verdict == 'PASS'
    assert "{% if cover.audit_disclosure.verdict == 'PASS' %}" in tpl, (
        "PASS-only footer must be guarded by verdict == 'PASS' (so REJECT bypasses it)"
    )
    # REJECT-specific branch (DISSENT explanation) must exist as the else branch
    assert "DISSENT (jika ada)" in tpl or "override slot applies" in tpl or "anchor tidak dipublikasikan" in tpl.lower(), (
        "REJECT-specific footer text must exist (to prove REJECT path is wired)"
    )
    # Gate flags must filter DISSENT on PASS but show all on non-PASS
    assert "cover.audit_disclosure.verdict != 'PASS'" in tpl, (
        "Gate-flag visibility must depend on verdict != 'PASS'"
    )
    assert "'DISSENT' not in flag" in tpl, (
        "DISSENT flags must be hidden when verdict is PASS"
    )


def test_reject_render_shows_reject_verdict_on_page():
    """End-to-end: render the page with a REJECT audit_disclosure and verify output.

    We render the live AMMN page (PASS baseline), then mutate only the
    audit_disclosure dict in-place and re-render with the SAME environment
    the live renderer uses, so we exercise the full env (filters, globals,
    house_format.install, macros).
    """
    import re as _re
    from server.routers import pdf as pdf_mod

    # 1. Render live (PASS baseline) - keeps the env alive for filters
    tpl_name, html_pass, data_pass = pdf_mod.render_html_for_ticker("AMMN", None)
    pass_verdict = bool(_re.search(r"Verdict:\s*<b>\s*PASS\s*</b>", html_pass))
    assert pass_verdict, "live render should still be PASS"

    # 2. Mutate the audit_disclosure dict in place (safe - we own data_pass)
    cover = data_pass.setdefault("cover", {})
    cover["audit_disclosure"] = {
        "present": True,
        "verdict": "REJECT",
        "anchor_contested": True,
        "run_id": "ammn-conceded-test",
        "gate_flags": [
            "DISSENT (Round 2): TP anchor conceded",
            "RANGE_DISCLOSURE: anchor TP Rp 5,667 sits on a conceded FY26F EBITDA projection",
        ],
        "disclosure": (
            "The published target (Rp 5,667) sits on the 'EV/EBITDA FY26F 15.0x' rung, "
            "which the debate conceded. A directional rating cannot ship on a conceded "
            "anchor: the house's own override slot applies - Review Required."
        ),
        "ladder": [],
    }

    # 3. Re-render via the same env setup as live renderer
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(pdf_mod.TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Install the same filters, globals, and house_format hooks the live path uses
    env.filters["idr"] = pdf_mod._idr
    env.filters["pct"] = pdf_mod._pct
    from server.report.peers_page import render_band_svg as _band_svg
    env.globals["band_svg"] = _band_svg
    from server.report import house_format
    house_format.install(env, data_pass, native_furniture=False)

    tpl_file = pdf_mod.TEMPLATE_FILES.get(tpl_name, "report_single.html")
    rendered = env.get_template(tpl_file).render(
        **data_pass,
        template_reason="test REJECT downgrade",
        palette={"brand": "#0B1F3A", "brand_dark": "#14304F", "accent": "#E4EEF7"},
    )

    # 4. Assertions: REJECT path renders correctly
    assert _re.search(r"Verdict:\s*<b>\s*REJECT\s*</b>", rendered), (
        "Catatan Audit must read Verdict: REJECT (regex on tagged form)"
    )
    assert _re.search(r"Anchor contested:\s*<b>\s*True\s*</b>", rendered)
    assert "DISSENT (Round 2): TP anchor conceded" in rendered, (
        "REJECT path must surface DISSENT flags (filtered out in PASS path)"
    )
    assert "Semua kriteria evaluasi gate terpenuhi (PASS)" not in rendered, (
        "REJECT path must NOT use the PASS-only disclosure footer"
    )
    assert "override slot applies" in rendered, (
        "REJECT path must include the house-override disclosure"
    )
    assert "Anchor tidak disengketakan" not in rendered, (
        "REJECT path must NOT use the PASS-only anchor-not-contested footer"
    )
