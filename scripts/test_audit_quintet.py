"""Pytest wrapper for scripts/audit_quintet_gates.py — exercises all 5 quintet tickers.

Runs the audit script (which has all 5 expectations hardcoded) as a subprocess and
asserts on its exit code + output. The audit script imports from agents.valuation.gates
itself, so this also indirectly verifies the gate runner public API is intact.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_quintet_gates.py"


@pytest.fixture(scope="module")
def audit_result() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def test_audit_exits_zero(audit_result):
    assert audit_result.returncode == 0, (
        f"Audit script failed (rc={audit_result.returncode}):\n"
        f"STDOUT:\n{audit_result.stdout}\n"
        f"STDERR:\n{audit_result.stderr}"
    )


def test_audit_summary_line_present(audit_result):
    assert "ALL QUINTET TICKERS MATCH EXPECTED METHOD VERDICTS" in audit_result.stdout


@pytest.mark.parametrize("ticker", ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"])
def test_audit_lists_each_ticker(audit_result, ticker: str):
    assert ticker in audit_result.stdout


def test_cdia_thin_data_in_audit_output(audit_result):
    """CDIA verdict must include the thin-data disclosure marker."""
    # The audit table shows `True` under the Thin column for CDIA
    cdia_line = next(
        (line for line in audit_result.stdout.splitlines() if line.startswith("CDIA")),
        None,
    )
    assert cdia_line is not None, "CDIA line not found in audit output"
    assert "True" in cdia_line, f"CDIA should be marked thin=True, got: {cdia_line}"


def test_bbcA_ddm_in_audit_output(audit_result):
    """BBCA verdict must show DDM as primary method."""
    bbca_line = next(
        (line for line in audit_result.stdout.splitlines() if line.startswith("BBCA")),
        None,
    )
    assert bbca_line is not None, "BBCA line not found in audit output"
    assert "DDM / Excess Return" in bbca_line
