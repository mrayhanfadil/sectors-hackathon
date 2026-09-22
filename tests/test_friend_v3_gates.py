"""Guards for the handed-over generator ruleset (docs/rules/friend-system-prompt-v3.md).

Every arm in `server/report/forecast_gate.py` is pinned in both directions: a payload that breaks
the clause produces the violation, and a payload that satisfies it produces nothing. The last two
tests prove the wiring (the arms actually run inside `audit_house_rules`, which is what the Critic
and the render path call) and that the shipped AMMN deck satisfies all of them, so a later edit to
the cover copy cannot quietly reintroduce a violation.
"""
from __future__ import annotations

import pytest

from server.report import forecast_gate as fg


# --------------------------------------------------------------------------- helpers
def _cover(period: str = "First quarter 2026", *, disclosure: str = "",
           title: str = "Capital spending peak passed, free cash flow funds debt paydown",
           heading: str = "First quarter 2026: net profit down 61,95%") -> dict:
    return {
        "meta": {"date": "11 Sep 2026", "ticker": "TEST"},
        "cover": {
            "slide1": {
                "theme_title": title,
                "highlights": ["Sales that quarter Rp 13,73 tn, net profit Rp 2,72 tn."],
                "financial_para": {
                    "heading": heading,
                    "body": (disclosure + " " if disclosure else "")
                            + f"Sales that quarter Rp 13,73 tn, net profit Rp 2,72 tn ({period}).",
                },
            },
            "slide2": {
                "katalis": {"body": "Verified Catalysts: (1) smelter done. Priced-in: 24 months."},
                "valuasi": {"body": "Target price Rp 5.873 at 15,0 times earnings."},
                "key_financials": {
                    "headers": ["Year to 31 Dec", "2024A", "2025A", "2026F", "2027F", "2028F"],
                    "rows": [
                        ["Revenue (Rpbn)", "43.036", "30.904", "27.236", "29.100", "31.400"],
                        ["EBITDA (Rpbn)", "23.040", "16.410", "18.396", "19.900", "21.500"],
                        ["Net Profit (Rpbn)", "10.290", "4.167", "7.004", "7.500", "8.100"],
                        ["EPS (Rp)", "141,9", "57,5", "96,6", "103,4", "111,7"],
                    ],
                },
            },
        },
        "financial_highlights": {
            "years": ["FY21A", "FY22A", "FY23A", "FY24A", "FY25A"],
            "rows": [
                ["Pendapatan Bersih (Rp bn)", 43036.0, 43036.0, 43036.0, 43036.0, 30904.0],
                ["EBITDA (Rp bn)", 23040.0, 23040.0, 23040.0, 23040.0, 16410.0],
                ["Marjin EBITDA (%)", 42.8, 54.8, 50.1, 53.5, 53.1],
            ],
        },
    }


# --------------------------------------------------------------------------- G1.1
@pytest.mark.parametrize("stamp,expected", [
    ("2026-08-14", "1Q26"), ("2026-08-15", "1H26"), ("2026-11-14", "1H26"),
    ("2026-11-15", "9M26"), ("2027-02-14", "9M26"), ("2027-02-15", "FY26"),
    ("2027-05-15", "FY26"), ("2027-05-16", "1Q27"),
])
def test_expected_period_boundaries(stamp: str, expected: str) -> None:
    """45 days after a period closes, that period is the oldest a report may lead with."""
    import datetime as _dt

    _rank, label = fg.expected_period_rank(_dt.date.fromisoformat(stamp))
    assert label == expected


def test_period_freshness_fires_when_the_cover_presents_an_old_period_as_latest() -> None:
    hits = fg.check_period_freshness(_cover())
    assert len(hits) == 1
    assert hits[0].startswith("G1.1")
    assert "1H26" in hits[0]


def test_period_freshness_passes_when_the_cover_says_the_newer_period_is_missing() -> None:
    payload = _cover(disclosure="The newest period available is first quarter 2026; the "
                                "first-half report is not yet available.")
    assert fg.check_period_freshness(payload) == []


def test_period_freshness_passes_when_the_snapshot_is_current() -> None:
    payload = _cover(period="First half 2026")
    assert fg.check_period_freshness(payload) == []


# --------------------------------------------------------------------------- G1.2
def test_unit_scale_fires_when_two_surfaces_disagree_by_a_scale() -> None:
    payload = _cover()
    # Same metric, same year (FY24A), 1000x apart: the class of bug that put 352,4 tn next to
    # 362,24 tn on one page.
    payload["financial_highlights"]["rows"][0][4] = 43.036
    hits = fg.check_unit_scale(payload)
    assert any(h.startswith("G1.2") and "revenue" in h for h in hits), hits


def test_unit_scale_passes_when_the_surfaces_agree() -> None:
    assert fg.check_unit_scale(_cover()) == []


def test_unit_scale_ignores_an_honest_blank() -> None:
    payload = _cover()
    payload["financial_highlights"]["rows"][0][1] = None
    assert fg.check_unit_scale(payload) == []


def test_unit_scale_fires_on_a_magnitude_its_unit_cannot_hold() -> None:
    payload = _cover()
    payload["cover"]["slide2"]["key_financials"]["rows"][0][2] = "43.036.000"
    hits = fg.check_unit_scale(payload)
    assert any("magnitude" in h for h in hits), hits


# --------------------------------------------------------------------------- G2.2
def _with_margin_quadrant(payload: dict, margin_peak: float, narrative: str) -> dict:
    payload["performance_page"] = {"quadrants": [{
        "title": "EBITDA & EBITDA Margin",
        "labels": ["2024A", "2025A", "2026F"],
        "line": [53.5, 53.1, margin_peak],
        "actual_n": 2,
        "narrative": narrative,
    }]}
    return payload


def test_margin_above_the_record_needs_a_driver() -> None:
    payload = _with_margin_quadrant(_cover(), 67.8, "Margins move to the end of the period.")
    hits = fg.check_forecast_margin(payload)
    assert len(hits) == 1
    assert hits[0].startswith("G2.2")


def test_margin_above_the_record_passes_when_the_narrative_names_the_driver() -> None:
    payload = _with_margin_quadrant(
        _cover(), 67.8,
        "Margins move to 67,8% at the end of the projection period, reflecting operating "
        "efficiency and the product mix after the smelter ramp.")
    assert fg.check_forecast_margin(payload) == []


def test_margin_inside_the_record_is_silent() -> None:
    payload = _with_margin_quadrant(_cover(), 52.0, "No driver named here at all.")
    assert fg.check_forecast_margin(payload) == []


# --------------------------------------------------------------------------- G2.3
def test_elasticity_is_the_margin_implied_pass_through() -> None:
    assert fg.elasticity_from_margin(50.0) == pytest.approx(20.0)
    assert fg.elasticity_from_margin(25.0) == pytest.approx(40.0)
    assert fg.elasticity_from_margin(0.0) is None


def test_operating_leverage_arm_fires_on_a_flat_pass_through() -> None:
    payload = _with_margin_quadrant(_cover(), 50.6, "Costs absorb the price move.")
    payload["valuation_page"] = {"notes": ["A 10% price move carries 10,0% to EBITDA."]}
    hits = fg.check_operating_leverage(payload)
    assert len(hits) == 1
    assert hits[0].startswith("G2.3")


def test_operating_leverage_arm_accepts_the_margin_implied_figure() -> None:
    payload = _with_margin_quadrant(_cover(), 50.6, "Costs absorb the price move.")
    payload["valuation_page"] = {"notes": ["A 10% price move carries 19,8% to EBITDA."]}
    assert fg.check_operating_leverage(payload) == []


# --------------------------------------------------------------------------- G2.6
def test_flat_consecutive_forecast_years_fire() -> None:
    payload = _cover()
    payload["cover"]["slide2"]["key_financials"]["rows"][0] = [
        "Revenue (Rpbn)", "43.036", "30.904", "27.236", "27.236", "31.400"]
    hits = fg.check_flat_forecast_years(payload)
    assert len(hits) == 1
    assert hits[0].startswith("G2.6")


def test_flat_years_pass_when_the_payload_declares_a_flat_basis() -> None:
    payload = _cover()
    rows = payload["cover"]["slide2"]["key_financials"]
    rows["rows"][0] = ["Revenue (Rpbn)", "43.036", "30.904", "27.236", "27.236", "31.400"]
    rows["notes"] = ["The projection holds 2026-2027 flat: no volume growth is assumed."]
    assert fg.check_flat_forecast_years(payload) == []


def test_actual_columns_are_never_flagged_as_flat_forecast_years() -> None:
    payload = _cover()
    payload["cover"]["slide2"]["key_financials"]["rows"][0] = [
        "Revenue (Rpbn)", "43.036", "43.036", "27.236", "29.100", "31.400"]
    assert fg.check_flat_forecast_years(payload) == []


# --------------------------------------------------------------------------- G3.4
def test_scenario_ladder_fires_when_the_downside_is_not_lower() -> None:
    payload = {"cDcf": {"scenarios": {
        "BEAR": {"scenario": "BEAR", "fair_value_per_share": 3200.0},
        "BASE": {"scenario": "BASE", "fair_value_per_share": 2468.4},
        "BULL": {"scenario": "BULL", "fair_value_per_share": 5176.5},
    }}}
    hits = fg.check_scenario_ladder(payload)
    assert len(hits) == 1
    assert hits[0].startswith("G3.4")


def test_scenario_ladder_passes_on_a_proper_ladder() -> None:
    payload = {"cDcf": {"scenarios": {
        "BEAR": {"scenario": "BEAR", "fair_value_per_share": 1918.6},
        "BASE": {"scenario": "BASE", "fair_value_per_share": 2468.4},
        "BULL": {"scenario": "BULL", "fair_value_per_share": 5176.5},
    }}}
    assert fg.check_scenario_ladder(payload) == []


def test_scenario_ladder_is_silent_when_no_ladder_was_computed() -> None:
    assert fg.check_scenario_ladder({"cDcf": {"scenarios": {}}}) == []
    assert fg.check_scenario_ladder({}) == []


# --------------------------------------------------------------------------- G4.2
def _wacc(payload: dict, rows: list[list[str]]) -> dict:
    payload["valuation_page"] = {"wacc_rows": rows}
    return payload


def test_currency_arm_fires_when_an_indogb_model_adds_a_country_premium() -> None:
    payload = _wacc(_cover(), [
        ["Risk-free rate (Rf)", "7,10%", "INDOGB 10Y"],
        ["Country Risk Premium", "1,50%", "Damodaran country risk premium"],
        ["Equity Risk Premium (ERP)", "4,00%", "Damodaran mature-market ERP"],
    ])
    hits = fg.check_currency_discipline(payload)
    assert any("twice" in h for h in hits), hits


def test_currency_arm_fires_when_the_erp_label_claims_a_country_adjustment() -> None:
    payload = _wacc(_cover(), [
        ["Risk-free rate (Rf)", "7,10%", "INDOGB 10Y (assumptions.rf)"],
        ["Equity Risk Premium (ERP)", "4,00%", "Damodaran (country risk adj.)"],
    ])
    hits = fg.check_currency_discipline(payload)
    assert len(hits) == 1
    assert hits[0].startswith("G4.2")


def test_currency_arm_fires_when_a_usd_model_omits_the_country_premium() -> None:
    payload = _wacc(_cover(), [
        ["Risk-free rate (Rf)", "4,20%", "UST 10Y"],
        ["Equity Risk Premium (ERP)", "4,00%", "Damodaran mature-market ERP"],
    ])
    hits = fg.check_currency_discipline(payload)
    assert any("underprices the country" in h for h in hits), hits


def test_currency_arm_passes_on_the_house_build() -> None:
    payload = _wacc(_cover(), [
        ["Risk-free rate (Rf)", "7,10%", "INDOGB 10Y (assumptions.rf)"],
        ["Equity Risk Premium (ERP)", "4,00%",
         "Damodaran mature-market ERP - no country premium added (the risk-free rate is the "
         "10Y government bond)"],
    ])
    assert fg.check_currency_discipline(payload) == []


# --------------------------------------------------------------------------- G5.2
def test_headline_caps_fire_on_a_statistic_title_over_budget() -> None:
    payload = _cover(title="The market only uses 18,38 times 2026 earnings versus a 28,42 times "
                           "long-run average and the uplift is not in the price")
    hits = fg.check_headline_caps(payload)
    assert any("runs" in h and "budget 10" in h for h in hits), hits


def test_headline_caps_fire_on_a_title_without_a_verb() -> None:
    payload = _cover(title="Copper price record and foreign fund flow")
    hits = fg.check_headline_caps(payload)
    assert any("no verb" in h for h in hits), hits


def test_headline_caps_fire_on_a_long_heading_and_a_long_bullet() -> None:
    payload = _cover(heading="First quarter 2026: net profit Rp 2,72 tn, down 61,95% from the "
                             "prior quarter, gross profit 42,4% of sales")
    payload["cover"]["slide1"]["highlights"] = [" ".join(["word"] * 31) + " Rp 1 tn"]
    hits = fg.check_headline_caps(payload)
    assert any("headline runs" in h for h in hits), hits
    assert any("highlight 1 runs" in h for h in hits), hits


def test_headline_caps_fire_on_four_figures_in_one_sentence() -> None:
    payload = _cover()
    payload["cover"]["slide1"]["highlights"] = [
        "Sales Rp 66,9 tn, profit Rp 15,2 tn and Rp 33,9 tn by 2028."]
    hits = fg.check_headline_caps(payload)
    assert any("figures in one sentence" in h for h in hits), hits


def test_headline_caps_pass_on_a_compliant_cover() -> None:
    assert fg.check_headline_caps(_cover()) == []


def test_figure_counter_ignores_digits_inside_a_name() -> None:
    """Phase-8, FY26F and 1Q26 are names; a reader never budgets them as figures."""
    assert fg._num_tokens("Phase-8 lifts ore from 1 million to 38 million tons") == 2
    assert fg._num_tokens("FY26F revenue Rp 66,9 tn") == 1
    assert fg._num_tokens("Rp 33,9 tn to Rp 55,2 tn by 2028") == 3


# --------------------------------------------------------------------------- G5.3
def _catalysts(payload: dict, items: list[dict], cover_body: str = "") -> dict:
    payload["catalysts"] = items
    payload["cover"]["shares"] = {"outstanding": 72.5}
    if cover_body:
        payload["cover"]["slide2"]["katalis"]["body"] = cover_body
    return payload


def test_catalyst_score_reads_the_items_own_fields() -> None:
    strong = {"name": "Smelter finished", "effect": "capital spending falls, revenue capacity up",
              "quantified": {"capex": "Rp 1,60 tn", "fcf": "+Rp 1,69 tn"},
              "source": "press release 24 Jul 2026"}
    score = fg.score_catalyst(strong, report_date=fg.parse_report_date("11 Sep 2026"))
    assert score["total"] >= fg.CATALYST_SCORE_FLOOR
    weak = {"name": "VanEck index review", "effect": "the stock is in the index",
            "quantified": {}, "source": "news"}
    assert fg.score_catalyst(weak, report_date=fg.parse_report_date("11 Sep 2026"))["total"] \
        < fg.CATALYST_SCORE_FLOOR


def test_insider_block_below_the_floor_must_be_a_direction() -> None:
    payload = _catalysts(_cover(), [{
        "name": "Board buying shares together, Jul 2026",
        "effect": "a sign management backs the outlook",
        "quantified": {"shares": "+12.961.700", "avg_price": "Rp 3.548"},
        "source": "IDX disclosures"}])
    hits = fg.check_catalyst_curation(payload)
    assert any("0.5% floor" in h or "below the" in h for h in hits), hits


def test_insider_block_reported_as_a_net_direction_passes() -> None:
    payload = _catalysts(_cover(), [{
        "name": "Board net buying in Jul 2026",
        "effect": "a cumulative sign management backs the outlook",
        "quantified": {"shares": "+12.961.700", "avg_price": "Rp 3.548"},
        "source": "IDX disclosures"}])
    assert fg.check_catalyst_curation(payload) == []


def test_catalyst_table_cap_fires_past_seven_items() -> None:
    items = [{"name": f"Catalyst {i}", "effect": "revenue and margin driver",
              "quantified": {"value": "Rp 1,0 tn", "date": "2026-08-01"},
              "source": "news 2026-08-02"} for i in range(8)]
    hits = fg.check_catalyst_curation(_catalysts(_cover(), items))
    assert any("cap 7" in h for h in hits), hits


def test_cover_paragraph_catalyst_cap_fires_past_three_names() -> None:
    names = ["Alpha catalyst", "Beta catalyst", "Gamma catalyst", "Delta catalyst"]
    items = [{"name": n, "effect": "revenue and margin driver",
              "quantified": {"value": "Rp 1,0 tn", "date": "2026-08-01"},
              "source": "news 2026-08-02"} for n in names]
    payload = _catalysts(_cover(), items, cover_body="Verified Catalysts: " + "; ".join(names))
    hits = fg.check_catalyst_curation(payload)
    assert any("cap 3" in h for h in hits), hits


def test_a_daily_price_move_is_excluded_as_a_catalyst() -> None:
    payload = _catalysts(_cover(), [{
        "name": "Share price rose 4% today",
        "effect": "the share price jumped 4% today",
        "quantified": {"move": "4%"},
        "source": "exchange summary"}])
    hits = fg.check_catalyst_curation(payload)
    assert any("which the rules exclude" in h for h in hits), hits


# --------------------------------------------------------------------------- robustness + wiring
@pytest.mark.parametrize("junk", [
    {}, {"cover": "x"}, {"cover": {"slide1": None, "slide2": []}}, {"meta": {"date": 3}},
    {"catalysts": ["x", 3]}, {"financial_highlights": {"rows": [[None, "a"]]}},
    {"valuation_page": {"wacc_rows": "x"}}, {"performance_page": {"quadrants": [1, 2]}},
])
def test_arms_never_raise_on_a_malformed_payload(junk) -> None:
    assert isinstance(fg.audit_friend_v3(junk), list)


def test_house_rules_runs_the_friend_arms() -> None:
    """A gate nobody calls enforces nothing: the arms must ride in the aggregate the Critic reads."""
    from server.report.house_rules import audit_house_rules

    payload = _cover()
    payload["cover"]["slide1"]["theme_title"] = "Copper price record and foreign fund flow"
    audit = audit_house_rules(payload)
    assert any(v.startswith("G5.2") for v in audit["violations"]), audit["violations"]
    assert "friend-v3" in audit["sections"]


def test_constants_do_not_drift_from_the_house_contract() -> None:
    from server.report import house_rules as hr

    assert fg.KF_HEADER_FIRST == hr.KF_HEADER_FIRST
    for prefix in fg.KF_LEVEL_ROWS:
        assert any(row.startswith(prefix) for row in hr.KF_ROWS), prefix


def test_the_shipped_deck_satisfies_every_arm() -> None:
    """The live AMMN payload is the artifact a reader gets: it must be clean on all arms."""
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload("AMMN", None)
    assert fg.audit_friend_v3(payload) == []
