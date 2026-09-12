#!/usr/bin/env python3
r"""scripts/harness_post_agy.py — Post-AGY dispatch recovery harness.

Validates any post-AGY change against public API, behavioral, test,
naming, and font invariants in under 10 seconds.
Exits 0 on PASS, exits non-zero on any failure.
"""

from __future__ import annotations

import inspect
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def check_python_api() -> tuple[bool, str, list[str]]:
    """Verify Python public API invariants:
    1. Import evaluate, GateVerdict, and 10 DOMAIN_* constants from agents.valuation.gates
    2. evaluate() signature accepts required kwargs
    3. Import adjust_assumptions from agents.valuation.assumptions
    4. agents.adk.agents.instructions contains evaluate, adjust_assumptions, DISCOUNT-RATE DISCIPLINE
    """
    errors: list[str] = []

    # 1. Imports from agents.valuation.gates
    required_gates_symbols = [
        "evaluate",
        "GateVerdict",
        "DOMAIN_BANK",
        "DOMAIN_INSURANCE",
        "DOMAIN_MULTIFINANCE",
        "DOMAIN_SECURITIES",
        "DOMAIN_REIT",
        "DOMAIN_MINING",
        "DOMAIN_OIL_GAS",
        "DOMAIN_PLANTATION",
        "DOMAIN_HOLDING_DISSIMILAR",
        "DOMAIN_SINGLE_BUSINESS",
    ]

    gates_mod = None
    try:
        import agents.valuation.gates as gates_mod

        for sym in required_gates_symbols:
            if not hasattr(gates_mod, sym):
                errors.append(f"agents.valuation.gates missing '{sym}'")
    except (ImportError, AttributeError, Exception) as e:  # noqa: BLE001
        errors.append(f"Cannot import from agents.valuation.gates: {e}")

    # 2. evaluate() signature parameter presence
    if gates_mod and hasattr(gates_mod, "evaluate"):
        evaluate_fn = gates_mod.evaluate
        sig = inspect.signature(evaluate_fn)
        expected_params = [
            "ticker",
            "domain",
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
            "upside_pct",
            "terminal_value_pct_of_ev",
        ]
        missing_params = [p for p in expected_params if p not in sig.parameters]
        if missing_params:
            errors.append(f"evaluate() missing expected parameters: {missing_params}")

    # 3. Import adjust_assumptions
    try:
        import agents.valuation.assumptions as assumptions_mod

        if not hasattr(assumptions_mod, "adjust_assumptions"):
            errors.append("agents.valuation.assumptions missing 'adjust_assumptions'")
    except (ImportError, AttributeError, Exception) as e:  # noqa: BLE001
        errors.append(f"Cannot import from agents.valuation.assumptions: {e}")

    # 4. Agent instructions invariant
    instructions_file = REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py"
    if not instructions_file.exists():
        errors.append(f"Instructions file not found: {instructions_file}")
    else:
        try:
            content = instructions_file.read_text(encoding="utf-8")
            for token in ["evaluate", "adjust_assumptions", "DISCOUNT-RATE DISCIPLINE"]:
                if token not in content:
                    errors.append(f"agents.adk.agents.instructions missing '{token}'")
        except OSError as e:
            errors.append(f"Error reading instructions.py: {e}")

    if errors:
        return False, f"python_api: FAIL ({'; '.join(errors)})", errors
    return True, "python_api: PASS (gates + assumptions + 11 constants)", []


def check_tests() -> tuple[bool, str, list[str]]:
    """Verify test invariants:
    1. pytest --co -q must collect >=90 tests
    2. pytest agents/valuation/ scripts/test_audit_quintet.py must pass 0 failures
    """
    errors: list[str] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    # 1. pytest --co -q
    co_cmd = [sys.executable, "-m", "pytest", "--co", "-q"]
    collected = 0
    try:
        res_co = subprocess.run(
            co_cmd,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        combined_co = res_co.stdout + "\n" + res_co.stderr
        match = re.search(r"(\d+)\s+tests?\s+collected", combined_co)
        if not match:
            match = re.search(r"collected\s+(\d+)\s+items", combined_co)

        if match:
            collected = int(match.group(1))
        else:
            lines = [line for line in res_co.stdout.splitlines() if "::" in line]
            collected = len(lines)

        if collected < 90:
            errors.append(f"collected {collected} tests (< 90 required)")
        if res_co.returncode != 0 and collected < 90:
            errors.append(f"pytest --co returned code {res_co.returncode}")
    except (subprocess.SubprocessError, OSError) as e:
        errors.append(f"pytest --co failed: {e}")

    # 2. pytest agents/valuation/ scripts/test_audit_quintet.py
    test_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "agents/valuation/",
        "scripts/test_audit_quintet.py",
        "-q",
    ]
    failed_count = 0
    try:
        res_test = subprocess.run(
            test_cmd,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        if res_test.returncode != 0:
            match_fail = re.search(r"(\d+)\s+failed", res_test.stdout)
            failed_count = int(match_fail.group(1)) if match_fail else 1
            errors.append(
                f"pytest agents/valuation/ scripts/test_audit_quintet.py had {failed_count} failure(s)"
            )
    except (subprocess.SubprocessError, OSError) as e:
        errors.append(f"pytest test run failed: {e}")
        failed_count = 1

    if errors:
        return False, f"tests: FAIL ({'; '.join(errors)})", errors
    return True, f"tests: PASS ({collected} collected, {failed_count} failed)", []


def check_naming() -> tuple[bool, str, list[str]]:
    r"""Verify naming invariants:
    1. grep -rn "\.IJ\b" templates/ server/routers/ docs/ references/ src/ must be empty
    2. no <h1..h4> heading in templates/*.html uses the retired section wording
       ("Risks and Catalysts", "Key Takeaways")
    """
    errors: list[str] = []

    # 1. No .IJ suffix
    ij_regex = re.compile(r"\.IJ\b")
    search_dirs = ["agents", "data", "docs", "references", "scripts", "server", "src", "templates", "tests"]
    ij_matches: list[str] = []

    for d in search_dirs:
        p = REPO_ROOT / d
        if not p.exists():
            continue
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in files:
            if (
                "__pycache__" in f.parts
                or f.name in {"harness_post_agy.py", "test_naming.py"}
                or f.suffix in {
                    ".png",
                    ".jpg",
                    ".ttf",
                    ".pdf",
                    ".pyc",
                    ".ico",
                    ".woff",
                    ".woff2",
                    ".db",
                    ".sqlite",
                    ".sqlite3",
                    ".webp",
                    ".zip",
                    ".gz",
                }
            ):
                continue
            try:
                raw = f.read_bytes()
                if b"\x00" in raw[:4096]:
                    continue
                content = raw.decode("utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if ij_regex.search(line):
                        rel = f.relative_to(REPO_ROOT)
                        ij_matches.append(f"{rel}:{line_idx}")
            except OSError:
                continue

    if ij_matches:
        errors.append(f"found .IJ suffix in: {', '.join(ij_matches[:5])}")

    # 2. Retired section wording must not survive as a HEADING in the report templates.
    #    Matching headings (not any occurrence) keeps this honest: the phrases are legitimate
    #    inside an inline Jinja comment or in templates/DATA_CONTRACT.md, which documents which
    #    archetype adds which block, and neither is a printed section title.
    retired_heading_regex = re.compile(
        r"<h[1-4][^>]*>[^<]*\b(?:Risks and Catalysts|Key Takeaways)\b", re.IGNORECASE
    )
    wording_matches: list[str] = []
    template_root = REPO_ROOT / "templates"

    if template_root.exists():
        for f in sorted(template_root.rglob("*.html")):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if retired_heading_regex.search(line):
                        rel = f.relative_to(REPO_ROOT)
                        wording_matches.append(f"{rel}:{line_idx}")
            except OSError:
                continue

    if wording_matches:
        errors.append(f"found old section wording in: {', '.join(wording_matches[:5])}")

    if errors:
        return False, f"naming: FAIL ({'; '.join(errors)})", errors
    return True, "naming: PASS (0 .IJ, 0 retired section headings)", []


def check_fonts() -> tuple[bool, str, list[str]]:
    """Verify font invariants:
    - assets/fonts/SourceSerif4-VF.ttf exists
    - assets/fonts/Inter-VF.ttf exists
    - assets/fonts/JetBrainsMono-VF.ttf exists
    """
    errors: list[str] = []
    required_fonts = [
        "assets/fonts/SourceSerif4-VF.ttf",
        "assets/fonts/Inter-VF.ttf",
        "assets/fonts/JetBrainsMono-VF.ttf",
    ]
    present_count = 0
    for rel_path in required_fonts:
        f = REPO_ROOT / rel_path
        if not f.is_file():
            errors.append(f"missing font: {rel_path}")
        else:
            present_count += 1

    if errors:
        return False, f"fonts: FAIL ({'; '.join(errors)})", errors
    return True, f"fonts: PASS ({present_count} corporate fonts present)", []


def main() -> int:
    checks = [
        ("python_api", check_python_api),
        ("tests", check_tests),
        ("naming", check_naming),
        ("fonts", check_fonts),
    ]

    results = []
    has_failure = False

    for name, check_fn in checks:
        passed, msg, errors = check_fn()
        results.append((name, passed, msg, errors))
        if not passed:
            has_failure = True

    if not has_failure:
        print("HARNESS-RESULT: PASS")
        for _, _, msg, _ in results:
            print(f"  {msg}")
        return 0
    else:
        print("HARNESS-RESULT: FAIL")
        for name, passed, msg, errors in results:
            if not passed:
                print(f"  {msg}")
            else:
                print(f"  {name}: PASS")
        return 1


if __name__ == "__main__":
    sys.exit(main())
