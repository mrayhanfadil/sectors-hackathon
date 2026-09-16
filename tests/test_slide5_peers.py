"""Slide 5 - peer valuation + own-history bands: the rules, the arithmetic, and the cache contract."""
from __future__ import annotations

import json
import os
import pathlib
import statistics as st

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "output" / "cache" / "sectors" / "AMMN"
SPEC = ROOT / "docs" / "ammn-slides" / "slide5-peer-spec.md"
TEMPLATE = ROOT / "templates" / "report_single.html"
PARTIAL = ROOT / "templates" / "_slide5_peers.html"
INSTRUCTIONS = ROOT / "agents" / "adk" / "agents" / "instructions.py"

cached = pytest.mark.skipif(not (CACHE / "peer_table.json").exists(),
                            reason="no cached Sectors artifacts for slide 5")


def _load(name: str) -> dict:
    return json.loads((CACHE / name).read_text())


# --------------------------------------------------------------------------- data layer
@cached
def test_rebuild_from_cache_spends_no_credits():
    """The whole point of the data layer: a cached rebuild is free."""
    from server.report.peers_data import build_peer_table, build_bands

    table = build_peer_table("AMMN")
    bands = build_bands("AMMN")
    assert table["credit_log"] == "billed calls: 0 | cache hits: 11"
    assert bands["credit_log"].startswith("billed calls: 0")
    assert table["rows"] and bands["sessions"]


@cached
def test_peer_table_basis_is_single_and_rows_are_complete():
    rows = _load("peer_table.json")["rows"]
    assert len(rows) == 10
    assert sum(1 for r in rows if r["is_covered"]) == 1
    for r in rows:
        assert r["period_end"], f"{r['symbol']} has no quarter end date"
        assert r["quarters_used"] >= 4, f"{r['symbol']} has fewer than four quarters"
        # every row is built from the same fields, so a missing one is a data gap, not a silent zero
        assert r["equity"] is not None and r["net_debt"] is not None


@cached
def test_ev_ebitda_uses_market_cap_plus_net_debt_over_ttm_ebitda():
    rows = {r["symbol"]: r for r in _load("peer_table.json")["rows"]}
    for sym, r in rows.items():
        if r["ev_ebitda_ttm"] is None:
            continue
        assert r["ev"] == pytest.approx(r["market_cap"] + r["net_debt"])
        assert r["ev_ebitda_ttm"] == pytest.approx(r["ev"] / r["ebitda_ttm"], rel=1e-6), sym
        # the recovered market cap must stay on the published ratio basis
        assert r["market_cap"] == pytest.approx(r["pb_mrq"] * r["equity"], rel=1e-9)


@cached
def test_median_and_average_exclude_non_meaningful_pe():
    table = _load("peer_table.json")
    rows = [r for r in table["rows"] if not r["is_covered"]]
    pe = sorted(r["pe_ttm"] for r in rows if r["pe_meaningful"])
    assert table["stats"]["pe_ttm"]["n"] == len(pe)
    assert table["stats"]["pe_ttm"]["median"] == pytest.approx(st.median(pe))
    assert table["stats"]["pe_ttm"]["average"] == pytest.approx(st.mean(pe))
    for sym in table["pe_excluded"]:
        row = next(r for r in rows if r["symbol"] == sym)
        assert not row["pe_meaningful"]
        assert row["pe_ttm"] <= 0 or row["pe_ttm"] > 200


@cached
def test_bands_current_is_last_observation_and_percentile_is_recomputed():
    bands = _load("bands_1y.json")
    assert bands["window"]["sessions"] == len(bands["sessions"])
    for key, s in bands["summary"].items():
        vals = [x[key] for x in bands["sessions"] if x[key] is not None]
        assert s["n"] == len(vals), key
        assert s["current"] == pytest.approx(vals[-1])
        assert 0 <= s["percentile"] <= 100
        pct = 100.0 * sum(1 for v in vals if v <= s["current"]) / len(vals)
        assert s["percentile"] == pytest.approx(pct, abs=1e-6)


@cached
def test_implied_price_math_holds_the_driver_flat():
    bands = _load("bands_1y.json")
    sessions = bands["sessions"]
    shares = bands["market_cap"] / bands["last_close"]
    drv = bands["driver"]
    for key, ps in (("pe", drv["earnings_ttm"] / shares),
                    ("pbv", drv["equity"] / shares),
                    ("ev_ebitda", drv["ebitda_ttm"] / shares),
                    ("ev_sales", drv["revenue_ttm"] / shares)):
        imp = bands["implied_price"][key]
        s = bands["summary"][key]
        if key in ("pe", "pbv"):
            assert imp["to_mean"] == pytest.approx(s["mean"] * ps, rel=1e-9)
            assert imp["to_median"] == pytest.approx(s["median"] * ps, rel=1e-9)
        else:
            # regression: net debt is subtracted PER SHARE, not as a total
            nd_ps = drv["net_debt"] / shares
            assert imp["to_mean"] == pytest.approx(s["mean"] * ps - nd_ps, rel=1e-9)
            assert imp["to_median"] == pytest.approx(s["median"] * ps - nd_ps, rel=1e-9)
            assert imp["to_mean"] > 0, "an EV-multiple implied price must not come out negative"


@cached
def test_frozen_driver_sessions_are_counted_not_hidden():
    bands = _load("bands_1y.json")
    frozen = [s for s in bands["sessions"] if s["driver_as_of"] != bands["driver"]["as_of"]]
    assert bands["driver_frozen_sessions"] == len(frozen)
    assert bands["driver"]["as_of"] == bands["driver"]["as_of"][:10]


# --------------------------------------------------------------------------- page + gate
@cached
def test_page_payload_splits_the_two_methodologies():
    from server.report.peers_page import build_peers_page

    page = build_peers_page("AMMN")
    assert page["available"]
    a, b = page["part_a"], page["part_b"]
    assert a["exhibit"] == 11 and b["exhibits"] == [12, 13]
    assert [blk["key"] for blk in b["bands"]][:2] == ["pe", "pbv"]
    assert {r["key"] for r in b["implied"]} >= {"pe", "pbv"}
    assert "bukan Target Price" in b["disclaimer"]
    from server.report.peers_page import render_band_svg
    svg = str(render_band_svg(b["bands"][0]))
    assert svg.lstrip().startswith("<svg"), "the band chart must be raw svg, not escaped markup"
    assert any("n.m." in s for s in a["narrative"])


@cached
def test_gate_passes_on_the_real_page_and_bites_on_every_rule():
    import copy

    from server.report.house_rules import audit_peer_page
    from server.report.peers_page import build_peers_page

    page = build_peers_page("AMMN")
    assert audit_peer_page(page) == []

    mutations = {
        "no median row": lambda d: d["part_a"].pop("median"),
        "no average row": lambda d: d["part_a"].pop("average"),
        "missing p/bv column": lambda d: d["part_a"].__setitem__("columns", ["Ticker", "P/E (x)"]),
        "tampered median": lambda d: d["part_a"]["median"].__setitem__("pe", 99.9),
        "no as-of date": lambda d: d["part_a"].__setitem__("as_of", ""),
        "covered row unflagged": lambda d: [r.__setitem__("is_covered", False) for r in d["part_a"]["rows"]],
        "p/e band removed": lambda d: d["part_b"].__setitem__(
            "bands", [b for b in d["part_b"]["bands"] if b["key"] != "pe"]),
        "median implied missing": lambda d: d["part_b"]["implied"][0].__setitem__("to_median", None),
        "disclaimer stripped": lambda d: d["part_b"].__setitem__("disclaimer", "see slide 4"),
        "per-chart narrative merged": lambda d: [b.pop("narrative") for b in d["part_b"]["bands"]],
        "percentile removed": lambda d: [
            b.__setitem__("narrative", b["narrative"].replace("persentil", "")) for b in d["part_b"]["bands"]],
        "cache-only contract missing": lambda d: d["part_a"].__setitem__("sources", []),
    }
    for label, mutate in mutations.items():
        d = copy.deepcopy(page)
        mutate(d)
        violations = audit_peer_page(d)
        assert violations, f"the gate failed to catch: {label}"


def test_unavailable_page_is_a_violation_not_a_silent_drop():
    from server.report.house_rules import audit_peer_page

    # the builder ran and produced nothing -> loud; the deck never had the page -> not applicable
    assert audit_peer_page({"available": False, "reason": "no cache"})
    assert audit_peer_page(None) == []


# --------------------------------------------------------------------------- wiring guards
def test_spec_carries_the_binding_rule_text():
    text = SPEC.read_text()
    for marker in ("## 0. Binding rule text (owner, 12 Sep 2026)", "Bagian Atas (~50%)",
                   "Bagian Bawah (~50%)", "Exhibit 12. P/E Historical Band", "Implied Price Judgement",
                   "## 7. Decision log", "cache-first", "zero billed calls"):
        assert marker in text, f"slide-5 spec lost: {marker}"


def test_prompt_rule_and_data_technique_reach_the_agents():
    from agents.adk.agents import instructions as I

    rule = I.SLIDE5_RULE
    for marker in ("SLIDE 5 - PEER VALUATION", "DATA TECHNIQUE", "peers_data.py", "quarterly(symbol)",
                   "90 days", "n.m.", "net debt PER SHARE", "Median and Average", "RANGE"):
        assert marker in rule, f"the slide-5 rule lost: {marker}"
    # it reaches the prompts that build pages, and stays out of the ones that only gather data
    for name in ("industry_instruction", "writer_instruction", "critic_instruction"):
        assert "SLIDE 5 - PEER VALUATION" in getattr(I, name), f"{name} lost the slide-5 rule"
    for name in ("news_harvester_instruction",):
        assert "SLIDE 5 - PEER VALUATION" not in getattr(I, name), f"{name} should not carry page rules"


def test_template_renders_slide_5_and_drops_the_old_peer_table():
    single = TEMPLATE.read_text()
    partial = PARTIAL.read_text()
    assert '_slide5_peers.html' in single
    assert "Peer Comparison -" not in single, "the superseded peer table is still in the deck"
    # two consecutive pages: 5A cross-sectional (section 6), 5B time-series (section 7)
    assert partial.count('<div class="page">') == 2, "slide 5A and 5B must be separate pages"
    assert '{{ m.section("Peer Valuation - Cross-Sectional", ns) }}' in partial
    assert '{{ m.section("Valuasi Relatif Historis - Own History", ns) }}' in partial
    # the owner removed the scaffolding banner (13 Sep 2026): the requires-text says the two
    # methodologies must be separated by a divider OR a section header, and the 5B section header is it.
    assert "metodologi time-series, berbeda filosofi" not in partial, \
        "the sidebar-style method banner must not come back"
    assert 'm.section("Valuasi Relatif Historis - Own History", ns)' in partial, "5B still needs its own section header as the separation"
    for marker in ("MEDIAN", "AVERAGE", "Implied Price Judgement", "peer-self", "band_svg",
                   "keduanya tidak saling mengonfirmasi"):
        assert marker in partial, f"slide-5 partial lost: {marker}"


def test_pdf_router_builds_the_page_from_cache_not_the_network():
    src = (ROOT / "server" / "routers" / "pdf.py").read_text()
    assert 'payload["peers_page"] = build_peers_page(t)' in src
    assert 'env.globals["band_svg"]' in src
    builder = (ROOT / "server" / "report" / "peers_page.py").read_text()
    for banned in ("requests", "httpx", "urlopen", "sectors."):
        assert banned not in builder, f"the page builder must not touch the network ({banned})"
