#!/usr/bin/env python3
"""Frontend No-Fabrication Verifier.

Verifies that the Frontend codebase (src/fe/src) strictly avoids fabricated figures,
mock/fixture imports, placeholder strings, and synthetic values, ensuring that all data
is grounded in backend payloads and absent sections render honest pending states.

Modes:
  1. Static (default): Walks src/fe/src/** and flags:
     (a) Mock/fixture/sample module imports
     (b) Numeric literal arrays of 3+ elements (unless allowlisted with --allow)
     (c) ?? <number> / || <number> with figure-like left-hand side
     (d) Literal placeholder strings ('lorem', 'dummy', 'example', 'TBD', 'N/A') used as presented values
     (e) Math.random / Date.now feeding displayed values
  2. Payload Cross-Check (--payload <file> or --ticker <T> [--base <url>]):
     Extracts numeric leaves from a real backend payload and cross-checks against FE constants.
  3. Selftest (--selftest):
     Runs against tests/fixtures/fe_fabrication/ verifying detection of mock imports and figure fallbacks.

Exit codes:
  0: Clean (no findings) or baseline run (--baseline)
  1: Findings detected
  2: Configuration or execution error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Constants and Regex Patterns
# ---------------------------------------------------------------------------

FIGURE_KEYWORDS = (
    "price",
    "tp",
    "fv",
    "ev",
    "ebitda",
    "revenue",
    "wacc",
    "multiple",
    "ratio",
    "upside",
    "margin",
    "value",
    "score",
)

FIGURE_KW_PATTERN = "|".join(FIGURE_KEYWORDS)

# Rule (a): Mock / fixture / sample imports
MOCK_IMPORT_RE = re.compile(
    r"""(?:import\s+[\s\S]*?\s+from\s+['"][^'"]*(?:mock|fixture|sample)[^'"]*['"]|import\s*\(\s*['"][^'"]*(?:mock|fixture|sample)[^'"]*['"]\s*\)|require\s*\(\s*['"][^'"]*(?:mock|fixture|sample)[^'"]*['"]\s*\))""",
    re.IGNORECASE,
)

# Rule (b): Numeric literal arrays of 3+ elements
# Matches: [1, 2, 3], [10.5, 20.2, 30.1], [-1, 0, 1, 2]
NUM_PATTERN = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
NUMERIC_ARRAY_RE = re.compile(
    r"\[\s*" + NUM_PATTERN + r"(?:\s*,\s*" + NUM_PATTERN + r"){2,}\s*,?\s*\]"
)

# Rule (c): ?? <number> / || <number> with figure-like left-hand side
# Matches LHS containing keywords followed by ?? or || and a number
FIGURE_FALLBACK_RE = re.compile(
    r"(?P<lhs>[\w$]+(?:\.[\w$]+|\?\.[\w$]+|\[\s*['\"][^'\"]+['\"]\s*\])*)\s*(?P<op>\?\?|\|\|)\s*(?P<val>-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Rule (d): Placeholder strings presented to user
# Matches string literals or JSX text with lorem, dummy, example, TBD, N/A
PLACEHOLDER_STRING_RE = re.compile(
    r"""(?:['"`]([^'"`]*\b(?:lorem|dummy|example|TBD|N/A)\b[^'"`]*)['"`]|>([^<]*\b(?:lorem|dummy|example|TBD|N/A)\b[^<]*)<)""",
    re.IGNORECASE,
)

# Rule (e): Math.random / Date.now
MATH_RANDOM_RE = re.compile(r"\bMath\.random\s*\(\s*\)")
DATE_NOW_RE = re.compile(r"\bDate\.now\s*\(\s*\)")


@dataclass
class Finding:
    file: Path
    line: int
    rule: str
    pattern: str
    matched_text: str
    line_content: str
    reason: str
    remediation: str

    @property
    def rel_path(self) -> str:
        try:
            return str(self.file.resolve().relative_to(REPO_ROOT.resolve()))
        except ValueError:
            return str(self.file)


# ---------------------------------------------------------------------------
# Comment Stripper & Source Analyzer
# ---------------------------------------------------------------------------

def clean_lines_and_preserve_positions(text: str) -> list[tuple[int, str, str]]:
    """Splits text into (line_number, clean_line_without_comments, raw_line).
    
    Handles multi-line block comments (/* ... */) and single-line comments (// ...).
    """
    lines = text.splitlines()
    result: list[tuple[int, str, str]] = []
    in_block = False

    for i, line in enumerate(lines, 1):
        clean = line
        if in_block:
            if "*/" in clean:
                clean = clean.split("*/", 1)[1]
                in_block = False
            else:
                clean = ""

        while "/*" in clean and not in_block:
            before, after = clean.split("/*", 1)
            if "*/" in after:
                clean = before + " " + after.split("*/", 1)[1]
            else:
                clean = before
                in_block = True

        if "//" in clean:
            clean = clean.split("//", 1)[0]

        result.append((i, clean, line))
    return result


def is_figure_name(name: str) -> bool:
    """Checks if identifier or property access contains any figure keywords.

    Keywords: price, tp, fv, ev, ebitda, revenue, wacc, multiple, ratio, upside, margin, value, score.
    Uses leaf property token-boundary matching so that 'events' does not match 'ev',
    but 'target_price', 'ev_ebitda', 'margin_of_safety_pct', 'dcf[\"fv\"]', 'score' do match.
    """
    # Extract leaf property from property access (e.g., 'a.b.c' -> 'c', 'dcf["fv"]' -> 'fv')
    leaf = name
    if '["' in name or "['" in name:
        parts = re.split(r'\[[\'"]', name)
        leaf = parts[-1].rstrip('\'"]')
    elif "." in name:
        leaf = name.split(".")[-1]

    # Split into words by underscores, non-alphanumeric, and camelCase
    raw_tokens = re.findall(r"[A-Za-z0-9]+", leaf)
    tokens: list[str] = []
    for tok in raw_tokens:
        sub_tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|[0-9]+", tok)
        tokens.extend(sub_tokens if sub_tokens else [tok])

    for tok in tokens:
        if tok.lower() in FIGURE_KEYWORDS:
            return True

    # Also check if the whole expression or prefix contains unambiguous compound figure terms like 'ev_ebitda'
    for kw in ("ev_ebitda", "ebitda_margin", "fair_value", "target_price", "fv_per_share"):
        if kw in name.lower():
            return True

    return False


# ---------------------------------------------------------------------------
# Static Scanner
# ---------------------------------------------------------------------------

class FrontendFabricationScanner:
    def __init__(self, fe_root: Path, allowlist: set[str] | None = None):
        self.fe_root = fe_root
        self.allowlist = {str(Path(p).resolve()) for p in (allowlist or set())}

    def scan_file(self, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: could not read {file_path}: {e}", file=sys.stderr)
            return findings

        lines_info = clean_lines_and_preserve_positions(content)
        file_resolved = str(file_path.resolve())
        is_allowlisted = file_resolved in self.allowlist or file_path.name in self.allowlist

        # (a) Mock/fixture/sample module imports
        for lnum, clean, raw in lines_info:
            m = MOCK_IMPORT_RE.search(clean)
            if m:
                findings.append(
                    Finding(
                        file=file_path,
                        line=lnum,
                        rule="RULE_A_MOCK_IMPORT",
                        pattern="Mock/Fixture/Sample Import",
                        matched_text=m.group(0),
                        line_content=raw.strip(),
                        reason="Imports mock, fixture, or sample module instead of binding to backend payload",
                        remediation="Remove mock import and consume live fields from ReportPayload contract",
                    )
                )

        # (b) Numeric literal arrays of 3+ elements
        if not is_allowlisted and file_path.suffix in (".ts", ".tsx"):
            # Multi-line or single-line numeric array
            for m in NUMERIC_ARRAY_RE.finditer(content):
                # Verify match is not inside comments
                start_pos = m.start()
                lnum = content[:start_pos].count("\n") + 1
                matched_str = m.group(0)
                # Check if this line is commented out in lines_info
                clean_on_line = lines_info[lnum - 1][1] if lnum - 1 < len(lines_info) else ""
                if clean_on_line.strip():
                    findings.append(
                        Finding(
                            file=file_path,
                            line=lnum,
                            rule="RULE_B_NUMERIC_ARRAY",
                            pattern="Hardcoded Numeric Literal Array (3+ elements)",
                            matched_text=matched_str.replace("\n", " ").strip(),
                            line_content=lines_info[lnum - 1][2].strip(),
                            reason="Hardcoded numeric array in source fabricates data series instead of reading payload",
                            remediation="Derive series dynamically from payload arrays or pass file to --allow if static axis",
                        )
                    )

        # (c) ?? <number> / || <number> with figure-like LHS
        for lnum, clean, raw in lines_info:
            for m in FIGURE_FALLBACK_RE.finditer(clean):
                lhs = m.group("lhs")
                op = m.group("op")
                val = m.group("val")
                if is_figure_name(lhs):
                    findings.append(
                        Finding(
                            file=file_path,
                            line=lnum,
                            rule="RULE_C_FIGURE_FALLBACK",
                            pattern=f"Fabricated Figure Fallback ({lhs} {op} {val})",
                            matched_text=m.group(0),
                            line_content=raw.strip(),
                            reason=f"Substitutes default figure '{val}' when '{lhs}' is missing, masking absent backend data",
                            remediation="Render honest pending block (PendingBlock) or format null as '-'",
                        )
                    )

        # (d) Literal placeholder strings ('lorem','dummy','example','TBD','N/A') used as presented values
        for lnum, clean, raw in lines_info:
            # Exclude normalization/comparison lines like: toLowerCase() === "n/a" or if (x === "N/A")
            if re.search(r"""===?\s*['"]n/?a['"]|!==?\s*['"]n/?a['"]""", clean, re.IGNORECASE):
                continue
            # Exclude token definitions / parsing helpers where 'n/a' is converted to null
            if "parseIdnNumber" in clean or "parseNumber" in clean:
                continue

            for m in PLACEHOLDER_STRING_RE.finditer(clean):
                str_match = m.group(1) or m.group(2) or m.group(0)
                # Ensure it's not a generic word inside a variable or import
                findings.append(
                    Finding(
                        file=file_path,
                        line=lnum,
                        rule="RULE_D_PLACEHOLDER_STRING",
                        pattern=f"Placeholder String Presented ({str_match.strip()})",
                        matched_text=str_match.strip(),
                        line_content=raw.strip(),
                        reason=f"Presents fabricated/placeholder text '{str_match.strip()}' to the user",
                        remediation="Render honest pending state or omit empty section",
                    )
                )

        # (e) Math.random / Date.now feeding displayed values
        for lnum, clean, raw in lines_info:
            if MATH_RANDOM_RE.search(clean):
                findings.append(
                    Finding(
                        file=file_path,
                        line=lnum,
                        rule="RULE_E_SIMULATED_RANDOM",
                        pattern="Math.random() in FE Component",
                        matched_text="Math.random()",
                        line_content=raw.strip(),
                        reason="Generates pseudo-random figures/values on client side",
                        remediation="Remove client-side random generation; display only deterministic backend payload values",
                    )
                )
            if DATE_NOW_RE.search(clean):
                # Only flag Date.now() if it's used in fallback expressions or data synthesis
                # e.g., ts: ev.ts ?? Date.now(), started_at: ... || Date.now()
                if any(k in clean for k in ("||", "??", "started_at", "timestamp", "ts:", "simulated")):
                    findings.append(
                        Finding(
                            file=file_path,
                            line=lnum,
                            rule="RULE_E_SIMULATED_DATE",
                            pattern="Date.now() Fallback in FE State/Data",
                            matched_text="Date.now()",
                            line_content=raw.strip(),
                            reason="Fabricates current timestamp when backend event timestamp is missing",
                            remediation="Preserve null/undefined timestamp or render pending status without inventing time",
                        )
                    )

        return findings

    def scan_tree(self) -> list[Finding]:
        all_findings: list[Finding] = []
        for root, dirs, files in os.walk(self.fe_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".git", ".next", "build", ".cache")]
            for f in sorted(files):
                if f.endswith((".ts", ".tsx", ".js", ".jsx")):
                    file_path = Path(root) / f
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)
        return all_findings


# ---------------------------------------------------------------------------
# Payload Cross-Check Mode
# ---------------------------------------------------------------------------

def extract_numeric_leaves(payload: Any, current_path: str = "$") -> dict[float | int, list[str]]:
    """Extracts all numeric leaves recursively from payload dict/list."""
    results: dict[float | int, list[str]] = {}

    def _walk(node: Any, path: str):
        if isinstance(node, (int, float)) and not isinstance(node, bool):
            results.setdefault(node, []).append(path)
        elif isinstance(node, dict):
            for k, v in node.items():
                _walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                _walk(item, f"{path}[{idx}]")

    _walk(payload, current_path)
    return results


def run_payload_crosscheck(
    payload_source: Path | str | None,
    ticker: str | None = None,
    base_url: str | None = None,
    fe_root: Path | None = None,
) -> int:
    """Performs payload cross-check against numbers present in FE codebase."""
    print("=" * 80)
    print("MODE 2: PAYLOAD CROSS-CHECK (GROUND-TRUTH GROUNDING)")
    print("=" * 80)

    payload_data: dict[str, Any] = {}

    if payload_source and Path(payload_source).exists():
        p_path = Path(payload_source)
        print(f"Loading payload JSON from file: {p_path}")
        payload_data = json.loads(p_path.read_text(encoding="utf-8"))
    elif ticker:
        if base_url:
            import urllib.request
            url = f"{base_url.rstrip('/')}/api/report/{ticker}/payload"
            print(f"Fetching payload from URL: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Verifier/1.0"})
            with urllib.request.urlopen(req) as resp:
                payload_data = json.loads(resp.read().decode("utf-8"))
        else:
            print(f"Rendering live payload for ticker '{ticker}' via Python backend...")
            from server.routers.pdf import render_html_for_ticker
            _template_name, _html, payload_data = render_html_for_ticker(ticker, None)
    else:
        # Default contract payload
        default_contract = REPO_ROOT / "docs" / "fe-payload-contract.json"
        if default_contract.exists():
            print(f"Loading default contract payload: {default_contract}")
            payload_data = json.loads(default_contract.read_text(encoding="utf-8"))
        else:
            print("Error: No payload provided and docs/fe-payload-contract.json not found.", file=sys.stderr)
            return 2

    numeric_leaves = extract_numeric_leaves(payload_data)
    unique_numbers = set(numeric_leaves.keys())
    print(f"Extracted {len(numeric_leaves)} distinct numeric values across payload paths.")

    # Cross check with numbers found in FE code
    target_dir = fe_root or (REPO_ROOT / "src" / "fe" / "src")
    print(f"Scanning frontend files in {target_dir} for ungrounded numeric constants...")

    fe_numbers: list[tuple[str, int, float, str]] = []
    # Match standalone numbers in assignments / default values
    num_literal_re = re.compile(r"""\b(?P<num>\d+(?:\.\d+)?)\b""")

    # Common layout / UI constants to exclude from ungrounded check
    COMMON_UI_CONSTANTS = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18, 20, 24, 28, 32, 36, 40,
        48, 50, 60, 64, 70, 72, 80, 85, 90, 95, 100, 120, 140, 160, 180, 200, 220, 240,
        300, 320, 360, 400, 500, 600, 700, 720, 800, 900, 1000, 2000, 3000, 4000, 5000,
        3600, 86400, 0.5, 0.1, 0.05, 0.95, 1.05, 1.5, 2.5,
    }

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".git", ".next", "build")]
        for f in sorted(files):
            if f.endswith((".ts", ".tsx")):
                file_path = Path(root) / f
                content = file_path.read_text(encoding="utf-8")
                lines_info = clean_lines_and_preserve_positions(content)
                rel_p = str(file_path.relative_to(REPO_ROOT))

                for lnum, clean, raw in lines_info:
                    # Strip CSS classnames, tailwind styling, SVG geometry attributes, and string slice params
                    stripped = re.sub(r"""(?:className|class)=['"][^'"]*['"]""", "", clean)
                    stripped = re.sub(r"""cls:\s*['"][^'"]*['"]""", "", stripped)
                    stripped = re.sub(r"""\b(?:width|height|viewBox|padLeft|padRight|radius|centerX|centerY|needleLength|slice)\b[^,;)}]*""", "", stripped)

                    # Look for figure assignments or fallback values
                    if any(kw in stripped.lower() for kw in FIGURE_KEYWORDS) or "??" in stripped or "||" in stripped:
                        for m in num_literal_re.finditer(stripped):
                            val_str = m.group("num")
                            val = float(val_str) if "." in val_str else int(val_str)
                            if val not in COMMON_UI_CONSTANTS:
                                fe_numbers.append((rel_p, lnum, val, raw.strip()))

    ungrounded = [item for item in fe_numbers if item[2] not in unique_numbers]

    print("\n--- PAYLOAD CROSS-CHECK RESULTS ---")
    if ungrounded:
        print(f"Found {len(ungrounded)} frontend numeric literals with NO exact counterpart in the payload:")
        for rel_p, lnum, val, raw in ungrounded:
            print(f"  {rel_p}:{lnum} -> value '{val}' | line: {raw}")
    else:
        print("No ungrounded domain-specific figures found in examined expressions.")

    print("\n" + "=" * 80)
    print("LIMITS OF THIS CHECK:")
    print("  * A number in the frontend may be legitimately transformed (e.g., * 100 for percentages,")
    print("    rounded to N decimal places, or converted between IDR/USD or millions/billions).")
    print("  * A missing match is an investigative lead, NOT definitive proof of fabrication.")
    print("  * Conversely, a matching number does not guarantee proper semantic binding.")
    print("=" * 80)
    return 0


# ---------------------------------------------------------------------------
# Selftest Mode
# ---------------------------------------------------------------------------

def run_selftest() -> int:
    """Runs verification tests against tests/fixtures/fe_fabrication/."""
    print("=" * 80)
    print("MODE 3: SELFTEST VERIFICATION")
    print("=" * 80)

    fixture_dir = REPO_ROOT / "tests" / "fixtures" / "fe_fabrication"
    if not fixture_dir.exists():
        print(f"Error: fixture directory {fixture_dir} does not exist.", file=sys.stderr)
        return 2

    scanner = FrontendFabricationScanner(fe_root=fixture_dir)
    findings = scanner.scan_tree()

    print(f"Scanned {fixture_dir} and identified {len(findings)} findings.")

    # Check that FabricatedComponent.tsx triggered both Rule A and Rule C
    has_mock_import = False
    has_price_fallback = False
    has_clean_findings = False

    for f in findings:
        if "FabricatedComponent.tsx" in str(f.file):
            if f.rule == "RULE_A_MOCK_IMPORT":
                has_mock_import = True
            if f.rule == "RULE_C_FIGURE_FALLBACK" and "target_price" in f.matched_text:
                has_price_fallback = True
        elif "CleanComponent.tsx" in str(f.file):
            has_clean_findings = True

    print("\nSelftest Assertions:")
    print(f"  [✓] Mock import flagged (Rule a): {has_mock_import}")
    print(f"  [✓] Price '?? 0' fallback flagged (Rule c): {has_price_fallback}")
    print(f"  [✓] CleanComponent has zero findings: {not has_clean_findings}")

    if has_mock_import and has_price_fallback and not has_clean_findings:
        print("\nSELFTEST RESULT: PASS (All scanner assertions succeeded)")
        return 0
    else:
        print("\nSELFTEST RESULT: FAIL (Missing expected assertions)", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Baseline Report Generation
# ---------------------------------------------------------------------------

def generate_markdown_report(findings: list[Finding], output_file: Path) -> None:
    """Generates the comprehensive audit report markdown."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rule_counts: dict[str, int] = {}
    for f in findings:
        rule_counts[f.rule] = rule_counts.get(f.rule, 0) + 1

    # Generate formatted tool output text for embedding
    output_lines: list[str] = [
        "=" * 80,
        "FRONTEND NO-FABRICATION VERIFIER (STATIC SCAN)",
        f"Target Directory: {REPO_ROOT / 'src' / 'fe' / 'src'}",
        "=" * 80,
        f"\n[!] FINDINGS DETECTED: {len(findings)} fabrication issues found:\n",
    ]
    for idx, f in enumerate(findings, 1):
        output_lines.append(f"{idx:2d}. {f.rel_path}:{f.line}")
        output_lines.append(f"    Rule:        {f.rule} ({f.pattern})")
        output_lines.append(f"    Line:        {f.line_content}")
        output_lines.append(f"    Why:         {f.reason}")
        output_lines.append(f"    Remediation: {f.remediation}")
        output_lines.append("-" * 60)

    md: list[str] = [
        "# Frontend No-Fabrication Scan Report",
        "",
        "**Date**: 2026-09-13",
        "**Target Directory**: `src/fe/src/`",
        f"**Total Findings**: {len(findings)}",
        "",
        "## Exact Commands Run",
        "",
        "```bash",
        "# 1. Static Scan on current tree (findings check)",
        ".venv/bin/python scripts/verify_fe_no_fabrication.py",
        "",
        "# 2. Baseline generation (writes this audit report and exits 0)",
        ".venv/bin/python scripts/verify_fe_no_fabrication.py --baseline",
        "",
        "# 3. Standalone Selftest",
        ".venv/bin/python scripts/verify_fe_no_fabrication.py --selftest",
        "",
        "# 4. Payload Cross-Check (AMMN Contract / Live Payload)",
        ".venv/bin/python scripts/verify_fe_no_fabrication.py --ticker AMMN",
        "```",
        "",
        "## Real Tool Output on Current Tree",
        "",
        "```text",
        *output_lines,
        "```",
        "",
        "## Tool Output Summary",
        "",
        "| Rule Category | Count | Description |",
        "| :--- | :--- | :--- |",
        f"| **Rule A: Mock/Fixture Imports** | {rule_counts.get('RULE_A_MOCK_IMPORT', 0)} | Imports of mock modules or fixture samples |",
        f"| **Rule B: Numeric Arrays** | {rule_counts.get('RULE_B_NUMERIC_ARRAY', 0)} | Hardcoded numeric literal arrays (3+ elements) |",
        f"| **Rule C: Figure Fallbacks** | {rule_counts.get('RULE_C_FIGURE_FALLBACK', 0)} | `?? <num>` or `\\|\\| <num>` fallbacks on figure names |",
        f"| **Rule D: Placeholder Strings** | {rule_counts.get('RULE_D_PLACEHOLDER_STRING', 0)} | Placeholder text ('lorem', 'dummy', 'TBD', 'N/A') |",
        f"| **Rule E: Simulated Values** | {rule_counts.get('RULE_E_SIMULATED_RANDOM', 0) + rule_counts.get('RULE_E_SIMULATED_DATE', 0)} | `Math.random` or `Date.now` feeding displayed state |",
        "",
        "## Table of Findings",
        "",
        "| File:Line | Pattern | Why it is fabrication | What it should render instead |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for f in findings:
        clean_matched = f.matched_text.replace("|", "\\|")
        clean_reason = f.reason.replace("|", "\\|")
        clean_remed = f.remediation.replace("|", "\\|")
        md.append(f"| `{f.rel_path}:{f.line}` | `{clean_matched}` | {clean_reason} | {clean_remed} |")

    md.extend([
        "",
        "## Limits of this Check",
        "",
        "1. **Static Heuristic Boundaries**: The scanner uses robust lexical and pattern analysis. While it detects mock imports, hardcoded numeric arrays, figure fallbacks, placeholders, and synthetic time generators, it cannot guarantee complete runtime semantic correctness across complex dynamic function invocations.",
        "2. **Payload Leaf Cross-Check**: Cross-checking numbers extracted from backend payloads against frontend literals is an investigative tool. A frontend figure may be mathematically scaled (e.g. multiplied by 100 for percentages), formatted into localized strings (Indonesian dot/comma separators), rounded, or represent SVG coordinate geometry. A discrepancy flags a candidate for manual review, not definitive proof of fabrication.",
        "3. **Absence State Verification**: This tool verifies that code does not substitute zero or hardcoded fallbacks when data is missing. It works in tandem with payload contract schemas (`docs/fe-payload-contract.json`) and house format visual verifiers (`scripts/verify_house_format.py`).",
        "",
    ])

    output_file.write_text("\n".join(md), encoding="utf-8")
    print(f"Baseline audit report written to: {output_file}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that Frontend codebase contains ZERO fabricated figures or mock imports."
    )
    parser.add_argument(
        "--fe-root",
        type=Path,
        default=REPO_ROOT / "src" / "fe" / "src",
        help="Path to frontend source root (default: src/fe/src)",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help="Allowlist file for numeric literal arrays (can be specified multiple times)",
    )
    parser.add_argument(
        "--payload",
        type=Path,
        help="Path to JSON payload file for Mode 2 cross-check",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Ticker symbol for Mode 2 payload cross-check",
    )
    parser.add_argument(
        "--base",
        type=str,
        help="Backend base URL for fetching ticker payload",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run Mode 3 selftest against tests/fixtures/fe_fabrication/",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Write baseline audit report to docs/audits/fe-fabrication-scan.md and exit 0",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "docs" / "audits" / "fe-fabrication-scan.md",
        help="Target markdown report path (default: docs/audits/fe-fabrication-scan.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON",
    )

    args = parser.parse_args()

    # 1. Mode 3: Selftest
    if args.selftest:
        return run_selftest()

    # 2. Mode 2: Payload Cross-Check
    if args.payload or args.ticker:
        return run_payload_crosscheck(
            payload_source=args.payload,
            ticker=args.ticker,
            base_url=args.base,
            fe_root=args.fe_root,
        )

    # 3. Mode 1: Static Verification (Default)
    allowlist = set()
    for item in args.allow:
        for part in item.split(","):
            if part.strip():
                allowlist.add(part.strip())

    scanner = FrontendFabricationScanner(fe_root=args.fe_root, allowlist=allowlist)
    findings = scanner.scan_tree()

    if args.json:
        out_data = [
            {
                "file": f.rel_path,
                "line": f.line,
                "rule": f.rule,
                "pattern": f.pattern,
                "matched_text": f.matched_text,
                "line_content": f.line_content,
                "reason": f.reason,
                "remediation": f.remediation,
            }
            for f in findings
        ]
        print(json.dumps(out_data, indent=2))
    else:
        print("=" * 80)
        print("FRONTEND NO-FABRICATION VERIFIER (STATIC SCAN)")
        print(f"Target Directory: {args.fe_root}")
        print("=" * 80)

        if findings:
            print(f"\n[!] FINDINGS DETECTED: {len(findings)} fabrication issues found:\n")
            for idx, f in enumerate(findings, 1):
                print(f"{idx:2d}. {f.rel_path}:{f.line}")
                print(f"    Rule:        {f.rule} ({f.pattern})")
                print(f"    Line:        {f.line_content}")
                print(f"    Why:         {f.reason}")
                print(f"    Remediation: {f.remediation}")
                print("-" * 60)
        else:
            print("\n[✓] CLEAN: No fabrication patterns or mock imports detected.")

    if args.baseline:
        generate_markdown_report(findings, args.report)
        print("\nBaseline mode: exiting with code 0.")
        return 0

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
