"""Keyless-runnable tests for server/sectors.py — no API key, no network."""
import pytest

from server import sectors
from server.sectors import (
    SectorsError,
    SectorsNotConfigured,
    bare_ticker,
)


@pytest.fixture(autouse=True)
def _keyless_isolated_cache(tmp_path, monkeypatch):
    """Pin _get() to a tmp SQLite DB with an empty key.

    Warm prod cache rows return without a key by design (hit saves a
    credit), which would mask the loud-failure assertions below. A key
    inherited from the shell would do the same — force both away.
    """
    import server.sectors as _S
    from server.config import get_settings
    from server.storage import SectorsCache

    monkeypatch.setenv("SECTORS_API_KEY", "")
    get_settings.cache_clear()
    iso = SectorsCache(db_path=str(tmp_path / "iso.db"))
    monkeypatch.setattr(_S, "_cache", iso, raising=False)
    yield
    iso.close()
    get_settings.cache_clear()


def test_bare_ticker():
    assert bare_ticker("bbca.jk") == "BBCA"
    assert bare_ticker(" MTEL ") == "MTEL"
    assert bare_ticker("ADRO") == "ADRO"


def test_no_key_raises_loud():
    # Every helper must fail LOUD without key — never silent fallback.
    for fn, args in [
        (sectors.daily, ("BBCA", "2026-01-01", "2026-01-02")),
        (sectors.quarterly, ("BBCA",)),
        (sectors.news, ("BBCA",)),
        (sectors.filings, ("BBCA",)),
        (sectors.corporate_actions, ("BBCA",)),
        (sectors.company_report, ("BBCA", "dividend")),
        (sectors.universe_close, ("2026-09-01",)),
        (sectors.foreign_flow, ("BBCA", "2026-01-01", "2026-01-02")),
        (sectors.peers, ("BBCA",)),
        (sectors.future, ("BBCA",)),
        (sectors.valuation_section, ("BBCA",)),
        (sectors.ownership, ("BBCA",)),
        (sectors.management, ("BBCA",)),
        (sectors.broker_top, ("BBCA", "2026-01-01", "2026-01-02")),
        (sectors.suspensions, ("BBCA",)),
        (sectors.subsectors, ()),
        (sectors.mining_companies, ("BBCA",)),
        (sectors.subsector_report, ("banks", "valuation,growth")),
        (sectors.listing_performance, ("CDIA",)),
        (sectors.screener, ("market_cap > 1000000000000",)),
        (sectors.index_daily, ("JKSE", "2026-01-01", "2026-01-02")),
        (sectors.idx_market_cap, ("2026-01-01", "2026-01-02")),
        (sectors.mining_company_financials, ("adaro",)),
        (sectors.segments, ("BBCA",)),
        (sectors.shareholders_composition, ("BBCA",)),
        (sectors.quarterly_dates, ("BBCA",)),
    ]:
        try:
            fn(*args)
        except SectorsNotConfigured:
            continue
        raise AssertionError(f"{fn.__name__} did not raise without key")


def test_error_shape():
    e = SectorsError(401, "unauthorized-key-here")
    assert e.status == 401
    assert "401" in str(e)
