"""AMMN-R2D proof harness — unassisted render_report('AMMN') gate stage.

Run:  .venv/bin/python output/ammn_r2d_proof.py
Prints a machine-readable block so the run can be pasted into a kanban handoff.
No Sectors billing: reads data/assumptions/AMMN.json only.
"""
from __future__ import annotations

import json
import pathlib
import sys
import traceback

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from server.routers import pdf as pdf_router  # noqa: E402
from server.report import typst_renderer as tr  # noqa: E402
from agents.valuation import gates as gate_mod  # noqa: E402

GATE_KEYS = tr._GATE_REQUIRED_KEYS

# 1. payload gate_inputs block (file -> payload passthrough)
payload = pdf_router._build_live_payload("AMMN", None)
gi = payload.get("gate_inputs") or {}
assum = json.loads((REPO / "data" / "assumptions" / "AMMN.json").read_text(encoding="utf-8"))

print("== payload gate_inputs ==")
print(json.dumps(gi, indent=2, ensure_ascii=False, default=str))
print("keys supplied:", sorted(gi))
print("keys required:", list(GATE_KEYS))
print("keys still absent:", [k for k in GATE_KEYS if k not in gi])

# 2. gate param extraction + evaluate (the production gate stage)
print("\n== _get_ticker_gate_params ==")
try:
    params = tr._get_ticker_gate_params("AMMN", payload)
except ValueError as exc:
    print("HALT ValueError:", exc)
    params = None
else:
    print("params:", json.dumps(params, indent=2, ensure_ascii=False, default=str))
    verdict = gate_mod.evaluate("AMMN", **params)
    print("verdict.primary:", verdict.primary)
    print("verdict.secondary:", verdict.secondary)
    print("gates_passed:", verdict.gates_passed)
    print("gates_failed:", verdict.gates_failed)

# 3. unassisted render_report('AMMN') — full production entrypoint
print("\n== render_report('AMMN') ==")
try:
    out = tr.render_report("AMMN")
except Exception as exc:  # noqa: BLE001
    print(f"HALT {type(exc).__name__}: {exc}")
    if not isinstance(exc, ValueError):
        traceback.print_exc()
else:
    print("RENDERED:", out)

# 4. what the assumptions file itself supplies for the 10 gate keys
print("\n== assumptions file gate coverage ==")
nested = assum.get("gate_inputs") if isinstance(assum.get("gate_inputs"), dict) else {}
for k in GATE_KEYS:
    where = "gate_inputs block" if k in nested else ("top level" if k in assum else "ABSENT")
    print(f"  {k:24s} {where}")
