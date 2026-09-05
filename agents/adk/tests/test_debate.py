"""Unit tests for agents.adk.debate.validate_debate (structured-duel guard).

Run: .venv/bin/python -m pytest agents/adk/tests/test_debate.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.adk.debate import validate_debate

VALID = [
    {
        "round": 1,
        "challenger": "WACC 9.67% too low vs peers",
        "claim": "beta 0.6 understates retail risk",
        "defense": {
            "mode": "defend",
            "calc_refs": ["calc_wacc(beta=0.6) -> 9.67%", "calc_dcf +/-100bps"],
            "sources": [{"url": "https://example.com/x", "date": "2026-09-04"}],
        },
        "verdict": "hold",
    }
]


def test_valid_round_passes():
    ok, errors = validate_debate(VALID)
    assert ok, errors


def test_fenced_json_passes():
    import json

    ok, errors = validate_debate("```json\n" + json.dumps(VALID) + "\n```")
    assert ok, errors


def test_dict_wrapper_passes():
    ok, errors = validate_debate({"debate": VALID})
    assert ok, errors


def test_placeholder_strings_fail():
    for bad in [
        "Red-team challenge in progress — stress-testing WACC.",
        "Red-team review complete — exiting the loop.",
        "",
        "agree, looks good",
    ]:
        ok, errors = validate_debate(bad)
        assert not ok, f"should fail: {bad!r}"
        assert errors


def test_empty_rounds_fail():
    ok, errors = validate_debate([])
    assert not ok and errors


def test_missing_calc_refs_fails():
    import copy

    bad = copy.deepcopy(VALID)
    bad[0]["defense"]["calc_refs"] = []
    ok, errors = validate_debate(bad)
    assert not ok
    assert any("calc_refs" in e for e in errors)


def test_missing_source_date_fails():
    import copy

    bad = copy.deepcopy(VALID)
    bad[0]["defense"]["sources"] = [{"url": "https://example.com/x"}]
    ok, errors = validate_debate(bad)
    assert not ok
    assert any("url+date" in e for e in errors)


def test_missing_round_key_fails():
    import copy

    bad = copy.deepcopy(VALID)
    del bad[0]["verdict"]
    ok, errors = validate_debate(bad)
    assert not ok
    assert any("verdict" in e for e in errors)


def test_submit_debate_tool():
    import json

    from agents.adk.debate import submit_debate

    good = submit_debate(json.dumps(VALID))
    assert good == {"ok": True, "n_rounds": 1}
    bad = submit_debate("Red-team review complete — exiting the loop.")
    assert bad["ok"] is False
    assert bad["errors"]


def _ev(calls=None, resps=None):
    return {"function_calls": calls or [], "function_responses": resps or []}


def test_extract_accepted_debate():
    import json

    from agents.adk.debate import extract_accepted_debate

    call = {"name": "submit_debate", "args": {"debate_json": json.dumps(VALID)}}
    ok_resp = {"name": "submit_debate", "response": {"ok": True, "n_rounds": 1}}
    # accepted (same event)
    out = extract_accepted_debate([_ev([call], [ok_resp])])
    assert out == VALID
    # accepted (realistic shape: call at seq N, response at seq N+1)
    out = extract_accepted_debate([_ev([call], []), _ev([], [ok_resp])])
    assert out == VALID
    # ok:false -> None
    out = extract_accepted_debate(
        [_ev([call], [{"name": "submit_debate", "response": {"ok": False, "errors": ["x"]}}])]
    )
    assert out is None
    # no submit at all -> None
    assert extract_accepted_debate([_ev()]) is None
    assert extract_accepted_debate([]) is None
    # last-wins: bad first, good second
    bad_call = {"name": "submit_debate", "args": {"debate_json": "nonsense"}}
    out = extract_accepted_debate(
        [
            _ev([bad_call], [{"name": "submit_debate", "response": {"ok": False, "errors": ["e"]}}]),
            _ev([call], [ok_resp]),
        ]
    )
    assert out == VALID
