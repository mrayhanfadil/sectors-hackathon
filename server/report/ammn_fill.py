"""AMMN live-payload fill from Sectors-harvested artifacts (AMMN-FILLT lane).

Reads the sibling lane's harvest at ``output/cache/ammn_fill/*.json``
(kanban t_2c5f420e, 13 billed credits) and fills every FILL_MAP-mapped key
of the DATA_CONTRACT payload built by server/routers/pdf.py.

Rules (LOUD policy):
  - FILL_MAP GAPs stay honest-empty (None / "-" / pending notes). No synthetic fill.
  - Missing cache dir/files -> section stays honest-empty, never raises.
  - No Sectors calls here: 0 credits, keyless-safe.
  - AMMN-only: the caller gates on ticker == "AMMN".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit
from server.report import numfmt as _nf

REPO_ROOT = Path(__file__).resolve().parents[2]
FILL_DIR = REPO_ROOT / "output" / "cache" / "ammn_fill"

# Thesis-relevant AMMN-tagged picks (FILL_MAP section 9). Matched by timestamp.
NEWS_PICKS = (
    "2026-09-10T15:30:00",
    "2026-09-09T09:17:00",
    "2026-09-09T08:30:00",
    "2026-09-03T18:40:00",
    "2026-09-03T06:33:00",
    "2026-08-31T17:25:39",
    "2026-08-27T07:59:26",
    "2026-08-21T08:51:32",
)

GAPS = [
    "G1 cover.vs_jci.ytd_abs/ytd_rel - YTD window (253d) unreachable, API caps at 90d",
    "G2 cover.shares.free_float_pct - no free-float print (screener projects symbol+name only)",
    "G3 segments FY2025 - /company/get-segments FY2025 -> 404; FY2024 latest",
    "G4 mining extension - AMMN absent from mining universe (9 coal names; keyword empty)",
    "G5 forward numbers - forward_pe + company/growth forecasts null",
    "G6 dividend/DPS - all dividend fields null (no dividend since 2023-07-07 listing)",
    "G7 KPI volumes - no volumetric line in any AMMN payload",
    "G8 peer EV/EBITDA - peer rows carry no EBITDA/debt/cash",
    "G9 valuation.bands - no band series beyond 4 annual multiple prints",
    "G10 reserve life/grade/C1-AISC - absent everywhere",
]


def _load(name: str) -> Optional[Any]:
    try:
        p = FILL_DIR / (name + ".json")
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _bn(x: Any, digits: int = 1) -> Any:
    """IDR -> IDR bn (rounded), None/unparseable -> honest dash."""
    if x is None:
        return "-"
    try:
        return round(float(x) / 1e9, digits)
    except Exception:
        return "-"


def _idn(x: Any, digits: int = 2) -> str:
    """id-ID number for reader-facing copy: 24.978,8 / +20,84% (matches the cover tables)."""
    if not isinstance(x, (int, float)):
        return "-"
    s = f"{x:,.{digits}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _pct100(x: Any, digits: int = 2) -> Any:
    if x is None:
        return "-"
    try:
        return round(float(x) * 100, digits)
    except Exception:
        return "-"


def _yoy(cur: Any, prev: Any, digits: int = 1) -> Any:
    try:
        c, p = float(cur), float(prev)
        if p == 0:
            return "-"
        return round((c - p) / abs(p) * 100, digits)
    except Exception:
        return "-"


def _idr_t(x: Any) -> str:
    """IDR -> 'Rp xxx,xx T' for prose."""
    try:
        return f"Rp {_nf.idn(float(x) / 1e12, digits=2)} tn"
    except Exception:
        return "-"


def _slide2_sector_blocks(payload: dict, filled: list) -> None:
    """Sector, filing, corporate-action, ownership and free-float blocks for the deck's page 2.

    Every value is what the Sectors endpoints returned for this ticker. The only arithmetic done
    here is summing returned numbers (insider buys per holder, insider value) and differencing two
    monthly ownership rows; the page states which of those are sums rather than reported figures. A
    block whose endpoint returned nothing is left ABSENT, so the page writes "tidak tersedia"
    instead of a plausible number.
    """
    sr = _load("subsector_report_basic-materials") or {}
    growth = ((sr.get("growth") or {}).get("growth_forecasts") or {}).get("2026") or {}
    hist = (((sr.get("growth") or {}).get("weighted_avg_growth_data") or {}).get("2025")) or {}
    companies = (sr.get("companies") or {}).get("top_companies") or {}
    mcap = [
        {"symbol": k, "name": (v or {}).get("name"), "market_cap": (v or {}).get("market_cap")}
        for k, v in (companies.get("top_mcap") or {}).items()
    ]
    mcap = sorted([m for m in mcap if m.get("market_cap")], key=lambda m: -m["market_cap"])
    if mcap or growth:
        payload["sector_data"] = {
            "subsector": sr.get("sub_sector") or sr.get("sector"),
            "growth_forecast_2026": {
                "revenue_pct": _pct100(growth.get("revenue_growth")),
                "eps_pct": _pct100(growth.get("eps_growth")),
                "base_year": growth.get("base_year"),
            },
            "growth_actual_2025": {
                "revenue_pct": _pct100(hist.get("avg_annual_revenue_growth")),
                "eps_pct": _pct100(hist.get("avg_annual_earning_growth")),
            },
            "top_mcap": mcap[:5],
            "source": "Sectors subsector report (basic-materials)",
        }
        filled.append(f"sector_data[{len(mcap[:5])} top mcap, growth 2025+2026F]")

    fl = _load("filings_AMMN") or {}
    rows = [r for r in (fl.get("results") or []) if isinstance(r, dict)]
    if rows:

        def _agg(items: list) -> dict:
            return {
                "n": len(items),
                "shares": sum(int(r.get("amount_transaction") or 0) for r in items),
                "value": sum(float(r.get("transaction_value") or 0) for r in items),
                "holders": sorted({str(r.get("holder_name")) for r in items if r.get("holder_name")}),
                "first": min(
                    (str(r.get("timestamp"))[:10] for r in items if r.get("timestamp")), default=None
                ),
                "last": max(
                    (str(r.get("timestamp"))[:10] for r in items if r.get("timestamp")), default=None
                ),
            }

        by_type: dict = {}
        for r in rows:
            by_type.setdefault(str(r.get("transaction_type") or "?").lower(), []).append(r)
        payload["filings_digest"] = {
            "n": len(rows),
            "buy": _agg(by_type.get("buy") or []),
            "sell": _agg(by_type.get("sell") or []),
            "source": "Sectors filings (keterbukaan IDX, dokumen terakhir yang dikembalikan endpoint)",
        }
        filled.append(f"filings_digest[{len(rows)} filings: buy/sell split]")

    ca = (_load("corporate_actions_AMMN") or {}).get("corporate_actions") or {}
    if ca:
        payload["corporate_actions"] = {
            "agm": [str(a.get("agm_date")) for a in (ca.get("agm") or []) if a.get("agm_date")],
            "dividend": ca.get("dividend"),
            "upcoming_dividend": ca.get("upcoming_dividend"),
            "bonus": ca.get("bonus"),
            "right_issue": ca.get("right_issue"),
            "stock_split": ca.get("stock_split"),
            "warrant": ca.get("warrant"),
            "source": "Sectors corporate-actions",
        }
        filled.append("corporate_actions[agm + dividend status]")

    sh = _load("shareholders_composition_AMMN") or {}
    sh_rows = [r for r in (sh.get("data") or []) if isinstance(r, dict)]
    if sh_rows:
        ordered = sorted(sh_rows, key=lambda r: str(r.get("date")))

        def _mix(r: dict) -> dict:
            return {
                "date": str(r.get("date")),
                "domestic": r.get("total_l"),
                "foreign": r.get("total_f"),
                "foreign_institutions": r.get("financial_institutions_f"),
                "foreign_mutual_fund": r.get("mutual_fund_f"),
                "foreign_corporate": r.get("corporate_f"),
                "individuals": r.get("individual_l"),
                "insurance": r.get("insurance_l"),
            }

        payload["ownership_mix"] = {
            "latest": _mix(ordered[-1]),
            "first": _mix(ordered[0]),
            "months": len(ordered),
            "source": "Sectors shareholders-composition (bulanan)",
        }
        filled.append(f"ownership_mix[{len(ordered)} bulan lokal vs asing]")

    ff = _load("screener_free_float_top25") or {}
    ff_rows = [r for r in (ff.get("results") or []) if isinstance(r, dict)]
    if ff_rows:
        payload["free_float"] = {
            "n": len(ff_rows),
            "in_list": any("AMMN" in str((r.get("symbol") or "")) for r in ff_rows),
            "source": "Sectors screener (25 emiten, daftar tanpa persentase)",
        }
        filled.append(f"free_float[in top-{len(ff_rows)} list]")


def apply_ammn_fill(payload: dict, assum: dict, fv: float,
                    rating: str, upside: Optional[float],
                    wacc_val: float, anchor_basis: Optional[str] = None,
                    anchor_leg: Optional[str] = None) -> dict:
    """Fill FILL_MAP-mapped keys into a live payload (AMMN-only).

    Mutates ``payload`` in place, stamps ``payload["fill_meta"]`` with
    ``{"filled": [...], "gaps": [...]}`` and returns it. Never raises:
    a missing cache keeps the honest-empty defaults.
    """
    filled: list[str] = []
    rep = _load("company_report_AMMN_multisection")
    if not isinstance(rep, dict):
        payload["fill_meta"] = {
            "filled": [],
            "gaps": ["no_cache: output/cache/ammn_fill absent - honest-empty kept"],
        }
        return payload["fill_meta"]

    ov = rep.get("overview") or {}
    fin = rep.get("financials") or {}
    val = rep.get("valuation") or {}
    own = rep.get("ownership") or {}

    # ---- annual tables (single source so tie-outs hold by construction) ----
    hist = [r for r in (fin.get("historical_financials") or []) if isinstance(r, dict)]
    by_year = {int(r["year"]): r for r in hist if r.get("year") is not None}
    years = sorted(by_year)
    rats: dict[int, dict] = {}
    for r in (fin.get("historical_financial_ratio") or []):
        try:
            rats[int(str(r.get("year")))] = r
        except Exception:
            continue
    heps = fin.get("historical_eps") or {}
    eps_y = {int(k): (v or {}).get("eps") for k, v in heps.items()}
    hv = {int(r["year"]): r for r in (val.get("historical_valuation") or [])
          if isinstance(r, dict) and r.get("year") is not None}

    def col(fn) -> list:
        return [fn(by_year[y]) for y in years]

    ylabels = [f"FY{str(y)[2:]}A" for y in years]
    rev = col(lambda r: _bn(r.get("revenue")))
    ebitda = col(lambda r: _bn(r.get("ebitda")))
    earn = col(lambda r: _bn(r.get("earnings")))
    gross = col(lambda r: _bn(r.get("gross_profit")))
    ebit = col(lambda r: _bn(r.get("ebit")))
    interest = col(lambda r: _bn(r.get("interest_expense_non_operating")))
    ebt = col(lambda r: _bn(r.get("earnings_before_tax")))
    tax = col(lambda r: _bn(r.get("tax")))
    # minorities: EBT - tax - earnings (derived, exact by construction)
    minorities = []
    for y in years:
        r = by_year[y]
        try:
            minorities.append(round(
                (float(r.get("earnings_before_tax") or 0)
                 - float(r.get("tax") or 0)
                 - float(r.get("earnings") or 0)) / 1e9, 1))
        except Exception:
            minorities.append("-")
    assets = col(lambda r: _bn(r.get("total_assets")))
    equity = col(lambda r: _bn(r.get("total_equity")))
    liab = col(lambda r: _bn(r.get("total_liabilities")))
    debt = col(lambda r: _bn(r.get("total_debt")))
    cash = col(lambda r: _bn(r.get("cash_and_equivalents")))
    inv = col(lambda r: _bn(r.get("inventories")))
    ocf = col(lambda r: _bn(r.get("operating_cash_flow")))
    icf = col(lambda r: _bn(r.get("investing_cash_flow")))
    fcf_cf = col(lambda r: _bn(r.get("financing_cash_flow")))
    net_cf = col(lambda r: _bn(r.get("net_cash_flow")))
    capex = col(lambda r: _bn(r.get("capital_expenditure")))
    cost = []
    for y in years:
        r = by_year[y]
        if r.get("cost_of_revenue") is not None:
            cost.append(_bn(r.get("cost_of_revenue")))
        elif r.get("revenue") is not None and r.get("gross_profit") is not None:
            try:
                cost.append(round((float(r["revenue"]) - float(r["gross_profit"])) / 1e9, 1))
            except Exception:
                cost.append("-")
        else:
            cost.append("-")
    opex = []
    for y in years:
        r = by_year[y]
        if r.get("operating_expense") is not None:
            opex.append(_bn(r.get("operating_expense")))
        elif r.get("gross_profit") is not None and r.get("operating_pnl") is not None:
            try:
                opex.append(round((float(r["gross_profit"]) - float(r["operating_pnl"])) / 1e9, 1))
            except Exception:
                opex.append("-")
        else:
            opex.append("-")

    def rget(y: int, *path: str) -> Any:
        cur: Any = rats.get(y, {})
        for k in path:
            cur = (cur or {}).get(k)
        return cur

    roe = [_pct100(rget(y, "profitability", "roe")) for y in years]
    roa = [_pct100(rget(y, "profitability", "roa")) for y in years]
    npm = [_pct100(rget(y, "profitability", "net_profit_margin")) for y in years]
    gm = [_pct100(rget(y, "profitability", "gross_profit_margin")) for y in years]
    der = [round(float(rget(y, "leverage", "debt_to_equity_ratio")), 2)
           if rget(y, "leverage", "debt_to_equity_ratio") is not None else "-"
           for y in years]
    icr = [round(float(rget(y, "leverage", "interest_coverage_ratio")), 2)
           if rget(y, "leverage", "interest_coverage_ratio") is not None else "-"
           for y in years]
    emgn = []
    for rv, ev in zip(rev, ebitda):
        try:
            emgn.append(round(float(ev) / float(rv) * 100, 1))
        except Exception:
            emgn.append("-")
    eps_row = [round(float(eps_y[y]), 2) if eps_y.get(y) is not None else "-" for y in years]
    pe_row = [round(float(hv[y]["pe"]), 2) if y in hv and hv[y].get("pe") is not None else "-"
              for y in years]
    pb_row = [round(float(hv[y]["pb"]), 2) if y in hv and hv[y].get("pb") is not None else "-"
              for y in years]
    ev_row = [round(float(hv[y]["enterprise_to_ebitda"]), 2)
              if y in hv and hv[y].get("enterprise_to_ebitda") is not None else "-"
              for y in years]

    def growth(vals: list) -> list:
        out: list = ["-"]
        for c, p in zip(vals[1:], vals[:-1]):
            out.append(_yoy(c, p) if isinstance(c, (int, float)) and isinstance(p, (int, float)) else "-")
        return out

    rev_g, ebitda_g, earn_g = growth(rev), growth(ebitda), growth(earn)

    # ---- quarterly TTM (file order is newest-first; TTM = first 4 rows) ----
    q = _load("quarterly_AMMN_8") or {}
    qrows = q.get("data") or []
    ttm: dict[str, float] = {}
    if len(qrows) >= 4:
        for k in ("revenue", "ebitda", "earnings", "capital_expenditure",
                  "free_cash_flow", "operating_cash_flow",
                  "interest_expense_non_operating"):
            try:
                ttm[k] = sum(float(r.get(k) or 0) for r in qrows[:4])
            except Exception:
                ttm[k] = 0.0
    q0 = qrows[0] if qrows else {}
    try:
        ttm_netd_ebitda = round((float(q0.get("total_debt") or 0) - float(q0.get("cash_only") or 0))
                                / ttm["ebitda"], 2)
    except Exception:
        ttm_netd_ebitda = None
    try:
        ttm_ebitda_int = round(ttm["ebitda"] / ttm["interest_expense_non_operating"], 2)
    except Exception:
        ttm_ebitda_int = None
    try:
        q0_emgn = round(float(q0.get("ebitda") or 0) / float(q0.get("revenue") or 1) * 100, 1)
        q0_gmgn = round(float(q0.get("gross_profit") or 0) / float(q0.get("revenue") or 1) * 100, 1)
    except Exception:
        q0_emgn, q0_gmgn = None, None

    f2 = lambda x: f"{_nf.idn(x, digits=2)}" if isinstance(x, (int, float)) else "-"
    f1 = lambda x: f"{_nf.idn(x, digits=1)}" if isinstance(x, (int, float)) else "-"

    # ================= meta =================
    meta = payload.setdefault("meta", {})
    meta["company_name"] = rep.get("company_name") or meta.get("company_name")
    meta["sector"] = "Basic Materials - Metals & Minerals"
    meta["subsector"] = "basic-materials"
    meta["date"] = "11 Sep 2026"
    filled.append("meta(company_name/sector/subsector/date)")

    # ================= cover =================
    cover = payload.setdefault("cover", {})
    last_price = (val.get("last_close_price")
                  or ov.get("last_close_price") or assum.get("last_price"))
    tp_int = int(round(fv or 0))
    up_txt = (("+" if upside > 0 else "") + _idn(upside, 2) + "%") if isinstance(upside, (int, float)) else "-"

    ttm_eb_tn = ttm.get("ebitda", 0) / 1e12
    ttm_rev_tn = ttm.get("revenue", 0) / 1e12
    # === dynamic EV/EBITDA (Sep 17 2026) ===
    # Bug from editorial review: cover hardcoded "17,99×" while peer table
    # computed 18,38× from the canonical block (362.24 tn mcap). The cover
    # value was stale from the pre-fix mcap (352.4 tn) and never matched the
    # peer table. Fix: compute EV/EBITDA from the SAME canonical block the
    # peer table reads, plus the TTM EBITDA just summed above.
    # Historical years (FY23/FY24/FY25) used frozen literals too; here they
    # are computed at today's EV (canonical mcap + canonical net_debt) over
    # the year-end EBITDA so the comparison set is internally consistent.
    canon = payload.get("canonical_metrics") or {}
    canon_mcap = canon.get("market_cap_rpbn", {}).get("value") if isinstance(canon.get("market_cap_rpbn"), dict) else canon.get("market_cap_rpbn")
    if canon_mcap is None:
        # Fallback: assumption file last_price * shares / 1e9 to get rp_bn
        canon_mcap = ((assum.get("last_price") or 0) * (assum.get("shares_out") or 0)) / 1e9
    canon_net_debt = assum.get("net_debt_after_cash")
    if canon_net_debt is None:
        canon_net_debt = float(q0.get("total_debt") or 0) - float(q0.get("cash_only") or 0)
    # canon_mcap is rp_bn (trillion rupiah), canon_net_debt is full rupiah.
    # EV in full rupiah = canon_mcap * 1e9 + canon_net_debt. EV in tn = /1e12.
    canon_ev_rupiah = (canon_mcap or 0) * 1e9 + canon_net_debt
    canon_ev_tn = canon_ev_rupiah / 1e12
    ttm_ev_eb = canon_ev_rupiah / ttm["ebitda"] if (ttm.get("ebitda") and canon_ev_rupiah) else None
    midc = (assum.get("ebitda_midcycle_constituents") or {})
    hist_mults = {
        yr: round(canon_ev_rupiah / midc[yr], 2) if midc.get(yr) else None
        for yr in ("FY2023", "FY2024", "FY2025")
    }
    # Surface EV/EBITDA inputs into cover.meta so other renderers (slide2
    # build_katalis) can read the same canonical basis instead of carrying
    # their own literals (the editorial-review Bug 4 root cause).
    cover_meta = cover.setdefault("meta", {})
    cover_meta["net_debt_after_cash"] = canon_net_debt
    cover_meta["ebitda_ttm"] = ttm.get("ebitda", 0)
    cover_meta["market_cap_rpbn"] = canon_mcap
    cover_meta["ev_ebitda_ttm_x"] = ttm_ev_eb
    rbox = cover.setdefault("rating_box", {})
    # Cover copy is reader-facing Indonesian, so numbers use id-ID separators (24,98 tn /
    # +20,84%) to match the sidebar tables. English separators here made the same figure read
    # two different ways on one page.
    # === forward bridge (owner rule: equity report looks forward, not back) ===
    # Bullet 3 carries the FY26F-28F path + CAGR + physical driver, read from the
    # same driver file the Key Financials exhibit resolves (no hand-typed numbers).
    # Falls back to a loud label when the file is absent/invalid - never silent.
    fwd_rev26 = fwd_rev28 = fwd_eb26 = fwd_eb28 = None
    fwd_mgn26 = fwd_mgn28 = fwd_cagr_eb = None
    fwd_note_short = ""
    fwd_basis_txt = "level normalised mid-cycle"
    try:
        _drv_path = REPO_ROOT / "data" / "drivers" / "AMMN.json"
        if _drv_path.exists():
            _drv = json.loads(_drv_path.read_text())
            _fx = float(_drv.get("fx_rp_bn_per_usd_mn") or 1.0)
            _dr = _drv.get("drivers") or {}
            _rp = lambda k, i: ((_dr.get(k) or {}).get("path") or [None, None, None])[i] * _fx \
                if isinstance(((_dr.get(k) or {}).get("path") or [None])[i], (int, float)) else None
            fwd_rev26, fwd_rev28 = _rp("revenue", 0), _rp("revenue", 2)
            fwd_eb26, fwd_eb28 = _rp("ebitda", 0), _rp("ebitda", 2)
            if fwd_rev26 and fwd_eb26:
                fwd_mgn26 = fwd_eb26 / fwd_rev26 * 100
            if fwd_rev28 and fwd_eb28:
                fwd_mgn28 = fwd_eb28 / fwd_rev28 * 100
            if fwd_eb26 and fwd_eb28 and fwd_eb26 > 0 and fwd_eb28 > 0:
                fwd_cagr_eb = ((fwd_eb28 / fwd_eb26) ** 0.5 - 1) * 100
            _rn = str(((_dr.get("revenue") or {}).get("note")) or "")
            # first physical driver clause only (Phase-8 ramp), not the whole note
            fwd_note_short = _rn.split(" plus ")[0].split(", new processing")[0].strip()
            if str(_drv.get("basis") or "") == "third-party-estimate":
                fwd_basis_txt = "estimasi tim atas basis data berlisensi"
    except Exception:
        pass
    if fwd_eb26 and fwd_eb28 and fwd_cagr_eb is not None:
        _fwd_b3 = (
            f"Ke depan FY26F-28F: EBITDA Rp {_idn(fwd_eb26 / 1000, 1)} tn → Rp {_idn(fwd_eb28 / 1000, 1)} tn "
            f"(CAGR {_idn(fwd_cagr_eb, 1)}%, marjin {_idn(fwd_mgn26, 1)}%→{_idn(fwd_mgn28, 1)}%) - "
            f"{fwd_note_short}; TP Rp {_idn(tp_int, 0)} ({rating}, {_idn(upside, 2)}%) anchor EV/EBITDA FY26F."
        )
    else:
        _fwd_b3 = (
            f"Ke depan FY26F-28F ({fwd_basis_txt}): jalur proyeksi tidak terverifikasi di file driver - "
            f"lihat tabel Key Financials; TP Rp {_idn(tp_int, 0)} ({rating}, {_idn(upside, 2)}%) anchor EV/EBITDA FY26F."
        )
    rbox["key_takeaways"] = [
        f"Tembaga+emas 100% pendapatan FY2024 (emas 55,0% menyalip tembaga 45,0%) - Sectors get-segments FY2024.",
        f"EBITDA TTM {_idn(ttm_eb_tn, 2)} tn, marjin EBITDA Q1-2026 {_idn(q0_emgn, 1)}%; net-debt/EBITDA TTM {_idn(ttm_netd_ebitda, 1)}× - Sectors quarterly 8Q.",
        _fwd_b3,
    ]
    cover["summary"] = (
        f"PT Amman Mineral Internasional Tbk. (AMMN) - penambang tembaga-emas Batu Hijau "
        f"(listing 7 Jul 2023, LQ45/KOMPAS100, 1.525 karyawan). "
        f"Pendapatan FY2024 Rp 43,04 tn: emas 55,0% (Rp 23,67 tn) menyalip tembaga 45,0% "
        f"(Rp 19,36 tn), dari 43,5%/56,5% di FY2023 - Sectors get-segments FY2024+FY2023. "
        f"EBITDA TTM Rp {f2(ttm_eb_tn)} tn atas pendapatan Rp {f2(ttm_rev_tn)} tn; marjin EBITDA "
        f"Q1-2026 {f1(q0_emgn)}% (bruto {f1(q0_gmgn)}%) - Sectors quarterly 8Q to 2026-03-31. "
        f"Utang bruto Rp {f2(float(q0.get('total_debt') or 0) / 1e12)} tn vs kas Rp "
        f"{f2(float(q0.get('cash_only') or 0) / 1e12)} tn; net-debt/EBITDA TTM {f1(ttm_netd_ebitda)}×, "
        f"EBITDA/bunga TTM {f1(ttm_ebitda_int)}×. "
        f"Harga 90d +28,57% vs IHSG +4,58% (rel +23,99 pp, 62 sesi 15 Jun–11 Sep 2026); "
        f"EV/EBITDA 2026 (TTM print) {_idn(ttm_ev_eb, 2)}× vs {_idn(hist_mults.get('FY2025'), 2)}× (2025) - de-rating adalah argumen, kontra: PE 38,23× "
        f"vs rerata peer sektor 10,07× (agregat konsensus rating broker tidak dipublikasikan). "
        f"Target harga Rp {_idn(tp_int, 0)} ({rating}, {up_txt}) berjangkar pada SATU FV engine "
        f"(EV/EBITDA FY26F, bukan intrinsic_value API Rp -11.850 yang tak terpakai). "
        f"Profil gate: domain mining, filing 6 thn (gate_inputs AMMN.json)."
    )
    filled.append("cover.summary+key_takeaways")

    # ---- vs IHSG (90d chart FILLED; YTD stays GAP G1) ----
    daily = _load("daily_AMMN_90d") or {}
    idx = _load("index_daily_lowercase_ihsg_90d")
    drows = daily.get("data") or []
    irows = idx if isinstance(idx, list) else (idx.get("data") if isinstance(idx, dict) else []) or []
    ipx = {r.get("date"): r.get("price") for r in irows if isinstance(r, dict)}
    labels, s_ammn, s_ihsg = [], [], []
    for r in drows:
        d = r.get("date")
        if d in ipx and r.get("close") is not None and ipx[d] is not None:
            labels.append(d)
            s_ammn.append(r["close"])
            s_ihsg.append(ipx[d])
    if labels:
        a0, a1 = s_ammn[0], s_ammn[-1]
        i0, i1 = s_ihsg[0], s_ihsg[-1]
        a_chg = round((a1 - a0) / a0 * 100, 2)
        i_chg = round((i1 - i0) / i0 * 100, 2)
        rel = round(a_chg - i_chg, 2)
        cover["vs_jci"] = {
            "ytd_abs": None,
            "ytd_rel": None,
            "source": "Sectors /daily/AMMN + /index-daily/ihsg (90d, 62 sesi 15 Jun–11 Sep 2026)",
            "note": (f"YTD tak terjangkau (cap API 90 hari < jendela YTD 253 hari); tersedia 90d "
                     f"AMMN {_nf.dec(a_chg, digits=2, signed=True)}% vs IHSG {_nf.dec(i_chg, digits=2, signed=True)}% (rel {_nf.dec(rel, digits=2, signed=True)} pp) - tanpa deret sintetik"),
            "chart": {"labels": labels, "series": [s_ammn, s_ihsg]},
        }
        cover["price_chart"] = {
            "title": "Kinerja Harga vs IHSG (90D, 15 Jun–11 Sep 2026)",
            "label": f"Kinerja Harga AMMN ({_nf.dec(a_chg, digits=1, signed=True)}% 90D) vs IHSG ({_nf.dec(i_chg, digits=1, signed=True)}% 90D)",
            "caption": f"Performa Relatif 90D: Outperform {_nf.dec(rel, digits=1, signed=True)} pp (YTD tak tersedia - cap API 90 hari)",
        }
        filled.append("cover.vs_jci.series+price_chart")
    cover["market"] = {
        "market_cap": _idr_t(ov.get("market_cap")).replace(" tn", " T"),
        "index_class": "LQ45 · KOMPAS100 · ECONOMIC30 · FTSE",
    }
    try:
        atp = ov.get("all_time_price") or {}
        lo = list((atp.get("52_w_low") or {}).values())
        hi = list((atp.get("52_w_high") or {}).values())
        if lo and hi:
            cover["market"]["range_52w"] = f"Rp {_nf.idn(min(lo), 0)}–{_nf.idn(max(hi), 0)}"
    except Exception:
        pass
    filled.append("cover.market")

    # ---- shares / shareholders ----
    scomp = _load("shareholders_composition_AMMN") or {}
    srows = scomp.get("data") or []
    if srows:
        try:
            cover["shares"] = {
                "outstanding": round(float(srows[0].get("shares_number") or 0) / 1e9, 1),
                "unit": "bn",
                "free_float_pct": None,
                "note": ("72.518.217.656 sh (shareholders-composition 31 Agu 2026); free float tak ada "
                         "print Sectors - bucket Publik 25,26% bukan definisi free float IDX (GAP G2)"),
            }
            filled.append("cover.shares.outstanding")
        except Exception:
            pass
    holders = []
    for h in (own.get("major_shareholders") or []):
        try:
            holders.append({"name": h.get("name"),
                            "pct": round(float(h.get("share_percentage")) * 100, 2)})
        except Exception:
            continue
    if holders:
        cover["shareholders"] = holders
        cover["shareholders_src"] = "Sectors company/report ownership (12 pemegang, 11 Sep 2026)"
        cover["shareholders_note"] = ("Lokal 86,50% / asing 13,50% (31 Agu 2026); 45.155 pemegang (31 Jul 2026). "
                                      "Bucket Publik 25,26% ≠ free float IDX.")
        filled.append("cover.shareholders[12]")
    cover["esg"] = {
        "found": True,
        "score": ov.get("esg_score"),
        "source": "Sectors overview (11 Sep 2026)",
        "date": "2026-09-11",
        "note": ("Skor ESG tunggal 38,69 - tak ada rincian E/S/G di API; box E/S/G disembunyikan "
                 "sampai rincian tersedia (tanpa karangan komponen)"),
    }
    filled.append("cover.esg(score)")

    # ================= financial_highlights (6Y) =================
    fh = payload.setdefault("financial_highlights", {})
    fh["years"] = ylabels
    fh["source"] = "Sectors company/report financials.historical_financials (IDR bn)"
    fh["note"] = ("FY2020-22 cash_only null → blank, tanpa interpolasi; FY2025 & Q1-2025 terdistorsi "
                  "ramp-up smelter (basis pendapatan Q1-2025 Rp 35,3 md)")
    fh["rows"] = [
        ["Pendapatan Bersih (Rp bn)", *rev],
        ["EBITDA (Rp bn)", *ebitda],
        ["Laba Bersih (Rp bn)", *earn],
        ["Marjin EBITDA (%)", *emgn],
        ["Marjin Bersih / NPM (%)", *npm],
        ["EPS (Rp penuh)", *eps_row],
        ["P/E (x)", *pe_row],
        ["ROE (%)", *roe],
        ["Free Cash Flow (Rp bn)", *col(lambda r: _bn(r.get("free_cash_flow")))],
    ]
    filled.append("financial_highlights(6Y,9rows)")

    # Slide-1 Key Financials (5Y window; NP ties to FH slice)
    kf_idx = [years.index(y) for y in (2021, 2022, 2023, 2024, 2025) if y in years]
    kf_y = [ylabels[i] for i in kf_idx]
    pick = lambda arr: [arr[i] for i in kf_idx]
    g_ebitda_full, g_earn_full = growth(ebitda), growth(earn)
    eps_num = [v if isinstance(v, (int, float)) else None for v in eps_row]
    g_eps_full = growth(eps_num)
    payload["key_financials"] = {
        "title": f"Key Financials ({kf_y[0]}–{kf_y[-1]})",
        "source": "Sectors company/report financials.historical_financials (IDR bn)",
        "headers": ["Metrik Finansial", *kf_y],
        "rows": [
            ["Revenue (Rp bn)", *pick(rev)],
            ["EBITDA (Rp bn)", *pick(ebitda)],
            ["EBITDA Growth %", *[g_ebitda_full[i] for i in kf_idx]],
            ["Net Profit (Rp bn)", *pick(earn)],
            ["EPS (Rp)", *pick(eps_row)],
            ["EPS Growth %", *[g_eps_full[i] for i in kf_idx]],
            ["PER (x)", *pick(pe_row)],
            ["PBV (x)", *pick(pb_row)],
            ["EV/EBITDA (x)", *pick(ev_row)],
        ],
    }
    filled.append("key_financials(5Y)")

    # ================= segments (FY2024 + FY2023) =================
    def _seg_vals(doc: Any) -> dict:
        out: dict = {}
        try:
            for e in (doc.get("revenue_breakdown") or []):
                if e.get("target") == "Total Revenue" and e.get("source") in ("Copper", "Gold"):
                    out[e["source"]] = float(e.get("value") or 0)
        except Exception:
            pass
        return out

    s24 = _seg_vals(_load("segments_AMMN_2024") or {})
    s23 = _seg_vals(_load("segments_AMMN_2023") or {})
    if s24.get("Copper") and s24.get("Gold") and s23.get("Copper") and s23.get("Gold"):
        tot24 = s24["Copper"] + s24["Gold"]
        payload["segments"] = [
            {"name": "Tembaga", "revenue": round(s24["Copper"] / 1e9, 1), "unit": "Rp bn",
             "yoy_pct": round((s24["Copper"] - s23["Copper"]) / s23["Copper"] * 100, 1),
             "share_pct": round(s24["Copper"] / tot24 * 100, 1), "pie": True,
             "source": "Sectors /company/get-segments FY2024 (9 flows)"},
            {"name": "Emas", "revenue": round(s24["Gold"] / 1e9, 1), "unit": "Rp bn",
             "yoy_pct": round((s24["Gold"] - s23["Gold"]) / s23["Gold"] * 100, 1),
             "share_pct": round(s24["Gold"] / tot24 * 100, 1), "pie": True,
             "source": "Sectors /company/get-segments FY2024 (9 flows)"},
        ]
        payload["segments_src"] = "Sectors /company/get-segments/AMMN (FY2024 latest; FY2025 -> 404)"
        payload["segments_note"] = ("FY2024 pilar terakhir tersedia (FY2025 404 'data does not exist', "
                                    "1 kredit; GAP G3). FY2023 tersedia untuk tren. Jangan infer FY2025 "
                                    "dari FY2024.")
        filled.append("segments[Cu/Au FY2024+FY2023]")

    # ================= kpis (FY2025A vs FY2024A, same-basis) =================
    if 2024 in years and 2025 in years:
        i4, i5 = years.index(2024), years.index(2025)
        payload["kpis"] = [
            {"name": "Pendapatan FY2025", "value": rev[i5], "prev": rev[i4], "unit": "Rp bn",
             "formula": f"yoy {_idn(_yoy(rev[i5], rev[i4]), 1)}% FY2025A vs FY2024A",
             "source": "Sectors annual"},
            {"name": "EBITDA FY2025", "value": ebitda[i5], "prev": ebitda[i4], "unit": "Rp bn",
             "formula": f"yoy {_idn(_yoy(ebitda[i5], ebitda[i4]), 1)}% FY2025A vs FY2024A",
             "source": "Sectors annual"},
            {"name": "D/E FY2025", "value": der[i5], "prev": der[i4], "unit": "×",
             "formula": "utang 108,37 tn vs ekuitas 90,90 tn (FY2025A)",
             "source": "Sectors annual"},
            {"name": "Interest Coverage FY2025", "value": icr[i5], "prev": icr[i4], "unit": "×",
             "formula": "tahunan; TTM Q1-2026 3,48×",
             "source": "Sectors annual + quarterly TTM"},
        ]
        payload["kpis_src"] = "Sectors API v2 - company/report + quarterly-financials (AMMN)"
        payload["kpis_note"] = ("Volume produksi/tonase, grade, C1/AISC: tak ada baris volumetrik di payload "
                                "Sectors mana pun (GAP G7/G10); AMMN absen dari mining extension (GAP G4).")
        filled.append("kpis[4 same-basis]")

    # ================= thesis (4 pillars, every number cited) =================
    tot24t = (s24.get("Copper", 0) + s24.get("Gold", 0)) / 1e12 if s24 else 0
    payload["thesis"] = [
        {"headline": "Bauran emas menyalip tembaga (FY2024)",
         "detail": (f"Pendapatan FY2024 Rp {_nf.idn(tot24t, digits=2)} tn: emas 55,0% (Rp 23,67 tn) vs tembaga 45,0% "
                    f"(Rp 19,36 tn); FY2023 masih 43,5%/56,5% (emas Rp 13,67 tn, tembaga Rp 17,72 tn). "
                    f"Marjin bruto FY2024 50,5%, operasi 44,5%."),
         "stat": "55,0%", "stat_label": "Porsi emas FY2024",
         "source": "Sectors /company/get-segments/AMMN FY2024 (9 flows) + FY2023"},
        {"headline": f"EBITDA TTM Rp {f2(ttm_eb_tn)} tn, marjin Q1-2026 {f1(q0_emgn)}%",
         "detail": (f"TTM (4 kuartal ke 2026-03-31): pendapatan Rp {f2(ttm_rev_tn)} tn, EBITDA Rp "
                    f"{f2(ttm_eb_tn)} tn, laba Rp {f2(ttm.get('earnings', 0) / 1e12)} tn. Marjin EBITDA "
                    f"Q1-2026 {f1(q0_emgn)}% (bruto {f1(q0_gmgn)}%). Basis Q1-2025 terdistorsi ramp smelter."),
         "stat": f"{f1(q0_emgn)}%", "stat_label": "Marjin EBITDA Q1-2026",
         "source": "Sectors /financials/quarterly/AMMN n_quarters=8"},
        {"headline": "Neraca pasca-smelter: kas menipis, capex run-rate turun",
         "detail": (f"Utang bruto Rp {f2(float(q0.get('total_debt') or 0) / 1e12)} tn vs kas Rp "
                    f"{f2(float(q0.get('cash_only') or 0) / 1e12)} tn (Q1-2026); net-debt/EBITDA TTM "
                    f"{f1(ttm_netd_ebitda)}×, EBITDA/bunga TTM {f1(ttm_ebitda_int)}×. Capex TTM Rp "
                    f"{f2(ttm.get('capital_expenditure', 0) / 1e12)} tn vs FCF Rp "
                    f"{f2(ttm.get('free_cash_flow', 0) / 1e12)} tn (smelter build); capex Q1-2026 turun "
                    f"ke Rp 1,60 tn dan FCF berbalik +Rp 1,69 tn."),
         "stat": f"{f1(ttm_netd_ebitda)}×", "stat_label": "Net debt / EBITDA TTM",
         "source": "Sectors quarterly 8Q (TTM ke 2026-03-31)"},
        {"headline": "De-rating multiple 2026 + arus asing membaik",
         "detail": (f"EV/EBITDA (TTM print 2026) {_idn(ttm_ev_eb, 2)}× vs {_idn(hist_mults.get('FY2025'), 2)}× (2025) / {_idn(hist_mults.get('FY2024'), 2)}× (2024) / {_idn(hist_mults.get('FY2023'), 2)}× (2023) - de-rate "
                    f"adalah argumen; kontra: PE 38,23× vs rerata peer sektor 10,07×. Asing 90d −Rp 0,37 tn "
                    f"tapi +Rp 0,24 tn dalam 30d terakhir; cluster-buy direksi Jul-2026 12.961.700 sh "
                    f"@ rata-rata Rp 3.548."),
         "stat": f"{_idn(ttm_ev_eb, 2)}×", "stat_label": "EV/EBITDA (TTM print 2026)",
         "source": "Sectors valuation.historical_valuation + foreign-flow 90d + broker-top 30d + filings Jul-2026"},
    ]
    filled.append("thesis[4 pillars]")

    # ================= financials + financial_statements ==================
    H = ["Akun", *ylabels]
    SRC = "Sectors company/report financials.historical_financials (IDR bn)"
    IS = [["Revenue", *rev], ["Cost of Revenue", *cost], ["Gross Profit", *gross],
          ["Operating Expenses", *opex], ["EBIT", *ebit], ["Interest Expense", *interest],
          ["Pre-tax Profit", *ebt], ["Income Tax", *tax], ["Minority Interest", *minorities],
          ["Net Profit", *earn]]
    BS = [["Cash & Equivalents", *cash], ["Inventory", *inv], ["Total Assets", *assets],
          ["Total Liabilities", *liab], ["Total Debt", *debt], ["Shareholders' Equity", *equity]]
    CF = [["Arus Kas Operasi", *ocf], ["Arus Kas Investasi", *icf],
          ["Arus Kas Pendanaan", *fcf_cf], ["Arus Kas Bersih", *net_cf],
          ["Belanja Modal (Capex)", *capex]]
    payload["financials"] = [
        {"title": "Income Statement", "headers": H, "rows": IS, "source": SRC},
        {"title": "Balance Sheet", "headers": H, "rows": BS, "source": SRC},
        {"title": "Cash Flow", "headers": H, "rows": CF, "source": SRC},
    ]
    payload["financials_note"] = ("Minorities = EBT-pajak-laba (derived, eksak); kas = cash_and_equivalents "
                                  "(= cash_only FY2023-25; cash_only FY2020-22 null → blank). Tanpa proyeksi.")
    payload["financial_statements"] = {
        "section_title": "Laporan Keuangan & Rasio Finansial 6 Tahun (FY20A–FY25A, aktual)",
        "section_sub": "Menjawab: Bagaimana realisasi laba rugi, neraca, likuiditas, dan profitabilitas 6 tahun?",
        "income": {"title": "Laporan Laba Rugi Komprehensif (FY20A–FY25A aktual)",
                   "headers": H, "rows": IS, "source": SRC},
        "balance": {"title": "Neraca Keuangan Ringkas (FY20A–FY25A aktual)",
                    "headers": H, "rows": BS, "source": SRC},
        "cashflow": {"title": "Laporan Arus Kas (FY20A–FY25A aktual)",
                     "headers": ["Arus Kas", *ylabels], "rows": CF, "bold_rows": [3],
                     "footers": [["Perubahan Kas Bersih", *net_cf],
                                 ["Saldo Kas Awal", *["-"] * len(years)],
                                 ["Saldo Kas Akhir (tie-out ke Neraca)", *cash]],
                     "source": SRC},
        "ratios": {"title": "Rasio Keuangan & Efisiensi (FY20A–FY25A aktual)",
                   "headers": ["Rasio Kunci", *ylabels],
                   "rows": [
                       ["GROWTH (% yoy)", *[""] * len(years)],
                       ["Sales Growth", *growth(rev)],
                       ["EBITDA Growth", *growth(ebitda)],
                       ["Net Profit Growth", *growth(earn)],
                       ["PROFITABILITY (%)", *[""] * len(years)],
                       ["Gross Margin", *gm], ["EBITDA Margin", *emgn], ["Net Margin", *npm],
                       ["Return on Assets (ROA)", *roa], ["Return on Equity (ROE)", *roe],
                       ["LEVERAGE & COVERAGE (x)", *[""] * len(years)],
                       ["D/E", *der], ["Interest Coverage", *icr]],
                   "source": "Sectors historical_financial_ratio (dihitung analis)"},
    }
    filled.append("financials[IS/BS/CF]+financial_statements")

    # ================= risks (6 buckets, news/filings-sourced) ==============
    payload["risks"] = [
        {"bucket": "Distribusi insider",
         "detail": ("Pesona Sukses Cemerlang jual 646.464.646 sh @Rp 4.950 (12 Mei 2026, 6,162%→5,27%) dan "
                    "283.535.354 sh @Rp 3.150 (26 Mei 2026, 5,27%→4,88%); Alexander Ramlie jual 67,6 jt sh "
                    "@Rp 6.200 (31 Des 2025) setelah 45 jt @Rp 6.900 (3 Okt 2025)."),
         "source": "Sectors filings (IDX PDF keterbukaan)"},
        {"bucket": "Konsentrasi komoditas",
         "detail": ("100% pendapatan = tembaga+emas (FY2024: emas 55,0%, tembaga 45,0%); reli tembaga "
                    "US$ 14.708/ton (8 Sep 2026) mengangkat saham +5,9% - arah sebaliknya berlaku simetris."),
         "source": "Sectors segments FY2024 + bloombergtechnoz 9 Sep 2026"},
        {"bucket": "Leverage",
         "detail": (f"Utang bruto Rp {f2(float(q0.get('total_debt') or 0) / 1e12)} tn vs kas Rp "
                    f"{f2(float(q0.get('cash_only') or 0) / 1e12)} tn (Q1-2026); net-debt/EBITDA TTM "
                    f"{f1(ttm_netd_ebitda)}×; EBITDA/bunga TTM {f1(ttm_ebitda_int)}×; D/E FY2025 1,55×."),
         "source": "Sectors quarterly 8Q + annual FY2025"},
        {"bucket": "Arus kas bebas negatif (smelter build)",
         "detail": (f"FCF TTM −Rp {f2(abs(ttm.get('free_cash_flow', 0)) / 1e12)} tn (capex TTM Rp "
                    f"{f2(ttm.get('capital_expenditure', 0) / 1e12)} tn); Q1-2026 capex turun ke Rp 1,60 tn, "
                    f"FCF +Rp 1,69 tn - pemulihan bergantung pada akhir belanja smelter."),
         "source": "Sectors quarterly 8Q (TTM ke 2026-03-31)"},
        {"bucket": "Risiko aliran dana event indeks",
         "detail": ("Rebalancing VanEck GDX/GDXJ 12 Sep 2026 menekan saham emas (−1,02% AMMN 10 Sep 2026); "
                    "AMMN bertahan di GDX. Suspensi IDX: nihil (Sectors /suspensions total_count 0) - "
                    "dinyatakan eksplisit, bukan klaim suspensi."),
         "source": "idnfinancials 10 Sep 2026 + investor.id 31 Agu 2026 + Sectors suspensions"},
        {"bucket": "Valuasi premium vs sektor",
         "detail": (f"EV/EBITDA (TTM print 2026) {_idn(ttm_ev_eb, 2)}× (dari {_idn(hist_mults.get('FY2025'), 2)}× di 2025); PE 38,23× vs rerata peer sektor 10,07×; "
                    "forward PE + proyeksi analis numerik tidak dipublikasikan di feed."),
         "stat": f"{_idn(ttm_ev_eb, 2)}×", "stat_label": "EV/EBITDA (TTM print 2026)",
         "source": "Sectors valuation.historical_valuation"},
    ]
    payload["risks_note"] = ("Bucket 1/5 dari filings+news (source=asumsi ditandai di mana bukan); "
                             "suspensi nihil ber-evidence.")
    filled.append("risks[6 buckets]")

    # ================= peers (9 komparabel + Median/Average) =================
    peer_src = "Sectors peers FY2025 (9 komparabel; EV/EBITDA peer tak tersedia - GAP G8)"
    try:
        comps = (rep.get("peers") or [])[0].get("peers_data", {}).get("companies", [])
    except Exception:
        comps = []
    prows, pe_l, pb_l = [], [], []
    for c in comps:
        try:
            if (c.get("symbol") or "") == "AMMN.JK":
                continue
            pe = round(float(c.get("pe_ttm")), 2)
            pb = round(float(c.get("pb_mrq")), 2)
            pe_l.append(pe)
            pb_l.append(pb)
            prows.append([(c.get("symbol") or "").replace(".JK", ""),
                          f"{_nf.idn(float(c.get('market_cap') or 0) / 1e12, digits=2)} tn",
                          pe, "-", pb, "-", "-"])
        except Exception:
            continue
    if prows:
        spe, spb = sorted(pe_l), sorted(pb_l)
        n = len(spe)
        med = lambda s: round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 2)
        avg = lambda s: round(sum(s) / n, 2)
        payload["peers"] = {
            "tables": [{
                "pillar": "Basic Materials - Logam & Mineral (FY2025)",
                "headers": ["Ticker", "Market Cap", "P/E (x)", "EV/EBITDA", "P/BV (x)", "ROE (%)", "Gearing"],
                "rows": prows,
                "median": ["Median", "-", med(spe), "-", med(spb), "-", "-"],
                "average": ["Average", "-", avg(spe), "-", avg(spb), "-", "-"],
                "source": peer_src,
            }],
            "source": peer_src,
            "note": ("AMMN sendiri 38,62×/3,82× (Rp 356,06 tn) di luar baris median/rerata (modeler rule); "
                     "rerata PE terdistorsi MDKA 9.141,67× & EMAS negatif - median yang bermakna."),
        }
        filled.append("peers[9+Median/Average]")

    # ================= news (8 picks, url+date) =============================
    newsdoc = _load("news_AMMN_30d") or {}
    nby_ts = {r.get("timestamp"): r for r in (newsdoc.get("results") or []) if isinstance(r, dict)}
    news = []
    for ts in NEWS_PICKS:
        r = nby_ts.get(ts)
        if not r:
            continue
        try:
            outlet = urlsplit(r.get("source") or "").netloc.replace("www.", "")
            news.append({"title": r.get("title"), "url": r.get("source"),
                         "date": str(ts)[:10], "source": outlet})
        except Exception:
            continue
    if news:
        payload["news"] = news
        filled.append(f"news[{len(news)} url+date]")

    # ================= sentiment (flows; no synthetic gauge) ================
    ff = _load("foreign_flow_AMMN_90d") or {}
    frows = ff.get("data") or []
    try:
        net90 = sum(float(r.get("net_foreign_inflow") or 0) for r in frows)
        net30 = sum(float(r.get("net_foreign_inflow") or 0) for r in frows
                    if str(r.get("date") or "") >= "2026-08-13")
        pos = sum(1 for r in frows if float(r.get("net_foreign_inflow") or 0) > 0)
        brk = _load("broker_top_AMMN_30d") or {}
        buyers = [(b.get("broker_code"), round(float(b.get("net_idr") or 0) / 1e9, 1))
                  for b in (brk.get("top_buyers") or [])[:5]]
        sellers = [(s.get("broker_code"), round(float(s.get("net_idr") or 0) / 1e9, 1))
                   for s in (brk.get("top_sellers") or [])[:5] or (brk.get("top_seller") or [])[:5]]
        payload["sentiment"] = {
            "net_foreign_90d_bn": round(net90 / 1e9, 2),
            "net_foreign_30d_bn": round(net30 / 1e9, 2),
            "pos_days": f"{pos}/{len(frows)}",
            "top_buyers": buyers,
            "top_sellers": sellers,
            "source": "Sectors foreign-flow 90d + broker-summary 30d (tanpa gauge sintetik)",
        }
        filled.append("sentiment[flows]")
    except Exception:
        pass

    # ================= catalysts (quantified, basis stated) =================
    payload["catalysts"] = [
        {"name": "Cluster-buy direksi Jul-2026",
         "effect": "sinyal keyakinan insider",
         "quantified": {"shares": "+12.961.700", "avg_price": "Rp 3.548", "by": "Jul-2026 (8 transaksi)"},
         "source": "IDX keterbukaan via Sectors filings"},
        {"name": "Reli harga tembaga global",
         "effect": "pendorong harga saham + arus broker",
         "quantified": {"copper": "US$ 14.708/ton (rekor, 8 Sep 2026)",
                        "broker": "UBS Rp 92,9 md + Mandiri Rp 46,6 md (8 Sep)"},
         "source": "bloombergtechnoz 9 Sep 2026"},
        {"name": "Rebalancing GDX/GDXJ 12 Sep 2026",
         "effect": "aliran dana asing pasif (dua arah)",
         "quantified": {"note": "kualitatif - AMMN bertahan di GDX; EMAS berpotensi naik ke GDX"},
         "source": "idnfinancials 10 Sep 2026 + investor.id 31 Agu 2026"},
        {"name": "Smelter tembaga selesai (PAC 18 Jul 2026)",
         "effect": "capex run-rate turun; FCF Q1-2026 positif",
         "quantified": {"capex_q1": "Rp 1,60 tn (vs 5,26 tn Q4-2025)", "fcf_q1": "+Rp 1,69 tn"},
         "source": "AMMAN press release 24 Jul 2026 (via AMMN.json fcf_basis)"},
    ]
    payload["catalysts_note"] = ("Basis kuantifikasi dinyatakan per katalis; yang kualitatif "
                                 "dilabeli eksplisit (tanpa tenant-karangan).")
    filled.append("catalysts[4 quantified]")

    # ================= slide 2 source blocks (full Sectors cache) ============
    # Deck page 2 (server/report/industry_page.py) reads these; the blocks stay absent when the
    # endpoint returned nothing, so the page degrades to an explicit missing-data line.
    _slide2_sector_blocks(payload, filled)

    # ================= exhibits + chart combos ==============================
    rev_tn = [round(float(v) / 1000, 2) if isinstance(v, (int, float)) else 0.0 for v in rev]
    earn_tn = [round(float(v) / 1000, 2) if isinstance(v, (int, float)) else 0.0 for v in earn]
    payload["exhibits"] = [
        {"title": f"Pendapatan & Laba Bersih ({ylabels[0]}–{ylabels[-1]})",
         "chart": {"type": "bar",
                   "data": {"labels": ylabels,
                            "datasets": [{"label": "Pendapatan (Rp tn)", "data": rev_tn},
                                         {"label": "Laba bersih (Rp tn)", "data": earn_tn}]}},
         "source": "Sectors annual"},
        {"title": "Harga AMMN vs IHSG (90 hari, 62 sesi)",
         "chart": ({"type": "line",
                    "data": {"labels": labels,
                             "datasets": [{"label": "AMMN", "data": s_ammn},
                                          {"label": "IHSG", "data": s_ihsg}]},
                    # the tools mark a reference level with a dashed line; here it is the last close, taken
                    # from the series itself so it can never disagree with the plotted data
                    "refLine": {"value": s_ammn[-1],
                                "label": "Terakhir " + _nf.idn(s_ammn[-1], 0)}}
                   if labels and s_ammn and isinstance(s_ammn[-1], (int, float)) else None),
         "source": "Sectors daily + index-daily"},
    ]
    filled.append("exhibits[2]")

    def _numline(vals: list) -> list:
        return [round(float(v), 1) if isinstance(v, (int, float)) else 0.0 for v in vals]

    payload["revenue_combo"] = {
        "title": f"Revenue & Revenue Growth ({ylabels[0]}–{ylabels[-1]} aktual)",
        "years": ylabels, "bars": _numline(rev),
        "line": [0.0, *[_yoy(c, p) if isinstance(c, (int, float)) and isinstance(p, (int, float)) else 0.0
                        for c, p in zip(rev[1:], rev[:-1])]],
        "actual_periods": len(ylabels), "source": SRC}
    payload["ebitda_combo"] = {
        "title": f"EBITDA & EBITDA Margin ({ylabels[0]}–{ylabels[-1]} aktual)",
        "years": ylabels, "bars": _numline(ebitda), "line": _numline(emgn),
        "actual_periods": len(ylabels), "source": SRC}
    payload["netprofit_combo"] = {
        "title": f"Net Profit & Net Margin ({ylabels[0]}–{ylabels[-1]} aktual)",
        "years": ylabels, "bars": _numline(earn), "line": _numline(npm),
        "actual_periods": len(ylabels), "source": SRC}
    filled.append("chart_combos[rev/ebitda/netprofit]")

    # ============ valuation.midcycle + dcf_deep_dive.wacc_build =============
    try:
        consts = assum.get("ebitda_midcycle_constituents") or {}
        cvals = [float(v) for v in consts.values()]
        mult = float(assum.get("ev_multiple"))
        mid_avg = sum(cvals) / len(cvals)
        impl_ev = mid_avg * mult
        impl_eq = impl_ev - float(assum.get("net_debt")) + float(assum.get("cash"))
        impl_ps = impl_eq / float(assum.get("shares_out"))

        # The gate-primary leg multiplies the target multiple by the FORWARD level from the cited path -
        # a forward multiple on a historic average would double count the ramp. The own-history multiple is
        # carried below as the reason it is not used.
        _fp = __import__("server.report.forecast_path", fromlist=["resolve_forecast_path"])
        _path = _fp.resolve_forecast_path(str(assum.get("ticker") or "AMMN"), assum=assum)
        _drv = (_path.get("drivers") or {}).get("ebitda") or {}
        fwd_ebitda_bn = (float(_drv.get("rp_bn", [mid_avg / 1e9])[0])
                         if _drv.get("rp_bn") else mid_avg / 1e9)
        fwd_ev_bn = fwd_ebitda_bn * mult
        fwd_eq_bn = (fwd_ev_bn - float(assum.get("net_debt") or 0.0) / 1e9
                     + float(assum.get("cash") or 0.0) / 1e9)
        fwd_ps = fwd_eq_bn * 1e9 / float(assum.get("shares_out"))
        _own = assum.get("ev_multiple_own_history") or {}
        own_trailing = float(_own.get("trailing_mean") or 0.0)
        own_norm = float(_own.get("normalised_mean") or 0.0)
        own_mult_ps = ((own_trailing * fwd_ebitda_bn - float(assum.get("net_debt") or 0.0) / 1e9
                        + float(assum.get("cash") or 0.0) / 1e9) * 1e9
                       / float(assum.get("shares_out"))) if own_trailing else 0.0
        payload.setdefault("valuation", {})["midcycle"] = {
            "title": "EV/EBITDA - Forward Multiple pada Level Jalur (dengan cross-check historis)",
            "source": ("EBITDA FY26F dari jalur proyeksi yang dikutip (data/drivers/AMMN.json) + "
                       "AMMN.json ev_multiple (asumsi eksplisit); cross-check historis dari Sectors"),
            "headers": ["Komponen", "Nilai", "Keterangan"],
            "rows": [
                ["EBITDA FY26F (basis TP)", f"Rp {_nf.idn(fwd_ebitda_bn / 1e3, digits=2)} tn",
                 "Jalur proyeksi yang dikutip - level forward"],
                ["Target EV/EBITDA (basis TP)", f"{_nf.dec(mult, digits=2)}×",
                 "Multiple forward: pasar 13,3× FY26F + ramp belum tercetak; cross-check pihak ketiga 15,7×"],
                ["Implied EV", f"Rp {_nf.idn(fwd_ev_bn / 1e3, digits=2)} tn", "EBITDA FY26F × multiple target"],
                ["(−) Total utang bruto", f"Rp {_nf.idn(float(assum['net_debt']) / 1e12, digits=2)} tn",
                 "Q1-2026 (leg bruto bridge)"],
                ["(+) Kas", f"Rp {_nf.idn(float(assum['cash']) / 1e12, digits=2)} tn", "Q1-2026"],
                ["Implied equity", f"Rp {_nf.idn(fwd_eq_bn / 1e3, digits=2)} tn", "EV − utang + kas"],
                ["Implied per saham (TP headline)", f"Rp {_nf.idn(fwd_ps, digits=0)}",
                 "Leg gate-primary, dipakai sebagai TP"],
                ["- cross-check historis (tidak dipakai) -", "", ""],
                *[(f"EBITDA {k} (constituent)", f"Rp {_nf.idn(v / 1e12, digits=2)} tn", "Sectors annual")
                  for k, v in sorted(consts.items())],
                ["Rata-rata EBITDA 3Y historis", f"Rp {_nf.idn(mid_avg / 1e12, digits=2)} tn",
                 "Mean 3 constituents - hanya pembanding"],
                ["Own-history multiple (trailing / normalised)", f"{_nf.dec(own_trailing, digits=2)}× / {_nf.dec(own_norm, digits=2)}×",
                 "Tidak dipakai: EV stabil Rp 506-672 tn saat EBITDA naik-turun 2×, jadi multiple ini "
                 "menghukum level yang sudah pulih"],
                ["Own-history multiple pada level FY26F (double-count)",
                 f"Rp {_nf.idn(own_mult_ps, digits=0)}",
                 "2,7-4,2× harga pasar - di luar batas, karena itu ditolak sebagai basis"],
            ],
        }
        filled.append("valuation.midcycle")
    except Exception:
        pass
    wacc_rows: list = []
    try:
        rf, beta, erp = float(assum["rf"]), float(assum["beta"]), float(assum["erp"])
        cod = float(assum["cod"])
        taxr = float(assum.get("tax", 0.22))
        we, wd = float(assum["we"]), float(assum["wd"])
        # CoE MUST be recomputed from Rf + Beta x ERP every time. Reading it
        # from the file is dangerous: a stale value computed against an old
        # ERP drifts from the locked ERP. cost_of_equity in the assumptions
        # file is ignored if present.
        coe = rf + beta * erp
        wacc = float(assum.get("wacc") or wacc_val)
        kd_at = cod * (1 - taxr)
        pc = lambda v: f"{_nf.dec(v * 100, digits=2)}%".replace(".", ",")
        wacc_rows = [
            ["Risk-Free Rate (Rf)", pc(rf), "SBN 10Y (AsianBondsOnline 4 Sep 2026)"],
            ["Equity Risk Premium (ERP)", pc(erp), "Damodaran Indonesia (5 Jan 2026)"],
            ["Beta relevered (sektor Metals & Mining)", f"{_nf.dec(beta, digits=3)}".replace(".", ","),
             "Damodaran Betas Global → D/E pasar 31,43%"],
            ["Biaya Ekuitas (CoE)", pc(coe), "CoE = Rf + Beta × ERP"],
            ["Biaya Utang Sebelum Pajak (Kd)", pc(cod), "Beban bunga TTM / utang Q1-2026"],
            ["Tarif Pajak", pc(taxr), "UU HPP"],
            ["Biaya Utang Setelah Pajak", pc(kd_at), "Kd × (1 − Tax)"],
            ["Bobot Ekuitas / Utang", f"{pc(we)} / {pc(wd)}",
             "Spot: mcap 11 Sep 2026 vs utang Q1-2026"],
            ["WACC Final Diterapkan", pc(wacc), "We×CoE + Wd×Kd_aftertax"],
        ]
        payload["dcf_deep_dive"] = {
            "section_sub": ("Menjawab: Bagaimana kalkulasi biaya modal (WACC), sensitivitas "
                            "WACC × g, skenario EBITDA, dan jembatan EV → ekuitas AMMN?"),
            "intro": ("Cost of Capital Build, Sensitivitas 5×5, Skenario dan Jembatan EV→Ekuitas "
                      "dihitung ulang oleh mesin deterministik (scripts/dcf_engine) dari "
                      "data/assumptions/AMMN.json + hasil harvest Sectors - tanpa angka fallback."),
            "wacc_build": {
                "headers": ["Komponen WACC", "Nilai", "Metodologi / Sumber"],
                "rows": wacc_rows,
            },
        }
        filled.append("dcf_deep_dive.wacc_build")
    except Exception:
        wacc_rows = []

    # ==== dcf_deep_dive: sensitivity 5x5 / scenarios / bridge (LIVE engine) ===
    # Every number below is output of scripts/dcf_engine.dcf()/ev_ebitda() - the
    # same year-end Gordon math the live /api/report engine uses - recomputed
    # from data/assumptions/AMMN.json + the Sectors harvest. No baked fallback
    # table can fire while these keys exist (they are always set when the
    # harvested fcf series is present).
    try:
        from scripts.dcf_engine import dcf as _eng_dcf, ev_ebitda as _eng_ev
    except Exception:  # pragma: no cover - import guard
        _eng_dcf = _eng_ev = None
    try:
        if _eng_dcf is None or _eng_ev is None or not wacc_rows:
            raise RuntimeError("engine or WACC rows unavailable")
        fcf_bn = [float(x) for x in (assum.get("fcf") or [])]
        if not fcf_bn:
            raise RuntimeError("no harvested fcf series")
        fcf_idr = [x * 1e9 for x in fcf_bn]          # fcf[] is IDR bn (AMMN.json)
        shares = float(assum["shares_out"])
        cash_idr = float(assum["cash"])
        debt_idr = float(assum["net_debt"])          # GROSS debt bridge leg (net_debt_semantics)
        g_base = float(assum["g"])
        mult = float(assum["ev_multiple"])
        wacc_applied = (float(wacc_val)
                        if isinstance(wacc_val, (int, float)) and wacc_val
                        else float(assum["wacc"]))
        price = float(last_price or assum.get("last_price") or 0)

        base = _eng_dcf(fcf_idr, wacc_applied, g_base, shares_out=shares,
                        cash=cash_idr, net_debt=debt_idr)
        pv_exp = float(sum(base["pv_fcfs"]))
        pv_tv = float(base["terminal_pv"])
        ev_idr = float(base["firm_value"])
        eq_idr = float(base["equity_value"])
        fv_dcf = float(base["fv_per_share"])

        def _n(x: Any, digits: int = 0) -> str:
            """Indonesian formatting: '.' thousands, ',' decimals - dash if unparseable."""
            try:
                s = f"{float(x):,.{digits}f}"
            except Exception:
                return "-"
            if digits:
                return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
            return s.replace(",", ".")

        def _p2(x: Any, digits: int = 2) -> str:
            try:
                return f"{float(x) * 100:.{digits}f}".replace(".", ",") + "%"
            except Exception:
                return "-"

        def _up(x: Any) -> str:
            try:
                return ("+" if float(x) > 0 else "") + f"{_nf.dec(float(x), digits=1)}".replace(".", ",") + "%"
            except Exception:
                return "-"

        def _rating_id(up_pct: Any) -> str:
            """Report rating bands (mirrors server/routers/pdf.py:214-225)."""
            if up_pct is None:
                return "HOLD"
            if up_pct >= 15:
                return "BUY"
            if up_pct >= 5:
                return "TRADING BUY"
            if up_pct <= -15:
                return "SELL"
            if up_pct <= -5:
                return "TRADING SELL"
            return "HOLD"

        # --- Sensitivity: WACC base ±1% (2×0,5pp) × g base ±0,5pp (2×0,25pp)
        wacc_axis = [round(wacc_applied + i * 0.005, 6) for i in (-2, -1, 0, 1, 2)]
        g_axis = [round(g_base + j * 0.0025, 6) for j in (-2, -1, 0, 1, 2)]
        matrix: list = []
        up_matrix: list = []
        for w in wacc_axis:
            row_fv: list = []
            row_up: list = []
            for g in g_axis:
                try:
                    r = _eng_dcf(fcf_idr, w, g, shares_out=shares,
                                 cash=cash_idr, net_debt=debt_idr)
                    f = round(float(r["fv_per_share"]), 2)
                    row_fv.append(f)
                    row_up.append(round((f / price - 1.0) * 100, 1) if price else None)
                except Exception:
                    row_fv.append(None)
                    row_up.append(None)
            matrix.append(row_fv)
            up_matrix.append(row_up)

        sens_headers = ["WACC \\ g", *[_p2(g) + (" (Base)" if j == 2 else "")
                                       for j, g in enumerate(g_axis)]]
        sens_rows = []
        for i in range(len(wacc_axis)):
            cells = [_p2(wacc_axis[i]) + (" (Base)" if i == 2 else "")]
            for j in range(len(g_axis)):
                f = matrix[i][j]
                if f is None:
                    cells.append("-")
                elif up_matrix[i][j] is None:
                    cells.append((f"−Rp {_n(abs(f))}" if f < 0 else f"Rp {_n(f)}"))
                else:
                    cells.append((f"−Rp {_n(abs(f))}" if f < 0 else f"Rp {_n(f)}")
                                 + f" ({_up(up_matrix[i][j])})")
            sens_rows.append(cells)
        valid = [x for row in matrix for x in row if x is not None]

        # --- Scenarios: harvested EBITDA band × AMMN.json mid-cycle multiple.
        # Leg = EV/EBITDA, AMMN's gate-primary (AMMN.json gate_primary;
        # dcf_role: "DCF comparison-only / punitive by construction"), so the
        # base row ties to the published mid-cycle cross-check.
        cons_bn = {str(k): float(v) / 1e9
                   for k, v in (assum.get("ebitda_midcycle_constituents") or {}).items()}
        mid_bn = (sum(cons_bn.values()) / len(cons_bn)) if cons_bn else None
        try:
            q_eb_bn = float(q0.get("ebitda")) / 1e9
        except Exception:
            q_eb_bn = None
        scen_rows: list = []
        scen_out: dict = {}
        specs: list = []
        if cons_bn:
            weak = min(cons_bn, key=lambda k: cons_bn[k])
            specs.append(("BEAR", cons_bn[weak],
                          f"EBITDA {weak} Rp {_n(cons_bn[weak])} tn (terlemah)",
                          f"EBITDA {weak} Rp {_n(cons_bn[weak], 2)} tn - konstituen siklus "
                          "terlemah (Sectors annual, AMMN.json ebitda_midcycle_constituents)"))
        if mid_bn is not None:
            specs.append(("BASE", mid_bn,
                          f"EBITDA mid-cycle 3Y Rp {_n(mid_bn)} tn",
                          f"EBITDA mid-cycle (rata-rata 3 tahun) Rp {_n(mid_bn, 2)} tn - "
                          "konstituen FY2023/FY2024/FY2025 disitir (MID-EBITDA-PROVENANCE)"))
        if q_eb_bn and q_eb_bn > 0:
            specs.append(("BULL", q_eb_bn * 4.0,
                          f"EBITDA Q1-2026 x4 Rp {_n(q_eb_bn * 4.0)} tn (run-rate)",
                          f"run-rate EBITDA Q1-2026 Rp {_n(q_eb_bn, 2)} tn x 4 kuartal = "
                          f"Rp {_n(q_eb_bn * 4.0, 2)} tn (Sectors quarterly 8Q to 2026-03-31)"))
        mult_id = f"{_nf.dec(mult, digits=2)}".replace(".", ",")
        for name, eb_bn, short_basis, full_basis in specs:
            r = _eng_ev(eb_bn * 1e9, mult, net_debt=debt_idr,
                        shares_out=shares, cash=cash_idr)
            fv = float(r["fv_per_share"])
            up_pct = round((fv / price - 1.0) * 100, 1) if price else None
            rate = _rating_id(up_pct)
            scen_rows.append([
                f"{name} - {short_basis}",
                f"Rp {_n(fv)}",
                f"{rate} ({_up(up_pct)})" if up_pct is not None else rate,
            ])
            scen_out[name] = {
                "scenario": name,
                "basis": full_basis,
                "ebitda_idr": eb_bn * 1e9,
                "multiple": mult,
                "fair_value_per_share": fv,
                "upside": (round(up_pct / 100.0, 6) if up_pct is not None else None),
                "rating": rate,
                "leg": "EV/EBITDA",
            }

        # --- EV → equity bridge (real gross debt / cash, Q1-2026) -------------
        bridge_rows = [
            ["PV Explicit + PV Terminal", _n(ev_idr / 1e9),
             f"Enterprise Value = PV FCFF {_n(pv_exp / 1e9)} + PV TV {_n(pv_tv / 1e9)}"],
            ["(+) Kas & Setara Kas", "+" + _n(cash_idr / 1e9),
             "Q1-2026 cash_only (Sectors 2026-03-31)"],
            ["(−) Total Utang Berbunga", "−" + _n(debt_idr / 1e9),
             "Utang bruto Q1-2026, bukan nol (net_debt_semantics)"],
            ["Implied Equity Value", _n(eq_idr / 1e9),
             f"Rp {_n(fv_dcf)}/saham = FV engine DCF (WACC {_p2(wacc_applied)}, g {_p2(g_base)})"],
        ]

        ddd = payload.setdefault("dcf_deep_dive", {})
        ddd["sensitivity"] = {
            "title": ("Sensitivity Analysis - FV DCF 5×5 (WACC %s ±1%% × g %s ±0,5pp)"
                      % (_p2(wacc_applied), _p2(g_base))),
            "headers": sens_headers,
            "rows": sens_rows,
            "note": ("Sel dihitung ulang per kombinasi oleh dcf() (25 FV live); tidak ada FV "
                     "fallback. Basis = mid-cycle FCFF flat Rp "
                     f"{_n(float(fcf_bn[0]), 1)} bn/thn (AMMN.json fcf_basis)."),
        }
        ddd["scenarios"] = {
            "headers": ["Scenario - basis EBITDA", f"Nilai Wajar (EV/EBITDA {mult_id}×)",
                        "Investment Recommendation"],
            "rows": scen_rows,
            "note": ("Band EBITDA dari hasil harvest (annual Sectors + run-rate kuartalan) × "
                     f"multiple mid-cycle {mult_id}× (AMMN.json ev_multiple, asumsi eksplisit ±2×). "
                     f"Kaki DCF (Rp {_n(fv_dcf)}) bersifat pembanding saja "
                     "(gate_primary = EV/EBITDA)."),
        }
        ddd["bridge"] = {
            "headers": ["Komponen Jembatan", "Nilai (Rp bn)", "Keterangan"],
            "rows": bridge_rows,
        }
        filled.append("dcf_deep_dive.sensitivity[5x5]+scenarios[3]+bridge[4]")

        # --- Exhibit-8 card (page 4) + FCFF table on the DCF method ----------
        payload.setdefault("valuation", {})["dcf_grid"] = {
            "pv_explicit": _n(pv_exp / 1e9),
            "pv_tv": _n(pv_tv / 1e9),
            "ev": _n(ev_idr / 1e9),
            "net_cash": ("−" if (cash_idr - debt_idr) < 0 else "")
                        + _n(abs(cash_idr - debt_idr) / 1e9),
            "unit": "Rp bn",
            "source": "scripts/dcf_engine.dcf - PV FCFF + PV TV ± kas − utang bruto (Rp bn, IDR)",
        }
        for m in (payload.get("valuation", {}).get("methods") or []):
            if m.get("method") == "DCF":
                m["table"] = {
                    "headers": ["Komponen DCF (Rp bn)",
                                *[f"FY{2026 + i}F" for i in range(len(fcf_bn))]],
                    "rows": [
                        ["Free Cash Flow (FCFF)", *[_n(x, 1) for x in fcf_bn]],
                        ["Discount Factor",
                         *[f"{_nf.dec(d, digits=3)}".replace(".", ",") for d in base["discount_factors"]]],
                        ["Present Value FCFF", *[_n(p / 1e9, 1) for p in base["pv_fcfs"]]],
                    ],
                }
                break
        filled.append("valuation.dcf_grid + methods[DCF].table(FCFF/DF/PV)")

        # --- cDcf: friend-style block consumed by BOTH renderers -------------
        # HTML: templates/report_single.html valuation block (svg macros).
        payload["cDcf"] = {
            "wacc_table": [{"label": r[0], "value": r[1]} for r in wacc_rows],
            "sensitivity": {
                "fair_value": matrix,
                "upside": up_matrix,
                "wacc_axis": wacc_axis,
                "g_axis": g_axis,
                "stats": {
                    "base": round(fv_dcf, 2),
                    "min": round(min(valid), 2) if valid else None,
                    "max": round(max(valid), 2) if valid else None,
                    "n_valid": len(valid),
                    "n_cells": len(wacc_axis) * len(g_axis),
                },
            },
            "scenarios": scen_out,
            "valuation": {
                "pv_explicit": pv_exp,
                "pv_terminal": pv_tv,
                "enterprise_value": ev_idr,
                "cash": cash_idr,
                "total_debt": debt_idr,
                "minority": 0.0,
                "equity_value": eq_idr,
                "fair_value_per_share": fv_dcf,
                "market_price": price,
                "upside": (round(fv_dcf / price - 1.0, 6) if price else None),
                "wacc": wacc_applied,
                "g": g_base,
                "shares_outstanding": shares,
            },
            "recommendation": {
                "rating": rating,
                "upside": (round(float(upside) / 100.0, 6)
                           if isinstance(upside, (int, float)) else None),
                "label": ("Undervalued" if (isinstance(upside, (int, float)) and upside > 0)
                          else "Overvalued"),
                "note": (f"FV DCF Rp {_n(fv_dcf)} vs harga Rp {_n(price)} "
                         f"(WACC {_p2(wacc_applied)}, g {_p2(g_base)}); rating {rating}."),
            },
            "provenance": ("scripts/dcf_engine.dcf/ev_ebitda on data/assumptions/AMMN.json "
                           "+ Sectors harvest - 0 kredit, deterministik."),
        }
        filled.append("cDcf(wacc_table/sensitivity/scenarios/valuation)")
    except Exception:
        pass

    payload["fill_meta"] = {
        "filled": filled,
        "gaps": GAPS,
        "src": "output/cache/ammn_fill (sibling t_2c5f420e, 13 kredit; lane ini 0 kredit)",
    }
    return payload["fill_meta"]
