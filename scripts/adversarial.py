"""
Scripts Shim: Adversarial Red Team — T09
Exposes challenge() and run_duel() for FastAPI backend server and CLI runners.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "agents"))

try:
    from adversarial import challenge as agent_challenge, run_duel as agent_run_duel  # type: ignore
except ImportError:
    from agents.adversarial import challenge as agent_challenge, run_duel as agent_run_duel  # type: ignore


async def challenge(ticker: str, claim: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Async endpoint interface for /api/challenge router."""
    return await agent_challenge(ticker, claim, context)


def run_duel(ticker: str, max_rounds: int = 2) -> Dict[str, Any]:
    """Runs 2-round duel and returns debate dictionary."""
    return agent_run_duel(ticker, max_rounds=max_rounds)


if __name__ == "__main__":
    import json
    tk = sys.argv[1] if len(sys.argv) > 1 else "RATU"
    if len(sys.argv) > 2:
        clm = sys.argv[2]
        res = asyncio.run(challenge(tk, clm))
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        res = run_duel(tk)
        print(json.dumps(res, indent=2, ensure_ascii=False))
