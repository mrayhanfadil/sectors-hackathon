"""Opsi C - the RNAV branch of deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md).

For a property / plantation / resources issuer whose value sits in identifiable assets. Unlike the DCF
and DDM branches there is no engine repo behind this one (the owner supplied engines for DCF, DDM and
relative peers only), so the arithmetic is the open RNAV identity and every input must carry its own
source: NAV per asset (a per-project DCF or an independent appraisal), the issuer's ownership share,
cash, debt, corporate overhead and the discount to RNAV the analyst applies.

The branch refuses loudly when the payload carries no asset-level data rather than inventing NAVs: the
Sectors API has no reserve tonnage, no per-asset production and no NAV per asset field.
"""

from __future__ import annotations
from server.report import numfmt as _nf

PERIOD_UNIT_LABELS = {
    "ton": "cadangan (ton)", "tonne": "cadangan (ton)", "oz": "cadangan (oz)",
    "boe": "cadangan (boe)", "ha": "landbank (ha)", "sqm": "luas (m2)",
    "unit": "kapasitas (unit)", "mw": "kapasitas (MW)", "tpa": "kapasitas (tpa)",
}


def build_rnav_page(payload: dict, assumptions: dict, helpers: dict) -> dict:
    _num = helpers["num"]
    assum = assumptions or {}
    asset_input = assum.get("assets") or payload.get("assets") or []
    discount = assum.get("rnav_discount")
    shares_bn = (assum.get("shares_out") or 0) / 1e9
    price = assum.get("last_price")
    total_debt_bn = (assum.get("total_debt") or 0) / 1e9
    cash_bn = (assum.get("cash") or 0) / 1e9
    overhead_bn = _num(assum.get("corporate_overhead_pv_bn")) or 0.0

    reasons: list[str] = []
    if not asset_input:
        reasons.append(
            "tidak ada data aset (nama aset, ukuran, NAV per aset, % kepemilikan) di payload maupun "
            "assumptions - Sectors tidak menyediakan cadangan/NAV per aset"
        )
    if discount is None:
        reasons.append("discount to RNAV belum ditetapkan analis (assumptions.rnav_discount)")
    if not shares_bn:
        reasons.append("jumlah saham beredar tidak tersedia")
    external = [
        str(a.get("name") or "?")
        for a in asset_input
        if "sectors" not in str(a.get("nav_source") or a.get("source") or "").lower()
    ]
    if external and not reasons:
        reasons.append(
            "aturan proyek: hanya data Sectors yang boleh dipakai. NAV aset berikut bersumber dari luar "
            "Sectors sehingga halaman ini menolak menampilkannya: " + ", ".join(external[:5])
        )
    if reasons:
        return {
            "available": False,
            "method": "rnav",
            "title": "Valuasi Intrinsik - RNAV",
            "missing": reasons,
            "subtitle": "Opsi C dipilih tetapi data aset belum ada; halaman sengaja tidak diisi NAV karangan.",
            "sources": ["Sectors API", f"data/assumptions/{payload.get('ticker', '?')}.json"],
        }

    assets = []
    for raw in asset_input:
        nav = _num(raw.get("nav_bn"))
        own = _num(raw.get("ownership_pct"))
        own = (own / 100) if own and own > 1 else own
        size = _num(raw.get("size"))
        assets.append({
            "name": str(raw.get("name") or "aset tanpa nama"),
            "size": size,
            "size_unit": str(raw.get("size_unit") or ""),
            "nav": nav,
            "ownership": own,
            "nav_attributable": (nav * own) if (nav is not None and own is not None) else None,
            "nav_source": str(raw.get("nav_source") or raw.get("source") or "sumber tidak dicantumkan"),
            "nav_source_is_sectors": "sectors" in str(raw.get("nav_source") or raw.get("source") or "").lower(),
            "discount_rate": _num(raw.get("discount_rate")),
        })

    sum_nav = sum(a["nav_attributable"] or 0.0 for a in assets)
    total_rnav = sum_nav + cash_bn - total_debt_bn - overhead_bn
    rnav_per_share = total_rnav / shares_bn
    target_price = rnav_per_share * (1 - discount) if discount is not None else None

    # Exhibit 10: the discount the analyst applies against the RNAV per share, plus the discount rate
    # axis when the assets carry their own rates (a project-level sensitivity, not a WACC sweep).
    discount_axis = [max(min(discount + i * 0.05, 0.9), 0.0) for i in range(-2, 3)]
    rates = [a["discount_rate"] for a in assets if a["discount_rate"] is not None]
    if rates:
        base_rate = sum(rates) / len(rates)
        rate_axis = [base_rate + i * 0.01 for i in range(-2, 3)]
    else:
        base_rate = None
        rate_axis = [5.0, 7.5, 10.0, 12.5, 15.0]
    grid: list[list] = []
    for rate in rate_axis:
        row = []
        for disc in discount_axis:
            if base_rate is not None and rate != 0:
                # a higher asset discount rate lowers the per-asset NAV before the RNAV discount applies
                scaled = total_rnav * (base_rate / rate)
            else:
                scaled = total_rnav * (1 - (rate - rate_axis[2]) / 100.0) if base_rate is None else total_rnav
            row.append(max(scaled / shares_bn * (1 - disc), 0.0))
        grid.append(row)

    page = {
        "available": True,
        "method": "rnav",
        "title": "Valuasi Intrinsik - RNAV",
        "subtitle": (
            "Opsi C (RNAV) aktif: nilai berdiri di aset yang teridentifikasi (NAV per aset x porsi "
            "kepemilikan), lalu bridge ke ekuitas dan satu discount to RNAV sebagai judgment call analis."
        ),
        "periods": [a["name"] for a in assets],
        "assets": assets,
        "blocks": {"build_up": {}},
        "bridge": {
            "sum_nav": sum_nav, "cash": cash_bn, "total_debt": total_debt_bn, "overhead": overhead_bn,
            "total_rnav": total_rnav, "rnav_per_share": rnav_per_share, "discount": discount,
            "target_price": target_price, "net_debt": total_debt_bn - cash_bn,
            "fv_gordon": target_price, "fv_exit": rnav_per_share,
            "tv_share": None, "tv_gordon_df": None, "pv_tv_gordon": None, "pv_explicit": None,
            "tv_gordon": total_rnav, "tv_exit": None, "pv_tv_exit": None,
            "ev_gordon": total_rnav, "ev_exit": rnav_per_share,
            "equity_gordon": total_rnav, "equity_exit": rnav_per_share,
            "implied_exit_multiple": None,
        },
        "alternatives": {},
        "wacc_rows": _rnav_parameter_rows(assum, total_debt_bn, cash_bn, overhead_bn),
        "sensitivity": {
            "fair_value": grid, "rows_axis": rate_axis, "cols_axis": discount_axis,
            "base": (2, 2), "base_fv": target_price,
            "swing": {"min": min(min(r) for r in grid), "max": max(max(r) for r in grid)},
            "wacc_axis": rate_axis, "g_axis": discount_axis,
        },
        "assumptions_view": {"wacc": None, "g": None, "shares_bn": shares_bn, "rf": assum.get("rf"),
                             "beta": assum.get("beta"), "erp": assum.get("erp")},
        "legs": {"dcf": ((payload.get("valuation") or {}).get("legs") or {}).get("dcf"),
                 "ev_ebitda": ((payload.get("valuation") or {}).get("legs") or {}).get("ev_ebitda")},
        "drivers": {"price": price, "discount": discount, "multiple": None,
                    "revenue_basis": "NAV per aset dari asumsi analis (DCF per proyek atau appraisal pihak ketiga)",
                    "rnav_per_share": rnav_per_share},
        "notes": _rnav_notes(assum, assets, discount, rnav_per_share),
        "sources": [
            "Sectors API: company_report, financials (cash, debt, equity), ownership",
            f"data/assumptions/{payload.get('ticker', '?')}.json (assets, rnav_discount, shares)",
            "Aritmetika RNAV terbuka (bukan engine pihak ketiga): SUM(NAV x kepemilikan) + kas - utang - overhead",
        ],
    }
    return _view_rnav(page)


def _rnav_parameter_rows(assum: dict, debt: float, cash: float, overhead: float) -> list[tuple[str, str, str]]:
    def f(v):
        return f"{_nf.idn(v, digits=1)}".replace(",", ".")
    return [
        ("Discount to RNAV yang dipakai", f"{_nf.dec((assum.get('rnav_discount') or 0) * 100, digits=1)}%",
         assum.get("rnav_discount_basis") or "judgment call analis (basis belum dicantumkan)"),
        ("Basis pembanding discount", assum.get("rnav_discount_comparables") or "tidak ada basis pembanding",
         "discount historis emiten sejenis / rata-rata sektor"),
        ("Cash & Equivalents", f(bn_cash := cash) + " bn", "neraca Sectors tanggal valuasi"),
        ("Total Debt", f(debt) + " bn", "neraca Sectors tanggal valuasi"),
        ("Corporate overhead (PV)", f(overhead) + " bn", "assumptions.corporate_overhead_pv_bn"),
        ("Jumlah saham beredar (bn)", f"{_nf.idn((assum.get('shares_out') or 0) / 1e9, digits=4)}", "Sectors company_report"),
    ]


def _rnav_notes(assum: dict, assets: list, discount, rnav_per_share) -> list[str]:
    notes = []
    unsourced = [a["name"] for a in assets if a["nav_source"] == "sumber tidak dicantumkan"]
    outside = [a["name"] for a in assets if not a.get("nav_source_is_sectors")]
    if unsourced:
        notes.append(
            "NAV per aset berikut belum mencantumkan sumber (wajib diisi sebelum dipublikasikan): "
            + ", ".join(unsourced[:5]) + ("…" if len(unsourced) > 5 else "")
        )
    comparables = assum.get("rnav_discount_comparables")
    if comparables:
        notes.append(f"Discount to RNAV {_nf.dec((discount or 0) * 100, digits=1)}% punya basis pembanding: {comparables}.")
    else:
        notes.append(
            f"Discount to RNAV {_nf.dec((discount or 0) * 100, digits=1)}% adalah PURE JUDGMENT: tidak ada basis pembanding "
            "di data, jadi dinyatakan sebagai asumsi analis dan bukan angka final yang punya dasar pasar."
        )
    if not any(a["discount_rate"] is not None for a in assets):
        notes.append(
            "Discount rate per aset belum tersedia, jadi Exhibit 9 menampilkan parameter bridge dan grid "
            "memakai rentang discount rate indikatif - bukan WACC hasil perhitungan per proyek."
        )
    if outside:
        notes.append(
            "NAV dari luar Sectors terdeteksi pada: " + ", ".join(outside) + " - aturan proyek hanya "
            "mengizinkan data Sectors, jadi baris ini harus diganti sumber Sectors atau dihapus."
        )
    notes.append(
        "RNAV tidak memakai terminal growth: aset dinilai satu per satu, jadi tidak ada klaim cadangan abadi."
    )
    if rnav_per_share is not None and rnav_per_share <= 0:
        notes.append(
            "PERIKSA BRIDGE: RNAV per saham nol atau negatif, artinya utang dan overhead menelan seluruh NAV "
            "aset. Halaman tetap menampilkannya apa adanya supaya tidak terbaca sebagai nilai wajar yang sehat."
        )
    return notes


def _fmt(value, digits: int = 1) -> str:
    if value is None:
        return "\u2014"
    return f"{value:,.{digits}f}".replace(",", "\u2009").replace(".", ",").replace("\u2009", ".")


def _fmt0(value) -> str:
    return "\u2014" if value is None else f"{_nf.idn(value, digits=0)}".replace(",", ".")


def _view_rnav(page: dict) -> dict:
    """Shape the RNAV page for the shared markup."""
    b = page["bridge"]
    page["exhibit8_title"] = "Asset Breakdown and RNAV Bridge"
    page["block1_rows"] = [
        (
            a["name"],
            [
                _fmt(a["size"], 0) + (" " + a["size_unit"] if a["size_unit"] else ""),
                _fmt(a["nav"]),
                f"{_nf.dec(a['ownership'] * 100, digits=1)}%" if a["ownership"] is not None else "\u2014",
                _fmt(a["nav_attributable"]),
                a["nav_source"],
            ],
        )
        for a in page["assets"]
    ]
    page["block1_headers"] = ["Aset / proyek", "Ukuran", "NAV per aset (Rp bn)", "% kepemilikan",
                              "NAV attributable (Rp bn)", "Sumber NAV"]
    page["block2_headers"] = ["Blok 2 - Bridge RNAV", "Rp bn", "Per saham (Rp)"]
    page["block2_rows"] = [
        ("Sum of NAV (attributable ke emiten)", _fmt(b["sum_nav"]), "\u2014"),
        ("(+) Cash & Equivalents", _fmt(b["cash"]), "\u2014"),
        ("(-) Total Debt", _fmt(-b["total_debt"]), "\u2014"),
        ("(-) Corporate overhead (PV)", _fmt(-b["overhead"]), "\u2014"),
        ("Total RNAV", _fmt(b["total_rnav"]), _fmt0(b["rnav_per_share"])),
        ("(-) Discount to RNAV", _fmt(b["discount"] * 100, 1) + "%", "\u2014"),
    ]
    page["block3_headers"] = ["Blok 3 - Target price", "Nilai", "Catatan"]
    page["block3_rows"] = [
        ("RNAV per share", _fmt0(b["rnav_per_share"]), "sebelum discount"),
        ("Target Price = RNAV per share x (1 - discount)", _fmt0(b["target_price"]), "highlight: angka yang dipakai laporan"),
        ("Harga pasar", _fmt0(page["drivers"]["price"]), "Sectors, penutupan terakhir"),
    ]
    page["sensitivity"]["columns"] = [f"{_nf.dec(d * 100, digits=0)}%" for d in page["sensitivity"]["cols_axis"]]
    page["sensitivity"]["rows"] = [
        {
            "label": f"rate {_nf.dec(r * 100, digits=1)}%" if page["sensitivity"]["wacc_axis"][0] < 1 else f"{_nf.dec(r, digits=1)}%",
            "cells": [
                {"value": _fmt0(v), "base": (i == page["sensitivity"]["base"][0]
                                             and j == page["sensitivity"]["base"][1])}
                for j, v in enumerate(row)
            ],
        }
        for i, (r, row) in enumerate(zip(page["sensitivity"]["wacc_axis"], page["sensitivity"]["fair_value"]))
    ]
    page["sensitivity"]["base_wacc"] = page["sensitivity"]["rows"][2]["label"]
    page["sensitivity"]["base_g"] = page["sensitivity"]["columns"][2]
    page["narrative"] = _narrative_rnav(page)
    page["crosscheck_rows"] = [
        ("RNAV (halaman ini)", _fmt0(b["target_price"]), "Target price dari NAV aset dikurangi discount"),
        ("RNAV per share (tanpa discount)", _fmt0(b["rnav_per_share"]), "Batas atas bila discount nol"),
        ("DCF FCFF (leg intrinsik lain)", _fmt0(page["legs"].get("dcf")), "Pembanding arus kas"),
        ("EV/EBITDA mid-cycle", _fmt0(page["legs"].get("ev_ebitda")), "ANCHOR relatif bila dipakai"),
    ]
    return page


def _narrative_rnav(page: dict) -> list[str]:
    b = page["bridge"]
    swing = page["sensitivity"]["swing"]
    grid = page["sensitivity"]["fair_value"]
    disc_span = [row[0] for row in grid]
    return [
        (
            f"Nilai halaman ini berdiri di NAV aset, bukan di satu arus kas agregat: "
            f"{len(page['assets'])} aset, NAV attributable Rp {_fmt(b['sum_nav'])} bn, bridge ke "
            f"Rp {_fmt(b['total_rnav'])} bn RNAV atau Rp {_fmt0(b['rnav_per_share'])} per saham."
        ),
        (
            f"Discount to RNAV {_fmt((b['discount'] or 0) * 100, 1)}% menurunkan RNAV per saham menjadi target "
            f"price Rp {_fmt0(b['target_price'])}. Besaran discount ini yang paling memengaruhi hasil: di dalam "
            f"grid, target price bergerak Rp {_fmt0(swing['min'])} sampai Rp {_fmt0(swing['max'])}. "
            "Kalau discountnya tidak punya basis pembanding (discount historis emiten sejenis atau rata-rata "
            "sektor), halaman menyatakannya sebagai pure judgment assumption."
        ),
        (
            "Dua hal harus dijaga saat aset bertambah: setiap NAV per aset wajib punya sumber (DCF per proyek "
            "atau appraisal pihak ketiga), dan aset development-stage sebaiknya memakai discount rate berbeda - "
            "Exhibit 9 menampilkan parameter per aset begitu datanya ada."
        ),
    ]
