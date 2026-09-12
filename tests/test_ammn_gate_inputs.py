"""AMMN-R2D regression guard: Gate-0..5 inputs are read from the assumptions file.

Baseline (docs/ammn-slides/verify-report-v2.md §1.1, CHK-01): unassisted
``render_report('AMMN')`` reached the gate stage and halted with

    ValueError: gate inputs absent for AMMN: missing ['filing_history_years',
    'ebit_positive_count', 'd_de_ratio', 'net_debt_to_ebitda',
    'interest_coverage', 'shareholders_equity', 'nci_pct', 'revenue_drivers',
    'has_steady_state_3y', 'life_cycle_stage'] — refusing fabricated gate params

Root cause: ``server/routers/pdf.py:_build_live_payload`` never put a
``gate_inputs`` block on the payload, while
``server/report/typst_renderer.py:_get_ticker_gate_params`` requires one.

This file pins the wiring: gate inputs are READ from ``data/assumptions/{T}.json``
(nested ``gate_inputs`` block, the same key at top level, or a restatement of a
quantity the file already declares). Keys the file does not support stay ABSENT —
the renderer must keep halting loudly and naming them rather than being handed an
invented filing history / equity base / coverage ratio (LOUD policy).
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
AMMN = REPO_ROOT / "data" / "assumptions" / "AMMN.json"

# server/report/typst_renderer.py:_GATE_REQUIRED_KEYS — the keys the gate stage needs.
GATE_KEYS = (
    "filing_history_years",
    "ebit_positive_count",
    "d_de_ratio",
    "net_debt_to_ebitda",
    "interest_coverage",
    "shareholders_equity",
    "nci_pct",
    "revenue_drivers",
    "has_steady_state_3y",
    "life_cycle_stage",
)

# The two keys the loader may RESTATE from a quantity the file already declares.
_RESTATED = ("d_de_ratio", "net_debt_to_ebitda")

# Minimal 15-key valuation input set so _build_live_payload() clears its own 422 gate.
_VALUATION_INPUTS: dict[str, Any] = {
    "rf": 0.071, "beta": 1.4071, "erp": 0.0669, "cod": 0.0649, "g": 0.025,
    "payout": 0.0, "fcf": [13088.9] * 5, "shares_out": 72518217656.0,
    "net_debt": 110786062912260.0, "cash": 13846126732260.0,
    "ebitda": 18396257972040.0, "ev_multiple": 28.42, "last_price": 4860.0,
    "we": 0.7608, "wd": 0.2392,
}

# A file-declared gate block for tests: every key the renderer requires, sourced
# from the file itself (mining domain mirrors agents/valuation/gates.py paths).
_DECLARED_GATE_INPUTS: dict[str, Any] = {
    "domain": "mining",
    "filing_history_years": 8,
    "ebit_positive_count": 3,
    "d_de_ratio": 0.24,
    "net_debt_to_ebitda": 5.27,
    "interest_coverage": 3.48,
    "shareholders_equity": 40_000_000_000_000.0,
    "nci_pct": 5.0,
    "revenue_drivers": ["commodity_coal"],
    "has_steady_state_3y": True,
    "life_cycle_stage": "mature",
}


def _assumptions(**overrides: Any) -> dict[str, Any]:
    data = dict(_VALUATION_INPUTS)
    data.update(overrides)
    return data


# ------------------------------------------------------------------ loader unit tests

def test_gate_inputs_read_from_nested_block_and_top_level():
    from server.routers.pdf import _gate_inputs_from_assumptions

    nested = _gate_inputs_from_assumptions({"gate_inputs": dict(_DECLARED_GATE_INPUTS)})
    assert nested == _DECLARED_GATE_INPUTS

    top_level = _gate_inputs_from_assumptions(dict(_DECLARED_GATE_INPUTS))
    assert top_level == _DECLARED_GATE_INPUTS


def test_gate_inputs_restate_file_declared_gearing_and_leverage():
    """wd is documented spot gearing D/(D+E); net_debt_after_cash is the net leg."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "wd": 0.2392, "net_debt_after_cash": 96_939_936_180_000.0,
        "ebitda": 18_396_257_972_040.0,
    })
    assert gi["d_de_ratio"] == pytest.approx(0.2392)
    assert gi["net_debt_to_ebitda"] == pytest.approx(
        96_939_936_180_000.0 / 18_396_257_972_040.0, rel=1e-4)


def test_gross_debt_leg_is_not_used_for_leverage():
    """The file labels `net_debt` the GROSS bridge leg (cash is added back separately);
    without `net_debt_after_cash` the leverage input must stay absent, not be guessed."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "net_debt": 110_786_062_912_260.0, "ebitda": 18_396_257_972_040.0,
    })
    assert "net_debt_to_ebitda" not in gi


def test_file_declared_values_win_over_restatements():
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "wd": 0.2392, "net_debt_after_cash": 96_939_936_180_000.0,
        "ebitda": 18_396_257_972_040.0,
        "gate_inputs": {"d_de_ratio": 0.77, "net_debt_to_ebitda": 9.99},
    })
    assert gi["d_de_ratio"] == 0.77 and gi["net_debt_to_ebitda"] == 9.99


def test_absent_keys_stay_absent_no_invented_defaults():
    """LOUD policy: an assumptions dict without gate facts yields an EMPTY block."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    bare = {k: v for k, v in _assumptions().items() if k not in ("wd", "net_debt_after_cash")}
    assert _gate_inputs_from_assumptions(bare) == {}
    assert _gate_inputs_from_assumptions({}) == {}


# ------------------------------------------------------------------ live AMMN payload

@pytest.fixture(scope="module")
def ammn() -> dict:
    if not AMMN.exists():
        pytest.skip("data/assumptions/AMMN.json not present (AMMN data lane purged)")
    return json.loads(AMMN.read_text(encoding="utf-8"))


def test_ammn_live_payload_gate_inputs_are_file_backed(ammn: dict):
    """No gate input may appear on the payload that the file does not support."""
    from server.routers.pdf import _build_live_payload

    gi = _build_live_payload("AMMN", None)["gate_inputs"]
    nested: dict = dict(ammn.get("gate_inputs") or {})
    supported = set(nested) | {k for k in GATE_KEYS if ammn.get(k) is not None}
    supported |= {"domain"} | set(_RESTATED)
    assert set(gi) <= supported, f"payload invented gate inputs: {sorted(set(gi) - supported)}"

    if gi.get("d_de_ratio") is not None:
        assert gi["d_de_ratio"] == pytest.approx(float(ammn["wd"]))
    if gi.get("net_debt_to_ebitda") is not None:
        assert gi["net_debt_to_ebitda"] == pytest.approx(
            float(ammn["net_debt_after_cash"]) / float(ammn["ebitda"]), rel=1e-4)


def test_ammn_gate_stage_is_loud_about_the_keys_the_file_lacks(ammn: dict):
    """Current AMMN state: the gate stage must either clear (file supplies all 10) or
    halt loudly naming exactly the keys the file does not support. Self-clearing when
    the data lane extends AMMN.json."""
    from server.report.typst_renderer import _get_ticker_gate_params
    from server.routers.pdf import _build_live_payload

    gi = _build_live_payload("AMMN", None)["gate_inputs"]
    nested: dict = dict(ammn.get("gate_inputs") or {})
    unsupported = [k for k in GATE_KEYS
                   if k not in gi and k not in nested and ammn.get(k) is None]
    assert not [k for k in unsupported if k in gi], "loader invented a gate input"

    try:
        params = _get_ticker_gate_params("AMMN", dict(_build_live_payload("AMMN", None)))
    except ValueError as exc:
        assert unsupported, "renderer halted although the file supplied every gate input"
        named = str(exc)
        assert all(k in named for k in unsupported), named
    else:
        assert all(k in params for k in GATE_KEYS)
        assert params["domain"]


# ------------------------------------------------- file -> gate passthrough (end-to-end)

def test_unassisted_render_clears_gate_evaluation_when_the_file_supplies_inputs(
    tmp_path, monkeypatch
):
    """The production entrypoint, unassisted: no gate_inputs injected into the payload.

    The assumptions file (a tmp `data/assumptions/TESTX.json` — the loader's real
    source) carries the 10 keys, so render_report() must get PAST gate evaluation and
    publish the gate verdict. Only the later compile stage is stubbed.
    """
    from server.report import typst_renderer as tr

    (tmp_path / "TESTX.json").write_text(
        json.dumps(_assumptions(gate_inputs=dict(_DECLARED_GATE_INPUTS))), encoding="utf-8")

    from server.routers import pdf as pdf_router

    monkeypatch.setattr(pdf_router, "ASSUMPTIONS_DIR", tmp_path)
    cache = tmp_path / "cache"
    monkeypatch.setattr(tr, "CACHE_ROOT", cache)

    def _stub_compile(input_typ, output_pdf, data_path=None, ticker=None):  # noqa: ANN001
        pathlib.Path(output_pdf).write_bytes(b"%PDF-1.4\n%stub\n")
        return True

    monkeypatch.setattr(tr, "compile_typst", _stub_compile)

    out = tr.render_report("TESTX", archetype="single", out_path=tmp_path / "out.pdf")
    assert pathlib.Path(out).read_bytes().startswith(b"%PDF")

    rendered = json.loads((cache / "render_testx" / "report_data.json").read_text(encoding="utf-8"))
    assert rendered["gate_inputs"] == _DECLARED_GATE_INPUTS
    gate_verdict = rendered["gate-verdict"]
    # Gate 0 mining domain -> NAV primary, DCF secondary; 8y filing history -> not thin.
    assert gate_verdict["primary"] == "NAV"
    assert gate_verdict["secondary"] == "DCF"
    assert gate_verdict["thin_data"] is False
    assert len(gate_verdict["gates"]) == 6
    assert gate_verdict["gates"][0]["passed"] is True
