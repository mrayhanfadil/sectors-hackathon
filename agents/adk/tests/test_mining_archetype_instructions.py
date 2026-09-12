# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Guard tests for mining-archetype instruction compliance (AMMN-tested, ticker-agnostic).

Proves the four mining deltas exist in instructions.py and that the ADDED
blocks carry no ticker literals (AMMN / Batu Hijau / Elang) — Option3:
instructions carry `{ticker}` patterns, AMMN only proves them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

INSTR_PATH = Path(__file__).resolve().parent.parent / "agents" / "instructions.py"

FORBIDDEN_LITERALS = ("AMMN", "Batu Hijau", "BatuHijau", "Elang", "BATU HIJAU")


def _src() -> str:
    return INSTR_PATH.read_text(encoding="utf-8")


def _block(src: str, marker: str, window: int = 1200) -> str:
    idx = src.find(marker)
    assert idx != -1, f"marker missing: {marker}"
    return src[max(0, idx - 200) : idx + window]


def test_modeler_finite_reserve_discipline():
    blk = _block(_src(), "FINITE-RESERVE DISCIPLINE")
    for kw in ("Gordon", "reserve life", "RNAV", "MID-CYCLE", "mine-development"):
        assert kw in blk, f"modeler finite-reserve block missing: {kw}"


def test_kpi_cu_au_slots():
    blk = _block(_src(), "Cu-eq production")
    for kw in ("C1", "AISC", "realized", "grade", "reserve life", "{ticker}"):
        assert kw in blk, f"kpi cu-au block missing: {kw}"


def test_visualizer_ex7_sector_switch():
    blk = _block(_src(), "Exhibit-7 SECTOR SWITCH")
    for kw in ("mining", "production volume", "cash-cost", "NIM", "lifting cost", "{ticker}"):
        assert kw in blk, f"visualizer ex7 switch block missing: {kw}"


def test_industry_mining_catalysts():
    blk = _block(_src(), "Mining/copper-gold")
    for kw in ("ESDM", "DMO", "royalty", "smelter", "timeline"):
        assert kw in blk, f"industry mining block missing: {kw}"


def test_mining_deltas_ticker_agnostic():
    src = _src()
    for marker in (
        "FINITE-RESERVE DISCIPLINE",
        "Cu-eq production",
        "Exhibit-7 SECTOR SWITCH",
        "Mining/copper-gold",
    ):
        blk = _block(src, marker)
        for lit in FORBIDDEN_LITERALS:
            assert lit not in blk, f"ticker literal {lit!r} leaked into block {marker!r}"
