"""Slide 6 - statements page: the rule's structure, the tie-outs, and the disclosures that keep it honest."""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "ammn-slides" / "slide6-statements-spec.md"
PARTIAL = ROOT / "templates" / "_slide6_statements.html"
SINGLE = ROOT / "templates" / "report_single.html"
INSTRUCTIONS = ROOT / "agents" / "adk" / "agents" / "instructions.py"

YEARS = ["2024A", "2025A", "2026F", "2027F", "2028F"]


def _page():
    from server.report.statements_page import build_statements_page
    from server.routers.pdf import render_html_for_ticker

    _t, _h, payload = render_html_for_ticker("AMMN", None)
    spine = ((payload.get("cover") or {}).get("slide2") or {}).get("key_financials")
    return build_statements_page("AMMN", spine), payload


@pytest.fixture(scope="module")
def page_payload():
    page, payload = _page()
    if not page.get("available"):
        pytest.skip(f"statements page unavailable: {page.get('reason')}")
    return page, payload


def rows(page, block):
    """Key by the rule's own row name: strip the parenthetical tails the page adds."""
    def norm(label: str) -> str:
        return str(label).split(" -")[0].split(" / ")[0].split(" (")[0].strip()

    out = {}
    for r in page[block]["rows"]:
        if r.get("kind") == "section":
            continue
        out[str(r["label"])] = r
        out.setdefault(norm(r["label"]), r)
    return out


# ------------------------------------------------------------------ structure
def test_columns_are_the_five_the_rule_names(page_payload):
    page, _ = page_payload
    assert page["years"] == YEARS
    for block in ("income", "balance"):
        assert page[block]["headers"][1:] == YEARS
        for r in page[block]["rows"]:
            assert len(r["cells"]) == 5, r["label"]


def test_income_statement_row_order_and_kinds(page_payload):
    page, _ = page_payload
    labels = [r["label"] for r in page["income"]["rows"]]
    order = ["Revenue / Sales", "Beban pokok pendapatan", "Laba kotor", "Beban usaha & operasional",
             "Laba usaha (EBIT)", "Pendapatan bunga", "Beban bunga", "Pendapatan/(beban) non-operasional lainnya", "Laba sebelum pajak",
             "Beban pajak penghasilan", "Kepentingan non-pengendali", "Laba bersih periode berjalan"]
    positions = []
    for want in order:
        hit = next((i for i, l in enumerate(labels) if l.startswith(want)), None)
        assert hit is not None, f"missing row {want}"
        positions.append(hit)
    assert positions == sorted(positions), f"row order drifted: {labels}"
    r = rows(page, "income")
    for label in ("Laba kotor", "Laba usaha (EBIT)", "Laba sebelum pajak"):
        assert r[label]["kind"] == "subtotal", label
    assert r["Laba bersih periode berjalan"]["kind"] == "highlight"
    for label in ("Beban pokok pendapatan", "Beban usaha & operasional", "Beban bunga", "Beban pajak penghasilan"):
        assert r[label]["kind"] == "deduction", label


def test_balance_sheet_rows_and_sections(page_payload):
    page, _ = page_payload
    labels = [r["label"] for r in page["balance"]["rows"]]
    for want in ("Cash & Cash Equivalents", "Trade Receivables", "Inventory", "Other Current Assets",
                 "Total Current Assets", "Fixed Assets", "Other Non-Current Assets", "Total Assets",
                 "Short-term Debt", "Trade Payables", "Other Current Liabilities",
                 "Total Current Liabilities", "Long-term Debt", "Other Non-Current Liabilities",
                 "Total Liabilities", "Shareholders' Equity", "Total Liabilities & Equity"):
        assert any(l.startswith(want) for l in labels), f"missing row {want}"
    kinds = {r["label"]: r["kind"] for r in page["balance"]["rows"]}
    assert kinds.get("Total Liabilities & Equity") == "subtotal"
    section_rows = [r for r in page["balance"]["rows"] if r["kind"] == "section"]
    assert [s["label"] for s in section_rows][:2] == ["ASSETS", "LIABILITIES & EQUITY"]


# ------------------------------------------------------------------ arithmetic
def test_income_statement_foots_vertically_in_every_column(page_payload):
    page, _ = page_payload
    r = rows(page, "income")
    for i in range(5):
        rev, cogs, gp = r["Revenue / Sales"]["cells"][i], r["Beban pokok pendapatan"]["cells"][i], r["Laba kotor"]["cells"][i]
        opex, ebit = r["Beban usaha & operasional"]["cells"][i], r["Laba usaha (EBIT)"]["cells"][i]
        ie, other, ebt = r["Beban bunga"]["cells"][i], r["Pendapatan/(beban) non-operasional lainnya"]["cells"][i], r["Laba sebelum pajak"]["cells"][i]
        tax, mino, net = r["Beban pajak penghasilan"]["cells"][i], r["Kepentingan non-pengendali"]["cells"][i], r["Laba bersih periode berjalan"]["cells"][i]
        assert gp == pytest.approx(rev - cogs, abs=1.0), f"gross profit does not foot in {YEARS[i]}"
        assert ebit == pytest.approx(gp - opex, abs=1.0), f"EBIT does not foot in {YEARS[i]}"
        assert ebt == pytest.approx(ebit - ie + other, abs=1.0), f"pre-tax does not foot in {YEARS[i]}"
        assert net == pytest.approx(ebt - tax - mino, abs=1.0), f"net profit does not foot in {YEARS[i]}"


def test_balance_sheet_ties_exactly_and_the_tie_is_reported(page_payload):
    page, _ = page_payload
    r = rows(page, "balance")
    for i, y in enumerate(YEARS):
        ta = r["Total Assets"]["cells"][i]
        tle = r["Total Liabilities & Equity"]["cells"][i]
        assert ta == pytest.approx(tle, abs=0.01), f"balance sheet does not tie in {y}"
        assert abs(page["tie_out"][y]) < 0.01
    assert page["tied"] is True


def test_balance_sheet_subtotals_foot(page_payload):
    page, _ = page_payload
    r = rows(page, "balance")
    for i in range(5):
        ca = (r["Cash & Cash Equivalents"]["cells"][i] + r["Inventory"]["cells"][i]
              + r["Other Current Assets"]["cells"][i])
        assert r["Total Current Assets"]["cells"][i] == pytest.approx(ca, abs=1.0)
        cl = (r["Short-term Debt"]["cells"][i] + r["Other Current Liabilities"]["cells"][i])
        assert r["Total Current Liabilities"]["cells"][i] == pytest.approx(cl, abs=1.0)
        tl = (r["Total Current Liabilities"]["cells"][i] + r["Long-term Debt"]["cells"][i]
              + r["Other Non-Current Liabilities"]["cells"][i])
        assert r["Total Liabilities"]["cells"][i] == pytest.approx(tl, abs=1.0)
        assert r["Total Assets"]["cells"][i] == pytest.approx(
            r["Total Current Assets"]["cells"][i] + r["Fixed Assets (Net)"]["cells"][i]
            + r["Other Non-Current Assets"]["cells"][i], abs=1.0)


def test_forecasts_tie_to_the_deck_spine(page_payload):
    page, payload = page_payload
    spine = payload["cover"]["slide2"]["key_financials"]["rows"]
    def spine_nums(prefix):
        row = next(r for r in spine if str(r[0]).lower().startswith(prefix) and "growth" not in str(r[0]).lower())
        return [float(str(v).replace(".", "").replace(",", ".")) for v in row[3:]]
    rev = spine_nums("revenue")
    net = spine_nums("net profit")
    r = rows(page, "income")
    for i in range(3):
        assert r["Revenue / Sales"]["cells"][2 + i] == pytest.approx(rev[i], abs=1.0)
        assert r["Laba bersih periode berjalan"]["cells"][2 + i] == pytest.approx(net[i], abs=1.0)


def test_ebitda_implied_by_the_statement_matches_the_deck_number(page_payload):
    """EBIT + D&A must land on the spine's mid-cycle EBITDA, or the page contradicts the valuation."""
    page, payload = page_payload
    r = rows(page, "income")
    spine = payload["cover"]["slide2"]["key_financials"]["rows"]
    ebitda_row = next(x for x in spine if str(x[0]).lower().startswith("ebitda")
                      and "growth" not in str(x[0]).lower())
    ebitda_spine = float(str(ebitda_row[3]).replace(".", "").replace(",", "."))
    dna = None
    for note in page["notes"]:
        if "D&A" in note:
            from tests.idn_number import to_float

            dna = to_float(note.split("D&A Rp ")[1].split(" bn")[0])
    assert dna, "the page must state the D&A driver it uses"
    assert (r["Laba usaha (EBIT)"]["cells"][2] + dna) == pytest.approx(ebitda_spine, rel=0.01)


# ------------------------------------------------------------------ disclosure
def test_unpublished_rows_are_marked_and_explained(page_payload):
    page, _ = page_payload
    na_rows = [r for block in ("income", "balance") for r in page[block]["rows"] if r["kind"] == "na"]
    assert na_rows, "the page must keep the rows Sectors cannot fill, not drop them"


def test_notes_disclose_the_residual_the_plug_and_the_margin_implication(page_payload):
    page, _ = page_payload
    blob = " ".join(page["notes"]).lower()
    for marker, why in (("rekonsiliasi", "the other-income residual"),
                        ("penyeimbang", "cash as the balance-sheet plug"),
                        ("dipublikasikan", "rows Sectors does not publish"),
                        ("gross margin", "the COGS balancing line and its margin implication")):
        assert marker in blob, f"notes do not disclose {why}"


# ------------------------------------------------------------------ gate
def test_gate_passes_and_bites(page_payload):
    import copy

    from server.report.house_rules import audit_statements_page

    page, _ = page_payload
    assert audit_statements_page(page) == []

    rows_in = page["income"]["rows"]
    mutations = {
        "drop net profit": lambda d: d["income"].__setitem__(
            "rows", [r for r in rows_in if not r["label"].startswith("Laba bersih periode berjalan")]),
        "reorder income rows": lambda d: d["income"].__setitem__("rows", list(reversed(rows_in))),
        "unflag the net profit highlight": lambda d: [r.__setitem__("kind", "") for r in d["income"]["rows"]
                                                      if r["label"].startswith("Laba bersih periode berjalan")],
        "stop treating cogs as a deduction": lambda d: [r.__setitem__("kind", "") for r in d["income"]["rows"]
                                                        if r["label"].startswith("Beban pokok pendapatan")],
        "break the balance tie": lambda d: d["balance"]["rows"][-1].__setitem__(
            "cells", [c * 1.01 for c in d["balance"]["rows"][-1]["cells"]]),
        "silence the notes": lambda d: d.__setitem__("notes", []),
        "wrong column set": lambda d: d.__setitem__("years", ["2024A", "2025A", "2026F"]),
    }
    for label, mutate in mutations.items():
        d = copy.deepcopy(page)
        mutate(d)
        assert audit_statements_page(d), f"the gate failed to catch: {label}"


def test_unavailable_page_is_loud_and_absent_page_is_not_applicable():
    from server.report.house_rules import audit_statements_page

    assert audit_statements_page({"available": False, "reason": "no annual rows"})
    assert audit_statements_page(None) == []


# ------------------------------------------------------------------ wiring guards
def test_spec_carries_the_binding_text_and_the_decisions():
    text = SPEC.read_text()
    for marker in ("## 0. Binding rule text (owner, 12 Sep 2026)", "Exhibit 14", "Exhibit 15",
                   "2024A", "Total Liabilities", "BBTN", "## 6. Decision log"):
        assert marker.lower() in text.lower(), f"slide-6 spec lost: {marker}"


def test_prompt_rule_reaches_the_page_builders_only():
    from agents.adk.agents import instructions as I

    for marker in ("SLIDE 6 - INCOME STATEMENT", "Net Profit (bold AND highlighted",
                   "Total Liabilities & Equity (bold) which MUST equal Total Assets exactly",
                   "BBTN pattern", "RECONCILING line", "key_financials", "n/a WITH the reason"):
        assert marker in I.SLIDE6_RULE, f"slide-6 rule lost: {marker}"
    for name in ("writer_instruction", "critic_instruction", "industry_instruction"):
        assert "SLIDE 6 - INCOME STATEMENT" in getattr(I, name), f"{name} lost the slide-6 rule"
    for name in ("news_harvester_instruction",):
        assert "SLIDE 6 - INCOME STATEMENT" not in getattr(I, name)


def test_template_and_router_wire_slide_six():
    partial = PARTIAL.read_text()
    single = SINGLE.read_text()
    pdf = (ROOT / "server" / "routers" / "pdf.py").read_text()
    for marker in ("stmt-table", "stmt-highlight", "Balance check", "stmt-notes", "n/a"):
        assert marker in partial, f"slide-6 partial lost: {marker}"
    assert '_slide6_statements.html' in single
    assert 'payload["statements_page"] = build_statements_page(' in pdf
    # the cash-flow table moved to slide 7 (Exhibit 16) when the owner's slide-7 rules landed
    assert "Cash Flow" in (ROOT / "templates" / "_slide7_cashflow.html").read_text()
