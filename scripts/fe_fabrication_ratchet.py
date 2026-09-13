#!/usr/bin/env python3
"""Ratchet the no-fabrication scanner: the current findings are judged and documented, anything new fails.

The scanner is a heuristic — it cannot tell an axis-tick fraction from an invented data series, or the agent page's
own elapsed-time clock from a fabricated timestamp. Judging every hit by hand is right once and useless at scale, so
each hit is recorded here with a reason and the gate compares against this file: a finding that is not on the list is
a regression, and a listed finding that disappears is also reported (the list must not rot).

    .venv/bin/python scripts/fe_fabrication_ratchet.py            # compare, exit 1 on an unknown finding
    .venv/bin/python scripts/fe_fabrication_ratchet.py --update   # accept the current set (re-judge first!)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KNOWN = ROOT / "scripts/fe_fabrication_known_safe.json"
SCANNER = ROOT / "scripts/verify_fe_no_fabrication.py"
ALLOW = ROOT / "scripts/fe_fabrication_allowlist.txt"

# Judged by hand, by surface. A reason is mandatory: "it was already there" is not a reason.
REASONS = {
    "PeersCharts.tsx:251:RULE_B_NUMERIC_ARRAY":
        "axis tick fractions (1.0 / 0.5 / 0.0 of the plot height) — the same fractions the PDF's SVG macro draws; "
        "no series is invented from them",
    "PerformanceQuadrants.tsx:103:RULE_B_NUMERIC_ARRAY":
        "axis tick fractions for the growth panel; the plotted values come from the payload",
    "PerformanceQuadrants.tsx:138:RULE_B_NUMERIC_ARRAY":
        "axis tick fractions for the margin panel; the plotted values come from the payload",
    "DcfSpreadCharts.tsx:81:RULE_C_FIGURE_FALLBACK":
        "layout scale only (Math.max of the bars with a floor of 1); both the market-price label and its reference "
        "line are rendered only when the price is non-null, so no figure is ever defaulted",
    "routeTree.gen.ts:14:RULE_A_MOCK_IMPORT":
        "generated router tree (TanStack codegen) referencing the demo route — no value is imported from it",
    "DividendTimeline.tsx:22:RULE_D_PLACEHOLDER_STRING":
        "the mock-sectors demo surface, not the report page: the route exists to show synthetic data",
    "NewsFeedCard.tsx:28:RULE_D_PLACEHOLDER_STRING":
        "the mock-sectors demo surface, not the report page",
    "QuarterlyTrendChart.tsx:65:RULE_D_PLACEHOLDER_STRING":
        "the mock-sectors demo surface, not the report page",
    "QuarterlyTrendChart.tsx:326:RULE_D_PLACEHOLDER_STRING":
        "the mock-sectors demo surface, not the report page",
    "QuarterlyTrendChart.tsx:622:RULE_D_PLACEHOLDER_STRING":
        "the mock-sectors demo surface, not the report page",
    "agent.tsx:71:RULE_E_SIMULATED_DATE":
        "the agent page's own wall clock for elapsed time, not a market figure",
    "agent.tsx:312:RULE_E_SIMULATED_DATE":
        "the agent page's own wall clock for elapsed time, not a market figure",
    "agent.tsx:528:RULE_E_SIMULATED_DATE":
        "the agent page's own wall clock for elapsed time, not a market figure",
    "agent.tsx:570:RULE_E_SIMULATED_DATE":
        "the agent page's own wall clock for elapsed time, not a market figure",
}


def scan() -> list[dict]:
    cmd = [sys.executable, str(SCANNER), "--json"]
    if ALLOW.exists():
        cmd += ["--allow", str(ALLOW)]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout
    start = out.find("[")
    return json.loads(out[start:]) if start >= 0 else []


def key(finding: dict) -> str:
    path = pathlib.Path(finding.get("file", ""))
    return f"{path.name}:{finding.get('line')}:{finding.get('rule')}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="record the current findings as the accepted set")
    args = ap.parse_args()

    findings = scan()
    present = {key(f): f for f in findings}

    if args.update:
        payload = {k: {"reason": REASONS.get(k, "NOT JUDGED — write a reason before accepting"), **v}
                   for k, v in present.items()}
        KNOWN.write_text(json.dumps(payload, indent=2))
        unjudged = [k for k in payload if payload[k]["reason"].startswith("NOT JUDGED")]
        print(f"recorded {len(payload)} findings in {KNOWN.name}")
        if unjudged:
            print(f"  {len(unjudged)} have no judgement yet:")
            for k in unjudged:
                print(f"    {k}")
        return 0

    known = json.loads(KNOWN.read_text()) if KNOWN.exists() else {}
    new = sorted(set(present) - set(known))
    gone = sorted(set(known) - set(present))

    print(f"scanner findings: {len(present)} · judged safe: {len(known)}")
    for k in new:
        line = present[k].get("line_text") or present[k].get("line") or ""
        print(f"  NEW FABRICATION CANDIDATE  {k}\n      {str(line).strip()[:120]}")
    for k in gone:
        print(f"  no longer found (remove from {KNOWN.name}): {k}")

    if new:
        print("\nA new finding is not automatically fabrication — judge it, add a reason, then --update.")
        return 1
    if gone:
        print("\nNo new fabrication, but the accepted list is stale.")
    else:
        print("no new fabrication candidate on any surface")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
