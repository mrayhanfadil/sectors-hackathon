"""
Adversarial Red Team Agent - agents/adversarial.py
Lane T09 (plan.md §3, §11).

Internal duel pre-PDF + User challenge post-PDF.
Anti-sycophancy: defender must defend with evidence (calc_* + exhibit) or concede with correction.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from scripts.adversarial import challenge, run_internal_duel


async def run_adversarial(ticker: str) -> Dict[str, Any]:
    """Runs internal duel for a ticker and returns debate summary."""
    rounds = await run_internal_duel(ticker)
    return {
        "ticker": ticker.upper(),
        "rounds": rounds,
        "verdict": "PASS" if all(r.get("verdict") == "defend" for r in rounds) else "REVISE",
        "provenance": "Adversarial Red Team 2-round duel (anti-sycophancy)",
    }


def adversarial_as_tool() -> Dict[str, Any]:
    return {
        "name": "adversarial_challenge",
        "description": "Challenge a claim against deterministic valuation and operational evidence",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "claim": {"type": "string"},
            },
            "required": ["ticker", "claim"],
        },
    }

