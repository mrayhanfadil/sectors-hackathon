"""Lane C live-probe — single cheap Sectors call (opt-in live billing).

Probe: company_report("BBCA", "dividend") — one section = ~1 credit.
Gated on SECTORS_LIVE=1 (explicit opt-in, mirrors OPENCODE_GO_LIVE=1):
absent → module skips, zero network, zero credits. Bare SECTORS_API_KEY
presence must NOT gate it — server/main.py force-loads the BE env file at
import, which would billing-fire the suite as a side effect.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SECTORS_LIVE") != "1",
    reason="live probe gated (SECTORS_LIVE=1)",
)

# Ensure repo root on path so 'server.sectors' resolves
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _probe_dividend() -> dict:
    """One cheap live call; honest source field, no silent fallback."""
    from server import sectors as S

    try:
        data = S.company_report("BBCA", "dividend")
    except S.SectorsNotConfigured:
        return {"source": "sectors_missing_key", "data": None}
    except S.SectorsError as e:
        return {"source": "sectors_error", "data": None, "error": str(e)[:300]}
    return {"source": "sectors", "data": data}


def test_live_company_report_bbca_dividend():
    if os.getenv("SECTORS_LIVE") != "1":
        pytest.skip("gated (SECTORS_LIVE=1)")
    if not os.getenv("SECTORS_API_KEY"):
        pytest.skip("SECTORS_API_KEY absent — nothing to probe")
    out = _probe_dividend()
    assert out["source"] == "sectors", f"expected live sectors source, got {out['source']}"
    data = out["data"]
    assert isinstance(data, (dict, list)), f"unexpected shape: {type(data).__name__}"
    assert data, "empty live response (billed anyway — check sections=)"
    if isinstance(data, dict):
        assert len(data) >= 1
