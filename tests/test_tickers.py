"""GET /api/tickers - universe comes from the Sectors screener post-key.

IDX Postgres killed Sep 2026 (external source): this endpoint is honest 503
until SECTORS_API_KEY lands and companies/?where=&order_by= is wired.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.main import app  # noqa: E402

client = TestClient(app)


def test_tickers_503_until_sectors_key():
    r = client.get("/api/tickers")
    assert r.status_code == 503, f"Expected 503, got {r.status_code}: {r.text}"
    assert "SECTORS_API_KEY" in r.text
