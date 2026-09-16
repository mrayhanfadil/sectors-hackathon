# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
"""Sectors-only ratchet for ADK agent instructions (13 Sep 2026).

No agent prompt may PERMIT an external source - every instruction that
names a data origin must route it through Sectors (fetch-* tools,
Sectors-backed web_search, or peer outputs). Mentions of outside outlets
are allowed only as prohibitions (Critic REJECT examples, no-browse rules).

Run: .venv/bin/python -m pytest agents/adk/tests/test_instructions_sectors_only.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agents.adk.agents import instructions as ins  # noqa: E402

# Every live agent instruction (social retired 14 Sep 2026 - kept as a retired
# marker in instructions.py so old refs fail loudly; sub-agent orphans excluded).
LIVE = {
    "collector": ins.collector_instruction,
    "news_harvester": ins.news_harvester_instruction,
    "modeler": ins.modeler_instruction,
    "analyst": ins.analyst_instruction,
    "industry": ins.industry_instruction,
    "risk": ins.risk_instruction,
    "kpi": ins.kpi_instruction,
    "writer": ins.writer_instruction,
    "visualizer": ins.visualizer_instruction,
    "sotp": ins.sotp_instruction,
    "adversarial": ins.adversarial_instruction,
    "critic": ins.critic_instruction,
}

# Phrasings that PERMIT external sourcing (each was a real find, 13 Sep 2026).
BANNED_PERMISSIONS = [
    "Cite sources per exhibit (Bloomberg",  # analyst: external cite list
    "(Brent/IEA/coal)",  # industry: external commodity sites
    "requires IDX fact sheet/KSEI",  # FLOAT/MSCI: external browsing
]


def test_no_instruction_permits_external_source():
    """No live prompt may contain a permission to use outside data."""
    bad = []
    for name, text in LIVE.items():
        for pat in BANNED_PERMISSIONS:
            if pat in text:
                bad.append(f"{name}: {pat!r}")
    assert not bad, "external-source permissions in prompts:\n" + "\n".join(bad)


def test_tools_field_mentions_are_sectors_scoped():
    """Wherever a prompt names tools/feeds, Sectors must be in the same breath."""
    weak = []
    for name, text in LIVE.items():
        low = text.lower()
        if ("fetch-" in low or "web_search" in low) and "sectors" not in low:
            weak.append(name)
    # modeler/calc-only agents name no feeds at all - they are fine either way;
    # this only fires when a prompt names tools without Sectors scope.
    assert not weak, f"tool mentions without Sectors scope: {weak}"


if __name__ == "__main__":
    failed = 0
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
