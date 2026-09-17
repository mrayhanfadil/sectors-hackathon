"""Tests for post-audit writer sanitization (Issue 9).

Verifies that internal backend leaks and raw dict keys / paths are stripped from
all copy that reaches the reader.
"""
from __future__ import annotations

import pytest

from agents.adk.post_audit_inject import sanitize_copy, sanitize_writer_output
from server.report.text_sanitize import clean_text


@pytest.mark.parametrize(
    "raw,expected_fragment,forbidden_pattern",
    [
        (
            "Target price: null (GAP G5) - hanya direksional (29 beli/1 tahan).",
            "hanya direksional (29 beli/1 tahan)",
            r"null\s*\(GAP\s*G5\)",
        ),
        (
            "Data forward (GAP G10) - yang tersedia hanya sensitivitas EBITDA.",
            "yang tersedia hanya sensitivitas EBITDA",
            r"GAP\s*G10",
        ),
        (
            "BVPS per tahun dari drivers.bvps_path: Rp 1.169, Rp 1.253.",
            "BVPS per tahun dari drivers: Rp 1.169, Rp 1.253",
            r"\.bvps_path",
        ),
        (
            "Sesuai asumsi data/drivers/AMMN.json fcf_basis untuk capex.",
            "basis asumsi tim",
            r"\.fcf_basis|fcf_basis",
        ),
        (
            "Jalur ev_ebitda_path menghasilkan fair value Rp 5.667.",
            "menghasilkan fair value Rp 5.667",
            r"ev_ebitda_path",
        ),
        (
            "tidak ada angka forward terverifikasi untuk emiten ini (LOUD policy, tanpa estimasi manajemen).",
            "tidak ada angka forward terverifikasi untuk emiten ini",
            r"LOUD policy",
        ),
        (
            "Perbandingan biaya vs peers: payload tidak membawa metrik operasional tersebut, jadi perbandingan biaya vs peers ditiadakan.",
            "Perbandingan biaya vs peers:",
            r"payload tidak",
        ),
        (
            "Suspensi IDX: nihil (Sectors /suspensions total_count 0) - dinyatakan eksplisit.",
            "Suspensi IDX: nihil - dinyatakan eksplisit",
            r"Sectors\s+/suspensions\s+total_count\s+0",
        ),
        (
            "Proyeksi opex: operating_expense yang dilaporkan Sectors (2025A +249 bn).",
            "Proyeksi opex: yang dilaporkan Sectors (2025A +249 bn)",
            r"operating_expense",
        ),
        (
            "Beban pendanaan: interest_expense dari jalur proyeksi.",
            "Beban pendanaan: dari jalur proyeksi",
            r"interest_expense",
        ),
        (
            "Kinerja kuartalan (Q1-2025 ramp-up smelter) (Q1-2025 ramp-up smelter) mencatat perbaikan.",
            "Kinerja kuartalan (Q1-2025 ramp-up smelter) mencatat perbaikan",
            r"\(Q1-2025[^\)]*\)\s*\(Q1-2025[^\)]*\)",
        ),
    ],
)
def test_sanitize_copy_removes_backend_leaks(raw: str, expected_fragment: str, forbidden_pattern: str):
    import re

    cleaned_post = sanitize_copy(raw)
    assert not re.search(forbidden_pattern, cleaned_post, re.I), f"Pattern {forbidden_pattern} survived sanitize_copy: {cleaned_post}"

    cleaned_server = clean_text(raw)
    assert not re.search(forbidden_pattern, cleaned_server, re.I), f"Pattern {forbidden_pattern} survived clean_text: {cleaned_server}"


def test_sanitize_writer_output_dict():
    wo = {
        "title": "AMMN report",
        "cover_paragraphs": [
            "Proyeksi (LOUD policy, no fallback).",
            "Rekap: null (GAP G1) - selesai.",
        ],
        "nested": {
            "note": "Via drivers.bvps_path and Sectors /filings total_count 12.",
        },
    }
    cleaned = sanitize_writer_output(wo)
    assert "LOUD policy" not in cleaned["cover_paragraphs"][0]
    assert "GAP G1" not in cleaned["cover_paragraphs"][1]
    assert "bvps_path" not in cleaned["nested"]["note"]
    assert "total_count" not in cleaned["nested"]["note"]
