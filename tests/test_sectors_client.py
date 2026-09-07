"""Keyless-runnable tests for server/sectors.py — no API key, no network."""
from server import sectors
from server.sectors import (
    SectorsError,
    SectorsNotConfigured,
    bare_ticker,
)


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
