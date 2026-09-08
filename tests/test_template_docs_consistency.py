"""H3 — template-mirror + docs consistency pins (E-batch cross-check).

Read-first findings (2026-09-08, commit bae3620):
- Mirror server/report/typst -> templates/typst/archetypes holds ONLY for
  report_single (modulo the two #import lines rewritten to ../common/).
  sotp/infra/strategy DIVERGE: templates copies carry baked Peer Median /
  Rata-rata / Median rows the server copies lack.
- De-baked markers live in server copies: report_single peer dashes +
  "Sectors (pending)"; infra fully data-driven peers; sotp ilustratif notes.
- Docs E-batch claims hold for code: no `jci_target` block in endpoints.py
  (outlook raises 503), no OutlookResponse in server/models.py.

Pure file-content assertions — no renderer, no fixtures, no network.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"
ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
ENDPOINTS = REPO_ROOT / "server" / "routers" / "endpoints.py"
MODELS = REPO_ROOT / "server" / "models.py"
DOCS_SWAP = REPO_ROOT / "docs" / "sectors-swap.md"


def _read(p: Path) -> str:
    assert p.exists(), f"missing file under test: {p}"
    return p.read_text(encoding="utf-8")


# ---------- 1. report_single mirror (the one mirror that holds) ----------

def test_report_single_mirrors_server_modulo_imports():
    server = _read(SERVER_TYPST / "report_single.typ")
    mirror = _read(ARCHETYPES / "report_single.typ")
    normalized = server.replace(
        '#import "theme.typ": *', '#import "../common/theme.typ": *'
    ).replace(
        '#import "cover.typ": *', '#import "../common/cover.typ": *'
    )
    assert normalized == mirror, (
        "report_single mirror drifted beyond the two ../common/ import rewrites"
    )


# ---------- 2. de-baked markers: report_single peers ----------

def test_report_single_peer_rows_debaked_to_dashes():
    for name in ("report_single.typ",):
        for base in (SERVER_TYPST, ARCHETYPES):
            src = _read(base / name)
            assert '((m.ticker, "-", "-", "-", "-", "-", "-"),)' in src, (
                f"{base.name}/{name}: dash-default peer row missing"
            )
            assert "Sectors (pending)" in src, (
                f"{base.name}/{name}: 'Sectors (pending)' source marker missing"
            )
    server = _read(SERVER_TYPST / "report_single.typ")
    # Old baked RATU/MEDC peer cells (E-batch bae3620 removed these exact rows;
    # note: bare multiples like 42,7x also occur in ratio-table defaults, so
    # pin the peer-block-unique market-cap cells instead).
    for baked in ("Rp 16,8 T", "Rp 34,2 T", "Rata-rata Peers", "Median Peers"):
        assert baked not in server, (
            f"server report_single.typ still serves baked peer row marker: {baked}"
        )


# ---------- 3. de-baked markers: server sotp pillar tables ----------

def test_server_sotp_pillars_carry_static_demo_note():
    src = _read(SERVER_TYPST / "report_sotp.typ")
    note = "Komparabel ilustratif CDIA, statis Sep 2026"
    assert src.count(note) >= 4, (
        f"server sotp pillar tables must each carry the static-demo note (>=4), "
        f"found {src.count(note)}"
    )
    for baked in ("Peer Median", "Rata-rata Peers", "Median Peers"):
        assert baked not in src, (
            f"server report_sotp.typ serves baked aggregate row: {baked}"
        )


# ---------- 4. de-baked markers: server infra peers fully data-driven ----------

def test_server_infra_peers_data_driven_no_baked_defaults():
    src = _read(SERVER_TYPST / "report_infra.typ")
    assert "data.peers.tables.at(0)" in src, (
        "server infra peer section must read straight from data.peers (no default)"
    )
    assert "Sectors pending" in src, "server infra Sectors-pending caption missing"
    for baked in ("Peer Median", "Rata-rata Peers", "Median Peers", "22,2x"):
        assert baked not in src, (
            f"server report_infra.typ serves baked peer marker: {baked}"
        )


# ---------- 5. server strategy Top Picks: rationale-only, no multiples ----------

def test_server_strategy_top_picks_rationale_only():
    src = _read(SERVER_TYPST / "report_strategy.typ")
    assert '("Ticker", "Cap", "Rationale")' in src, (
        "server strategy Exhibit 6 must stay Ticker/Cap/Rationale (no multiples)"
    )
    for baked in ("Peer Median", "Rata-rata Peers", "Median Peers"):
        assert baked not in src, (
            f"server report_strategy.typ serves baked aggregate row: {baked}"
        )


# ---------- 6. sotp/infra/strategy templates copies are NOT mirrors ----------

def test_templates_sotp_infra_strategy_diverged_from_server():
    # Drift detector: "Mirrored to templates/" (docs E-batch) covers
    # report_single only. If a lane re-mirrors these three, update this pin.
    diverged = {
        "report_sotp.typ": "Peer Median",
        "report_infra.typ": "Rata-rata Peers",
        "report_strategy.typ": "Rata-rata Peers",
    }
    for name, baked_marker in diverged.items():
        server = _read(SERVER_TYPST / name)
        mirror = _read(ARCHETYPES / name)
        assert baked_marker in mirror, (
            f"templates {name} lost its baked marker {baked_marker!r} — "
            f"mirror state changed, update this pin"
        )
        assert baked_marker not in server, (
            f"server {name} gained baked marker {baked_marker!r} — "
            f"de-baked state regressed"
        )
        assert server != mirror, f"{name}: unexpectedly identical, update this pin"


# ---------- 7. docs E-batch claim: outlook 503, no jci_target block ----------

def test_endpoints_no_jci_target_fixture_block():
    src = _read(ENDPOINTS)
    assert "jci_target" not in src, "endpoints.py still defines a jci_target block"
    m = re.search(
        r"async def outlook\(\):(.*?)(?=\n# ----------|\ndef |\n@router|\Z)",
        src,
        re.DOTALL,
    )
    assert m, "outlook handler missing in endpoints.py"
    body = m.group(1)
    assert "status_code=503" in body and "raise HTTPException" in body, (
        "outlook must raise 503 (Sectors-native pending), never serve JPM-9100"
    )


# ---------- 8. docs E-batch claim: OutlookResponse model deleted ----------

def test_models_no_outlook_response():
    src = _read(MODELS)
    assert "OutlookResponse" not in src, (
        "server/models.py still defines OutlookResponse"
    )


# ---------- 9. docs side of the consistency pair ----------

def test_docs_ebatch_claims_present():
    docs = _read(DOCS_SWAP)
    assert "OutlookResponse" in docs, (
        "docs E-batch section must record the OutlookResponse deletion claim"
    )
    assert "9100" in docs, "docs E-batch section must record the JPM-9100 claim"
