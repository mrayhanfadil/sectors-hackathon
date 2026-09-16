"""Slide 7 - cash flow + key ratio: structure, footing, the mandated tie-outs, and the gate."""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "server" / "routers" / "pdf.py"
PARTIAL = ROOT / "templates" / "_slide7_cashflow.html"
SPEC = ROOT / "docs" / "ammn-slides" / "slide7-cashflow-ratio-spec.md"
YEARS = ["2024A", "2025A", "2026F", "2027F", "2028F"]


@pytest.fixture(scope="module")
def payload():
    from server.routers.pdf import render_html_for_ticker

    return render_html_for_ticker("AMMN", None)[2]


def block(page, title):
    return next((sec["rows"] for sec in page["sections"] if sec["title"].startswith(title)), [])


def find(rows, needle):
    return next((r for r in rows if needle.lower() in str(r["label"]).lower()), None)


# ------------------------------------------------------------------ structure
def test_cashflow_has_the_three_sections_and_the_closing_block(payload):
    cf = payload["cashflow_page"]
    assert cf["available"] and cf["years"] == YEARS
    titles = [s["title"] for s in cf["sections"]]
    assert titles == ["Cash Flow from Operations", "Cash Flow from Investing", "Cash Flow from Financing"]
    ops = [r["label"] for r in block(cf, "Cash Flow from Operations")]
    assert ops[0].startswith("Net Profit") and ops[-1].startswith("Net Cash from Operations")
    for needle in ("Net Change in Cash", "Beginning Cash Balance", "Ending Cash Balance"):
        assert find(cf["closing"], needle), needle
    assert cf["memo"] and "Free Cash Flow" in cf["memo"][0]["label"]


def test_cashflow_sections_foot_in_every_column(payload):
    cf = payload["cashflow_page"]
    for title, parts in (("Cash Flow from Operations", ("Net Profit", "Depreciation", "Working Capital",
                                                        "Other Operating")),
                         ("Cash Flow from Investing", ("Capital Expenditure", "Other Investing")),
                         ("Cash Flow from Financing", ("Debt Raised", "Dividends", "Equity Raised"))):
        rows = block(cf, title)
        sub = rows[-1]
        assert sub["kind"] == "subtotal", title
        for i in range(5):
            total = sum((r["cells"][i] or 0.0) for r in rows[:-1])
            assert sub["cells"][i] == pytest.approx(total, abs=1.0), (title, YEARS[i])


# ------------------------------------------------------------------ tie-outs
def test_net_profit_chains_from_the_income_statement_into_the_cash_flow(payload):
    cf, sp = payload["cashflow_page"], payload["statements_page"]
    kf = {str(r[0]): r[1:] for r in payload["cover"]["slide2"]["key_financials"]["rows"]}
    cf_net = find(block(cf, "Cash Flow from Operations"), "Net Profit")["cells"]
    is_net = find(sp["income"]["rows"], "Net Profit")["cells"]
    kf_net = next(v for k, v in kf.items() if k.startswith("Net Profit"))
    for i, y in enumerate(YEARS):
        assert cf_net[i] == pytest.approx(is_net[i], abs=1.0), y
        assert cf_net[i] == pytest.approx(float(str(kf_net[i]).replace(".", "")), abs=1.0), y


def test_ending_cash_equals_the_balance_sheet_cash(payload):
    """The rule the page exists for: a gap here means the sheets are not linked."""
    cf = payload["cashflow_page"]
    bs_cash = find(payload["statements_page"]["balance"]["rows"], "Cash & Cash")["cells"]
    end = find(cf["closing"], "Ending Cash")["cells"]
    for i, y in enumerate(YEARS):
        assert end[i] == pytest.approx(bs_cash[i], abs=max(1.0, abs(bs_cash[i]) * 0.001)), y


def test_beginning_plus_net_change_equals_ending_or_says_why(payload):
    cf = payload["cashflow_page"]
    begin = find(cf["closing"], "Beginning")["cells"]
    change = find(cf["closing"], "Net Change")["cells"]
    end = find(cf["closing"], "Ending Cash")["cells"]
    residual_row = find(cf["closing"], "Selisih")
    for i, y in enumerate(YEARS):
        gap = end[i] - (begin[i] + change[i])
        if abs(gap) > 1.0:
            assert residual_row is not None, f"{y} has an undisclosed reconciliation gap"
    if residual_row:
        assert any("selisih" in str(n).lower() for n in cf["notes"]), \
            "the reconciliation row must be explained in the notes"


def test_fcf_memo_is_ocf_minus_capex_and_the_fcff_gap_is_explained(payload):
    cf = payload["cashflow_page"]
    ocf = find(block(cf, "Cash Flow from Operations"), "Net Cash from Operations")["cells"]
    capex = find(block(cf, "Cash Flow from Investing"), "Capital Expenditure")["cells"]
    memo = cf["memo"][0]["cells"]
    for i in range(5):
        assert memo[i] == pytest.approx(ocf[i] + capex[i], abs=1.0), YEARS[i]
    if cf.get("fcff_exhibit8"):
        assert any("cross-check fcff" in str(n).lower() for n in cf["notes"]), \
            "the FCFF cross-check must be printed, not implied"


# ------------------------------------------------------------------ ratios
def test_ratio_exhibit_has_the_three_sections_and_no_blank_rows(payload):
    kr = payload["key_ratio_page"]
    assert [s["title"] for s in kr["sections"]] == ["Growth (%)", "Profitability (%)", "Leverage"]
    for sec in kr["sections"]:
        for r in sec["rows"]:
            assert any(isinstance(c, (int, float)) for c in r["cells"]), r["label"]


def test_ratios_recompute_from_the_printed_statements(payload):
    kr, sp = payload["key_ratio_page"], payload["statements_page"]
    inc = {r["label"].split(" /")[0].split(" (")[0].strip(): r["cells"] for r in sp["income"]["rows"]}
    bal = {r["label"].split(" (")[0].strip(): r["cells"] for r in sp["balance"]["rows"]}

    def row(section, needle):
        return find(next(s["rows"] for s in kr["sections"] if s["title"].startswith(section)), needle)["cells"]

    gm, om, nm = row("Profitability", "Gross Margin"), row("Profitability", "Operating"), \
        row("Profitability", "Net Margin")
    cov, gear = row("Leverage", "Interest Coverage"), row("Leverage", "Gearing")
    for i in range(5):
        rev = inc["Revenue"][i]
        assert gm[i] == pytest.approx(inc["Gross Profit"][i] / rev * 100, abs=0.15), YEARS[i]
        assert om[i] == pytest.approx(inc["EBIT"][i] / rev * 100, abs=0.15), YEARS[i]
        assert nm[i] == pytest.approx(inc["Net Profit"][i] / rev * 100, abs=0.15), YEARS[i]
        assert cov[i] == pytest.approx(inc["EBIT"][i] / inc["Interest Expense"][i], abs=0.05), YEARS[i]
        debt = bal["Short-term Debt"][i] + bal["Long-term Debt"][i]
        want = (debt - bal["Cash & Cash Equivalents"][i]) / bal["Shareholders' Equity"][i]
        assert gear[i] == pytest.approx(want, abs=0.02), YEARS[i]


def test_ratio_windows_use_printed_balances_not_interpolated_ones(payload):
    kr = payload["key_ratio_page"]
    for sec in kr["sections"]:
        for r in sec["rows"]:
            assert r["cells"][0] is not None, f"{r['label']} has no 2024A ratio"
    assert any("rata-rata" in str(n).lower() or "average" in str(n).lower() for n in kr["notes"])


# ------------------------------------------------------------------ gate
def test_gate_passes_and_bites(payload):
    import copy

    from server.report.house_rules import audit_cashflow_page, audit_key_ratio_page, audit_house_rules

    assert audit_house_rules(payload)["violations"] == []
    cf, kr = payload["cashflow_page"], payload["key_ratio_page"]

    def drop_row(page, section, needle):
        for sec in page["sections"]:
            if sec["title"].startswith(section):
                sec["rows"] = [r for r in sec["rows"] if needle.lower() not in r["label"].lower()]

    mutations = {
        "cash flow: drop the D&A row": lambda p: drop_row(p["cashflow_page"], "Cash Flow from Operations",
                                                          "Depreciation"),
        "cash flow: make a subtotal wrong": lambda p: block(p["cashflow_page"], "Cash Flow from Operations")[-1]
        .__setitem__("cells", [0, 0, 0, 0, 0]),
        "cash flow: break the ending-cash tie": lambda p: find(p["cashflow_page"]["closing"],
                                                               "Ending Cash").__setitem__(
            "cells", [c * 1.05 for c in find(p["cashflow_page"]["closing"], "Ending Cash")["cells"]]),
        "cash flow: break the net-profit chain": lambda p: find(block(p["cashflow_page"],
                                                                      "Cash Flow from Operations"),
                                                                "Net Profit").__setitem__(
            "cells", [c + 500 for c in find(block(p["cashflow_page"], "Cash Flow from Operations"),
                                            "Net Profit")["cells"]]),
        "cash flow: drop the FCF memo": lambda p: p["cashflow_page"].__setitem__("memo", []),
        "ratio: blank a row": lambda p: next(s for s in p["key_ratio_page"]["sections"]
                                             if s["title"].startswith("Profitability"))["rows"][0].__setitem__(
            "cells", [None] * 5),
        "ratio: fudge net gearing": lambda p: find(next(s for s in p["key_ratio_page"]["sections"]
                                                        if s["title"].startswith("Leverage"))["rows"],
                                                   "Gearing").__setitem__("cells", [9.9] * 5),
    }
    for label, mutate in mutations.items():
        broken = copy.deepcopy(payload)
        mutate(broken)
        out = (audit_cashflow_page(broken["cashflow_page"], broken)
               + audit_key_ratio_page(broken["key_ratio_page"], broken))
        assert out, f"the gate failed to catch: {label}"

    assert audit_cashflow_page(None) == []
    assert audit_cashflow_page({"available": False, "reason": "no cache"})


# ------------------------------------------------------------------ wiring guards
def test_the_builders_run_in_order_so_the_pages_read_the_same_statements():
    """The ratio block must read the statements page the deck prints. Rebuilding it independently
    produced a ratio block computed from a different income statement - caught once already."""
    src = PDF.read_text()
    i_cf = src.index("build_cashflow_page(")
    i_is = src.index('payload["statements_page"] = build_statements_page(')
    i_kr = src.index("build_key_ratio_page(")
    assert i_cf < i_is < i_kr, "the cash flow must be built first, then the statements, then the ratios"
    assert "statements=payload[\"statements_page\"]" in src, \
        "the ratio builder must be handed the printed statements page"


def test_template_renders_both_exhibits_and_the_memo_style():
    t = PARTIAL.read_text()
    for marker in ("Cash Flow Statement", "key_ratio_page", "stmt-memo", "ratio-section",
                   "stmt-note-cols"):
        assert marker in t, marker
    assert "number}}" in t or "is number" in t, "negatives must render in brackets"


def test_spec_keeps_the_binding_text_and_the_decisions():
    text = SPEC.read_text()
    for marker in ("## 0. Binding rule text (owner, 13 Sep 2026)", "Ending Cash Balance", "Net Gearing",
                   "BBTN", "0.1%", "## 2. Decision log"):
        assert marker.lower() in text.lower(), marker
