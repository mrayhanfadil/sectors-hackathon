"""Numeric audit harness for ACES and institutional report fixtures.

Prevents regression of the dividend yield 8.99% bug (calculated @356 instead of spot @358)
and guarantees mathematical consistency across all fixture components:
  1. Dividend yield == DPS / price across all fixture prose, KPIs, and financial tables.
  2. Blended fair value arithmetic (60% DCF + 40% EV/EBITDA).
  3. DCF engine recomputation (FCF explicit discounting + Gordon growth TV + net cash).
  4. Multiples recomputation (EBITDA * peer multiple + net cash).
  5. Upside percentage arithmetic ((TP - Price) / Price * 100).
  6. Market capitalization ((Price * Shares) / 1000 in Rp T).
  7. 5x5 WACC x g sensitivity grid formula recalculation within Rp1.
  8. EV-to-equity bridge component sum (PVexplicit + PVtv + net_cash = Equity).
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "scripts" / "fixtures" / "aces_report_data.json"

# --- Verified Ground Truth Constants (ACES) ---
GROUND_TRUTH = {
    "price": 358.0,
    "shares_outstanding_B": 17.12,
    "DPS": 32.01,
    "net_cash_B": 1021.13,
    "cash_B": 2010.0,
    "debt_B": 988.87,
    "FCF_B": [720.0, 770.0, 825.0, 875.0, 925.0],
    "wacc": 0.110096,  # 11.01%
    "g": 0.03,         # 3.0%
    "ebitda_B": 1040.0,
    "peer_multiple": 8.0,
    "dcf_weight": 0.60,
    "multiples_weight": 0.40,
}


@pytest.fixture(scope="module")
def aces_fixture() -> Dict[str, Any]:
    """Load the ACES report fixture JSON."""
    assert FIXTURE_PATH.exists(), f"Fixture file not found: {FIXTURE_PATH}"
    content = FIXTURE_PATH.read_text(encoding="utf-8")
    return json.loads(content)


def parse_id_number(val: Any) -> float:
    """Parse Indonesian/English formatted numbers (e.g. '8,94%', '10.058', 'Rp 647', '+1.021')."""
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        raise ValueError(f"Cannot parse non-string/non-numeric value: {val!r}")

    s = val.strip()
    s = re.sub(r"[Rr]p\.?\s*", "", s)
    s = re.sub(r"%\s*(?:YoY|y/y)?", "", s)
    s = re.sub(r"\s*(?:T|bn|M|jt|miliar saham|/saham|saham|x)\b", "", s, flags=re.IGNORECASE)
    s = s.replace("+", "").strip()

    if "," in s and "." in s:
        # e.g., '1.021,50' -> '1021.50'
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Indonesian decimal: '8,94' -> '8.94'
        s = s.replace(",", ".")
    elif "." in s:
        # e.g., '10.058' (thousand sep) vs '647.12' (decimal)
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0:
            # Thousand separator representation in Rp bn
            s = parts[0] + parts[1]
        # else standard float representation

    return float(s)


def extract_yield_occurrences(data: Dict[str, Any]) -> List[Tuple[str, float, Optional[float], Optional[float], Any]]:
    """Extract all dividend yield occurrences with location paths, parsed yield, local DPS, local price, and raw value."""
    occurrences: List[Tuple[str, float, Optional[float], Optional[float], Any]] = []

    fallback_price = float(data.get("cover", {}).get("rating_box", {}).get("price", GROUND_TRUTH["price"]))
    fallback_dps = GROUND_TRUTH["DPS"]

    def parse_dps_price_from_text(text: str) -> Tuple[float, float]:
        dps_m = re.search(r"DPS\s*(?:Rp\.?\s*)?([0-9]+[.,][0-9]+)", text, re.IGNORECASE)
        price_m = re.search(r"@\s*(?:Rp\.?\s*)?([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        d = float(dps_m.group(1).replace(",", ".")) if dps_m else fallback_dps
        p = float(price_m.group(1).replace(",", ".")) if price_m else fallback_price
        return d, p

    # 1. Cover rating box takeaways
    takeaways = data.get("cover", {}).get("rating_box", {}).get("key_takeaways", [])
    for idx, item in enumerate(takeaways):
        m = re.search(r"[Yy]ield\s+([0-9]+[.,][0-9]+)%", item)
        if m:
            d, p = parse_dps_price_from_text(item)
            occurrences.append((
                f"cover.rating_box.key_takeaways[{idx}]",
                parse_id_number(m.group(1)),
                d,
                p,
                item
            ))

    # 2. Cover summary
    summary = data.get("cover", {}).get("summary", "")
    m = re.search(r"yield\s+([0-9]+[.,][0-9]+)%", summary, re.IGNORECASE)
    if m:
        d, p = parse_dps_price_from_text(summary)
        occurrences.append(("cover.summary", parse_id_number(m.group(1)), d, p, summary))

    # 3. Thesis details
    for idx, th in enumerate(data.get("thesis", [])):
        detail = th.get("detail", "")
        m = re.search(r"yield\s+([0-9]+[.,][0-9]+)%", detail, re.IGNORECASE)
        if m:
            d, p = parse_dps_price_from_text(detail)
            occurrences.append((f"thesis[{idx}].detail", parse_id_number(m.group(1)), d, p, detail))

    # 4. KPIs list
    for idx, kpi in enumerate(data.get("kpis", [])):
        name = kpi.get("name", "")
        if "yield" in name.lower() or "dividen" in name.lower():
            row_text = " ".join(str(c) for c in kpi.get("row", []) if c is not None)
            d, p = parse_dps_price_from_text(row_text)
            if "value" in kpi and kpi["value"] is not None:
                occurrences.append((f"kpis[{idx}].value", parse_id_number(kpi["value"]), d, p, kpi))
            if isinstance(kpi.get("row"), list) and len(kpi["row"]) > 1:
                occurrences.append((f"kpis[{idx}].row[1]", parse_id_number(kpi["row"][1]), d, p, kpi["row"]))

    # 5. Financials tables (Rasio Kunci)
    for t_idx, table in enumerate(data.get("financials", [])):
        for r_idx, row in enumerate(table.get("rows", [])):
            if row and "dividend yield" in str(row[0]).lower():
                row_text = " ".join(str(c) for c in row if c is not None)
                d, p = parse_dps_price_from_text(row_text)
                occurrences.append((
                    f"financials[{t_idx}].rows[{r_idx}]",
                    parse_id_number(row[1]),
                    d,
                    p,
                    row
                ))

    # 6. Valuation conclusion
    conclusion = data.get("valuation", {}).get("conclusion", "")
    m = re.search(r"yield\s+([0-9]+[.,][0-9]+)%", conclusion, re.IGNORECASE)
    if m:
        d, p = parse_dps_price_from_text(conclusion)
        occurrences.append(("valuation.conclusion", parse_id_number(m.group(1)), d, p, conclusion))

    # 7. Financial statements ratio table
    ratios = data.get("financial_statements", {}).get("ratios", {}).get("rows", [])
    for r_idx, row in enumerate(ratios):
        if row and "dividend yield" in str(row[0]).lower():
            row_text = " ".join(str(c) for c in row if c is not None)
            d, p = parse_dps_price_from_text(row_text)
            occurrences.append((
                f"financial_statements.ratios.rows[{r_idx}]",
                parse_id_number(row[1]),
                d,
                p,
                row
            ))

    return occurrences


def test_yield_matches_price(aces_fixture: Dict[str, Any]):
    """Exact regression test for the 8.99 bug:

    DPS 32.01 / price 358 = 8.94134% -> 8.94%.
    Any pre-fix value of 8.99% (computed @356) must strictly fail within 0.05pp tolerance.
    """
    occurrences = extract_yield_occurrences(aces_fixture)
    assert len(occurrences) >= 7, f"Expected at least 7 yield locations, found {len(occurrences)}"

    for loc, parsed_yield, local_dps, local_price, raw in occurrences:
        dps = local_dps if local_dps is not None else GROUND_TRUTH["DPS"]
        price = local_price if local_price is not None else GROUND_TRUTH["price"]
        expected_yield = (dps / price) * 100.0  # 8.94134...%

        diff = abs(parsed_yield - expected_yield)
        assert diff <= 0.02, (
            f"Yield mismatch at {loc}: found {parsed_yield}%, expected {expected_yield:.2f}% "
            f"(DPS={dps} / price={price} * 100). Diff: {diff:.4f}pp. Raw: {raw!r}"
        )


def test_blended_arithmetic(aces_fixture: Dict[str, Any]):
    """Assert blended Fair Value = 0.6 * DCF_FV (647.12) + 0.4 * Multiples_FV (545.63) = 606.52."""
    val = aces_fixture["valuation"]
    blended = val["blended"]
    methods = val["methods"]

    dcf_method = next(m for m in methods if m.get("method") == "DCF")
    mult_method = next(m for m in methods if "EV/EBITDA" in m.get("method", "") or "multiples" in m.get("method", "").lower())

    fv_dcf = float(dcf_method["fv"])
    fv_mult = float(mult_method["fv"])

    w_dcf = GROUND_TRUTH["dcf_weight"]
    w_mult = GROUND_TRUTH["multiples_weight"]
    expected_blended = round(w_dcf * fv_dcf + w_mult * fv_mult, 2)

    assert expected_blended == 606.52, f"Computed blended FV is {expected_blended}, expected 606.52"
    assert blended["fair_value"] == pytest.approx(606.52, abs=0.01)
    assert aces_fixture["cover"]["rating_box"]["tp"] == pytest.approx(606.52, abs=0.01)

    # Check peer table model blended row
    peer_rows = aces_fixture["peers"]["tables"][0]["rows"]
    blended_peer = next(r for r in peer_rows if "model blended" in str(r[0]).lower())
    assert float(blended_peer[1]) == pytest.approx(606.52, abs=0.01)


def test_dcf_recompute(aces_fixture: Dict[str, Any]):
    """Recompute DCF explicit PV, Terminal PV, EV, Equity, and FV from ground truth inputs:

    PV = sum(FCF_t / (1+w)^t), TV = FCF_5*(1+g)/(w-g), PV_TV = TV/(1+w)^5,
    EV = PV + PV_TV, Equity = EV + net_cash, FV = Equity / shares.
    """
    fcfs = GROUND_TRUTH["FCF_B"]
    w = GROUND_TRUTH["wacc"]
    g = GROUND_TRUTH["g"]
    net_cash = GROUND_TRUTH["net_cash_B"]
    shares = GROUND_TRUTH["shares_outstanding_B"]

    pv_explicit = sum(f / ((1.0 + w) ** t) for t, f in enumerate(fcfs, start=1))
    tv = fcfs[-1] * (1.0 + g) / (w - g)
    pv_tv = tv / ((1.0 + w) ** len(fcfs))
    ev = pv_explicit + pv_tv
    equity = ev + net_cash
    fv = equity / shares

    # Verify mathematical constants
    assert round(pv_explicit) == 3001
    assert round(pv_tv) == 7056
    assert round(ev) == 10058
    assert round(equity) == 11079
    assert round(fv, 2) == 647.12

    # Check DCF method in fixture
    dcf_method = next(m for m in aces_fixture["valuation"]["methods"] if m.get("method") == "DCF")
    assert dcf_method["fv"] == pytest.approx(647.12, abs=0.01)

    # Check DCF grid strings
    dcf_grid = aces_fixture["valuation"]["dcf_grid"]
    assert parse_id_number(dcf_grid["pv_explicit"]) == 3001.0
    assert parse_id_number(dcf_grid["pv_tv"]) == 7056.0
    assert parse_id_number(dcf_grid["ev"]) == 10058.0
    assert parse_id_number(dcf_grid["net_cash"]) == 1021.0


def test_multiples_recompute(aces_fixture: Dict[str, Any]):
    """Recompute EV/EBITDA fair value:

    EV = EBITDA * Multiple = 1040 * 8.0 = 8320.
    Equity = EV + net_cash = 8320 + 1021.13 = 9341.13.
    FV = Equity / shares = 9341.13 / 17.12 = 545.63.
    """
    ebitda = GROUND_TRUTH["ebitda_B"]
    mult = GROUND_TRUTH["peer_multiple"]
    net_cash = GROUND_TRUTH["net_cash_B"]
    shares = GROUND_TRUTH["shares_outstanding_B"]

    ev = ebitda * mult
    equity = ev + net_cash
    fv = equity / shares

    assert ev == 8320.0
    assert round(equity, 2) == 9341.13
    assert round(fv, 2) == 545.63

    mult_method = next(m for m in aces_fixture["valuation"]["methods"] if "EV/EBITDA" in m.get("method", ""))
    assert mult_method["fv"] == pytest.approx(545.63, abs=0.01)
    assert mult_method["assumptions"]["ebitda_bn"] == 1040
    assert mult_method["assumptions"]["multiple"] == 8.0


def test_upside_arithmetic(aces_fixture: Dict[str, Any]):
    """Assert upside percentage = (TP - Price) / Price * 100 = (606.52 - 358) / 358 * 100 = 69.42%."""
    price = GROUND_TRUTH["price"]
    tp = 606.52
    expected_upside = round((tp - price) / price * 100.0, 2)

    assert expected_upside == 69.42
    rating_box = aces_fixture["cover"]["rating_box"]
    assert rating_box["price"] == price
    assert rating_box["tp"] == tp
    assert rating_box["upside_pct"] == pytest.approx(69.42, abs=0.01)


def test_market_cap(aces_fixture: Dict[str, Any]):
    """Assert market cap = Price (358) * Shares (17.12B) / 1000 = 6.13 Rp T."""
    price = GROUND_TRUTH["price"]
    shares = GROUND_TRUTH["shares_outstanding_B"]
    expected_mcap_t = round((price * shares) / 1000.0, 2)

    assert expected_mcap_t == 6.13
    mcap_str = aces_fixture["cover"]["market"]["market_cap"]
    parsed_mcap = parse_id_number(mcap_str)
    assert parsed_mcap == pytest.approx(6.13, abs=0.01)


def test_sensitivity_grid_formula(aces_fixture: Dict[str, Any]):
    """Recompute full 5x5 WACC x g sensitivity grid using DCF formula:

    Rows: WACC = [9.01%, 10.01%, 11.01%, 12.01%, 13.01%]
    Cols: g = [2.0%, 2.5%, 3.0%, 3.5%, 4.0%]
    Assert each cell in fixture matches formula within Rp 1.
    """
    fcfs = GROUND_TRUTH["FCF_B"]
    net_cash = GROUND_TRUTH["net_cash_B"]
    shares = GROUND_TRUTH["shares_outstanding_B"]

    wacc_rates = [0.090096, 0.100096, 0.110096, 0.120096, 0.130096]
    g_rates = [0.02, 0.025, 0.03, 0.035, 0.04]

    sens = aces_fixture["dcf_deep_dive"]["sensitivity"]
    fixture_rows = sens["rows"]
    assert len(fixture_rows) == 5, f"Expected 5 rows in sensitivity table, got {len(fixture_rows)}"

    for i, w in enumerate(wacc_rates):
        fixture_row = fixture_rows[i]
        for j, g in enumerate(g_rates):
            pv_exp = sum(f / ((1.0 + w) ** t) for t, f in enumerate(fcfs, start=1))
            tv = fcfs[-1] * (1.0 + g) / (w - g)
            pv_tv = tv / ((1.0 + w) ** len(fcfs))
            fv = (pv_exp + pv_tv + net_cash) / shares
            expected_cell = round(fv)

            fixture_cell = parse_id_number(fixture_row[j + 1])
            assert abs(fixture_cell - expected_cell) <= 1, (
                f"Sensitivity cell mismatch at row {i} (w={w:.4f}), col {j} (g={g:.3f}): "
                f"fixture has {fixture_cell}, formula yielded {expected_cell} (raw {fv:.2f})"
            )

    # Assert 3 scenarios (Conservative, Base, Optimistic) match corner/center cells
    scenarios = aces_fixture["dcf_deep_dive"]["scenarios"]["rows"]
    cons_fv = parse_id_number(scenarios[0][1])  # WACC 13.01%, g 2.0%
    base_fv = parse_id_number(scenarios[1][1])  # WACC 11.01%, g 3.0%
    opt_fv = parse_id_number(scenarios[2][1])   # WACC 9.01%, g 4.0%

    assert cons_fv == 498.0
    assert base_fv == 647.0
    assert opt_fv == 973.0


def test_bridge_components(aces_fixture: Dict[str, Any]):
    """Assert EV-to-equity bridge consistency:

    PVexplicit (3001) + PVtv (7056) = EV (10058).
    EV (10058) + Net Cash (1021) = Implied Equity Value (11079).
    Equity (11079) / Shares (17.12) = 647/share.
    Net Cash = Cash (2010) - Debt (989) = 1021.
    """
    bridge_rows = aces_fixture["dcf_deep_dive"]["bridge"]["rows"]
    ev_val = parse_id_number(bridge_rows[0][1])        # 10.058 -> 10058
    net_cash_val = parse_id_number(bridge_rows[1][1])  # +1.021 -> 1021
    equity_val = parse_id_number(bridge_rows[2][1])    # 11.079 -> 11079
    fv_share = parse_id_number(bridge_rows[3][1])      # Rp 647/saham -> 647

    assert ev_val == 10058.0
    assert net_cash_val == 1021.0
    assert equity_val == 11079.0
    assert ev_val + net_cash_val == equity_val

    shares = GROUND_TRUTH["shares_outstanding_B"]
    assert round(equity_val / shares) == fv_share


@pytest.mark.parametrize(
    "mutation_path,bad_value",
    [
        ("cover.rating_box.key_takeaways[1]", "Yield 8,99% (DPS Rp32,01) ditopang net-cash Rp1,02T"),
        ("cover.summary", "Inisiasi liputan ACES... yield 8,99% ditopang..."),
        ("thesis[2].detail", "Ekspansi ex-Jawa... DPS Rp32,01 yield 8,99%"),
        ("kpis[3].value", 8.99),
        ("kpis[3].row[1]", 8.99),
        ("financials[1].rows[7][1]", 8.99),
        ("valuation.conclusion", "Blended FV... DPS Rp32,01 (yield 8,99%)."),
        ("financial_statements.ratios.rows[7][1]", "8,99%"),
    ]
)
def test_pre_fix_yield_mutations_rejected(aces_fixture: Dict[str, Any], mutation_path: str, bad_value: Any):
    """Parametrized verification that if ANY individual fixture location is reverted to 8.99%,

    the audit harness test_yield_matches_price logic detects and rejects it.
    """
    mutated = copy.deepcopy(aces_fixture)
    if mutation_path == "cover.rating_box.key_takeaways[1]":
        mutated["cover"]["rating_box"]["key_takeaways"][1] = bad_value
    elif mutation_path == "cover.summary":
        mutated["cover"]["summary"] = bad_value
    elif mutation_path == "thesis[2].detail":
        mutated["thesis"][2]["detail"] = bad_value
    elif mutation_path == "kpis[3].value":
        mutated["kpis"][3]["value"] = bad_value
    elif mutation_path == "kpis[3].row[1]":
        mutated["kpis"][3]["row"][1] = bad_value
    elif mutation_path == "financials[1].rows[7][1]":
        mutated["financials"][1]["rows"][7][1] = bad_value
    elif mutation_path == "valuation.conclusion":
        mutated["valuation"]["conclusion"] = bad_value
    elif mutation_path == "financial_statements.ratios.rows[7][1]":
        mutated["financial_statements"]["ratios"]["rows"][7][1] = bad_value

    with pytest.raises(AssertionError) as exc_info:
        test_yield_matches_price(mutated)
    assert "Yield mismatch" in str(exc_info.value)
