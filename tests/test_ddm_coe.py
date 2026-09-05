"""DDM/CoE lock — every calc_ddm caller must discount at cost_of_equity, never WACC.

Covers:
  1. calc_ddm discounts at CoE: hand-recomputed Gordon case + WACC-contrast.
  2. Signature lock: no `wacc` parameter on any DDM entry point.
  3. Caller scan (AST): no repo Python file passes a `wacc` variable/keyword
     into calc_ddm / engines.ddm / ddm_engine.ddm.
  4. Cross-engine agreement: finance_tools.calc_ddm == server.engines.ddm ==
     scripts/ddm_engine CLI (all CoE-discounted).
  5. Prompt discipline: modeler instructions forbid WACC -> calc_ddm.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.adk.tools.finance_tools import calc_ddm  # noqa: E402
from server.engines import ddm as engines_ddm  # noqa: E402
from scripts.ddm_engine import ddm as script_ddm  # noqa: E402


# ---------- 1. Hand-recomputed Gordon case ----------

def test_calc_ddm_discounts_at_coe_hand_recomputed():
    dividends = [10.0, 11.0]
    coe = 0.12
    g = 0.03
    # Independent hand recomputation (Gordon DDM, NOT via calc_ddm):
    pv1 = 10.0 / 1.12
    pv2 = 11.0 / (1.12 ** 2)
    tv = 11.0 * 1.03 / (0.12 - 0.03)
    pv_tv = tv / (1.12 ** 2)
    expected_fv = pv1 + pv2 + pv_tv  # ~118.05

    out = calc_ddm(dividends=dividends, cost_of_equity=coe, terminal_growth=g)
    assert "error" not in out
    assert out["fair_value_per_share"] == pytest.approx(expected_fv, abs=0.02)
    assert out["inputs"]["cost_of_equity"] == pytest.approx(coe)


def test_calc_ddm_result_differs_from_wacc_discounting():
    """Proves the discount rate IS CoE: same cash flows at WACC give another number."""
    dividends = [10.0, 11.0]
    coe, wacc, g = 0.12, 0.08, 0.03
    out = calc_ddm(dividends=dividends, cost_of_equity=coe, terminal_growth=g)
    # Hand recomputation at WACC (what a WACC-misuse bug would produce):
    wacc_fv = (
        10.0 / 1.08 + 11.0 / (1.08 ** 2)
        + (11.0 * 1.03 / (0.08 - 0.03)) / (1.08 ** 2)
    )
    assert out["fair_value_per_share"] != pytest.approx(wacc_fv, abs=1.0)


# ---------- 2. Signature lock ----------

def test_ddm_signatures_have_no_wacc():
    for fn, coe_param in ((calc_ddm, "cost_of_equity"), (engines_ddm, "coe"), (script_ddm, "coe")):
        params = inspect.signature(fn).parameters
        assert coe_param in params, f"{fn.__name__} missing {coe_param}"
        assert "wacc" not in params, f"{fn.__name__} must not accept wacc"
        assert "wacc_val" not in params, f"{fn.__name__} must not accept wacc_val"


# ---------- 3. Caller scan: no variable named wacc flows into DDM ----------

_DDM_CALL_NAMES = {"calc_ddm", "ddm"}

def _ddm_calls_with_wacc(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if name not in _DDM_CALL_NAMES:
            continue
        for kw in node.keywords:
            if kw.arg in ("wacc", "wacc_val", "cost_of_debt"):
                hits.append(f"{path}:{node.lineno} keyword '{kw.arg}' passed to {name}()")
            if isinstance(kw.value, ast.Name) and kw.value.id == "wacc":
                hits.append(f"{path}:{node.lineno} variable 'wacc' passed as '{kw.arg}' to {name}()")
        for arg in node.args:
            if isinstance(arg, ast.Name) and arg.id == "wacc":
                hits.append(f"{path}:{node.lineno} variable 'wacc' passed positionally to {name}()")
    return hits


def test_no_caller_passes_wacc_into_ddm():
    violations = []
    for sub in ("agents", "server", "scripts", "templates", "tests"):
        root = REPO_ROOT / sub
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            violations.extend(_ddm_calls_with_wacc(path))
    assert violations == [], "DDM callers passing WACC:\n" + "\n".join(violations)


# ---------- 4. Cross-engine agreement (all CoE) ----------

def test_engines_agree_on_coe_discounting():
    dividends = [10.0, 11.0]
    a = calc_ddm(dividends=dividends, cost_of_equity=0.12, terminal_growth=0.03)
    b = engines_ddm(dividends, 0.12, 0.03)
    c = script_ddm(dividends, 0.12, 0.03)
    assert a["fair_value_per_share"] == pytest.approx(b["fv_per_share"], abs=0.02)
    assert a["fair_value_per_share"] == pytest.approx(c["fv_per_share"], abs=0.02)


def test_ddm_cli_uses_coe_flag():
    src = (REPO_ROOT / "scripts" / "ddm_engine.py").read_text()
    assert "--coe" in src
    assert "--wacc" not in src
    proc = subprocess.run(
        [sys.executable, "scripts/ddm_engine.py",
         "--dividends", "10,11", "--coe", "0.12", "--g", "0.03"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    import json
    out = json.loads(proc.stdout)
    ref = calc_ddm(dividends=[10.0, 11.0], cost_of_equity=0.12, terminal_growth=0.03)
    assert out["fv_per_share"] == pytest.approx(ref["fair_value_per_share"], abs=0.02)


# ---------- 5. Prompt discipline ----------

def test_modeler_instructions_forbid_wacc_to_ddm():
    src = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text()
    assert "Never pass WACC to calc_ddm" in src
    assert "calc_ddm(dividends, cost_of_equity" in src
