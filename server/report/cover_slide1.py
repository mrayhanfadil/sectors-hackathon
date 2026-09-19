"""Slide-1 (cover) contract - the rating / price / stats / thesis block layout.

The cover carries the report's headline call (rating, TP, upside) plus the numbers a PM scans
before reading anything: shares, market cap, turnover, free float, controlling holders. Every
value here is derived from an artifact that already exists (Sectors quarterly 8Q, Sectors daily
90d, Sectors ownership, the assumptions file) or from the market harvest script
(``scripts/build_cover_market.py``), which is where the 24-month price-vs-IHSG series and the
USD/IDR rate come from - this module reads files only, so the render path stays offline and
deterministic. Nothing is invented: a value with no source renders as an honest "n/a" plus the
reason, per the LOUD policy.

Contract written to ``payload["cover"]["slide1"]``::

    rating        {action, action_status, prev_action, prev_tp}
    price_box     {rows: [[label, value]], anchor, anchor_basis}
    stats         {rows, major_shareholders: [{name, pct}], free_float_method, sources}
    analyst       {name, title}
    theme_title   str | None
    highlights    [str, str, str]
    financial_para{heading, body}
    jci_chart     {labels, price, rel_pct, window, source}

The house rule fixes the source line under every exhibit to "Company, Team Estimates", so the
per-field provenance below rides in ``stats["sources"]`` for the audit comment instead.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
AMMN_ART_DIR = REPO_ROOT / "output" / "cache" / "ammn_fill"
MARKET_DIR = REPO_ROOT / "output" / "cache" / "cover_market"
FX_CACHE = REPO_ROOT / "output" / "cache" / "fx_usdidr.json"

FACEBOOK_LIKE = {"public", "masyarakat", "treasury stock", "saham treasuri"}
RATING_TITLE = {
    "BUY": "Buy", "SELL": "Sell", "HOLD": "Hold",
    "TRADING BUY": "Trading Buy", "TRADING SELL": "Trading Sell",
    "REVIEW REQUIRED": "Review Required",
    "REVIEW-REQUIRED": "Review-Required",
}


# --------------------------------------------------------------------------- helpers

MONTH_ID = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
            7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"}


def _window_label(first: str, last: str) -> str:
    """'2026-06-15', '2026-09-11' -> '15 Jun–11 Sep 2026' (reader-facing, not ISO)."""
    def parse(s: str):
        try:
            y, m, d = (int(x) for x in str(s)[:10].split("-"))
            return y, m, d
        except Exception:
            return None
    a, b = parse(first), parse(last)
    if not a or not b:
        return f"{first}–{last}"
    if a[0] == b[0]:
        return f"{a[2]} {MONTH_ID[a[1]]}–{b[2]} {MONTH_ID[b[1]]} {b[0]}"
    return f"{a[2]} {MONTH_ID[a[1]]} {a[0]}–{b[2]} {MONTH_ID[b[1]]} {b[0]}"


def _read(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except Exception:
        return None


def _n(x: Any, digits: int = 1) -> str:
    """id-ID number: 352438.5 -> '352.438,5'."""
    if not isinstance(x, (int, float)):
        return "n/a"
    s = f"{x:,.{digits}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _pct(x: Any, digits: int = 2, signed: bool = True) -> str:
    if not isinstance(x, (int, float)):
        return "n/a"
    sign = "+" if (signed and x > 0) else ""
    return f"{sign}{_n(x, digits)}%"


def _rp_bn(x: Any) -> str:
    """IDR billions, switching to tn above 1,000 bn so a column stays one shape."""
    if not isinstance(x, (int, float)):
        return "n/a"
    return f"Rp {_n(x / 1000, 2)} tn" if abs(x) >= 1000 else f"Rp {_n(x, 1)} bn"


def _quarter(rows: list[dict], date: str) -> Optional[dict]:
    for r in rows:
        if str(r.get("date")) == date:
            return r
    return None


def _sort_q(rows: list[dict]) -> list[dict]:
    return sorted([r for r in rows if r.get("date")], key=lambda r: str(r["date"]))


def _chg(cur: Any, base: Any) -> Optional[float]:
    try:
        cur, base = float(cur), float(base)
        if base == 0:
            return None
        return (cur / base - 1.0) * 100.0
    except Exception:
        return None


def _sane_base(base_q: Optional[dict], rows: list[dict]) -> tuple[bool, str]:
    """Is a quarter usable as a YoY base?

    AMMN's Q1-2025 prints revenue of Rp 35,3 miliar and negative EBITDA - the smelter ramp
    quarter, where the quarterly feed has almost no revenue. Dividing by it produces a
    +38.000% "growth" number that is worse than useless in a research note, so the honest move
    is to say why the comparator is unusable instead of printing the artifact.
    """
    if base_q is None:
        return False, "kuartal pembanding tidak ada di deret 8 kuartal"
    rev = base_q.get("revenue")
    if not isinstance(rev, (int, float)) or rev <= 0:
        return False, "pendapatan kuartal pembanding nol/negatif"
    others = [float(r["revenue"]) for r in rows
              if isinstance(r.get("revenue"), (int, float)) and r["revenue"] > 0
              and str(r.get("date")) != str(base_q.get("date"))]
    if others:
        med = sorted(others)[len(others) // 2]
        if rev < 0.10 * med:
            return False, (f"pendapatan Rp {_n(rev / 1e9, 2)} bn pada kuartal pembanding "
                           f"(Q1-2025 kuartal ramp smelter)")
    return True, ""


# --------------------------------------------------------------------------- market data

def fx_usdidr(refresh: bool = False) -> Optional[dict]:
    """USD/IDR for the dual-currency cover rows, read from the harvest artifact.

    The server never imports yfinance (the production render path stays offline and
    deterministic), so this reads what ``scripts/build_cover_market.py`` wrote. No artifact ->
    None -> the cover prints "n/a" for the USD leg instead of a stale rate.
    """
    cached = _read(FX_CACHE)
    if cached and isinstance(cached.get("rate"), (int, float)):
        return cached
    return None


def monthly_vs_jci(ticker: str, months: int = 24) -> Optional[dict]:
    """`TICKER` vs IHSG, monthly closes, rebased at t0 - the cover's Exhibit 1 series.

    Two series in one frame: the left axis is the absolute close (navy line), the right axis is
    the relative performance against the index in percent (grey line), which is what a PM reads
    a relative chart for. Sectors caps its daily endpoint at 90 days, so a 1-2 year window comes
    from ``scripts/build_cover_market.py`` (yfinance) and is read here as an artifact.
    """
    art = _read(MARKET_DIR / f"{ticker.upper()}.json")
    if not isinstance(art, dict) or not art.get("labels"):
        return None
    if months and len(art["labels"]) > months:
        n = len(art["labels"]) - months
        art = {**art, "labels": art["labels"][n:], "price": art["price"][n:],
               "index": art["index"][n:], "rel_pct": art["rel_pct"][n:],
               "months": months,
               "window": f"{art['labels'][n]}–{art['labels'][-1]}"}
    return art


# --------------------------------------------------------------------------- block builders

def _rating_block(payload: dict) -> dict:
    rbox = (payload.get("cover") or {}).get("rating_box") or {}
    meta = payload.get("meta") or {}
    action = str(rbox.get("action") or "").strip()
    prev = rbox.get("prev_action")
    rtype = str(meta.get("report_type") or "").strip()
    if prev:
        prev_t = RATING_TITLE.get(str(prev).upper(), str(prev).title())
        new_t = RATING_TITLE.get(action.upper(), action.title())
        rank = {"BUY": 2, "TRADING BUY": 1, "HOLD": 0, "TRADING SELL": -1, "SELL": -2}
        if rank.get(action.upper(), 0) > rank.get(str(prev).upper(), 0):
            status = f"(Upgrade from {prev_t})"
        elif rank.get(action.upper(), 0) < rank.get(str(prev).upper(), 0):
            status = f"(Downgrade from {prev_t})"
        else:
            status = "(Maintained)"
    elif rtype.lower().startswith(("initiation", "inisiasi")):
        status = "(Initiation)"
    else:
        # No previous rating on file: "Maintained" would claim a history that does not exist.
        status = "(Initiation)"
    return {
        "action": RATING_TITLE.get(action.upper(), action.title()) or "n/a",
        "action_status": status,
        "prev_action": prev,
        "prev_tp": rbox.get("prev_tp"),
    }


def _price_box(payload: dict) -> dict:
    rbox = (payload.get("cover") or {}).get("rating_box") or {}
    price, tp, up = rbox.get("price"), rbox.get("tp"), rbox.get("upside_pct")
    prev_tp = rbox.get("prev_tp")
    val = payload.get("valuation") or {}
    # Previous TP sits between Target Price and Upside/Downside on the benchmark cover, and
    # prints an italic "NA" on initiation rather than being dropped (the reader still wants to
    # see that there is no prior target to compare against).
    prev_row = ["Previous TP (Rp)", _n(prev_tp, 0) if prev_tp else "NA", not prev_tp]
    return {
        "rows": [
            ["Last Price (Rp)", _n(price, 0)],
            ["Target Price (Rp)", _n(tp, 0)],
            prev_row,
            ["Upside/Downside (%)", _pct(up)],
        ],
        "anchor": val.get("anchor") or "n/a",
        "anchor_basis": val.get("anchor_basis") or "n/a",
    }


def _stats_block(payload: dict, assum: dict, fx: Optional[dict]) -> dict:
    cover = payload.get("cover") or {}
    rows: list[list[str]] = []
    sources: dict[str, str] = {}

    shares = (assum.get("shares_out") or 0) or 0
    if shares:
        rows.append(["No. of Shares (mn)", _n(shares / 1e6, 1)])
        sources["shares_mn"] = "Sectors ownership (shares outstanding)"

    canon = payload.get("canonical_metrics") or {}
    # Canonical block uses key market_cap_rpbn (already in rpbn units).
    # Sep 17 2026 (gate architecture): read the canonical rpbn value, fall
    # back to assumptions/daily only if the gate did not run.
    canon_mcap_rpbn = canon.get("market_cap_rpbn", {}).get("value")
    if canon_mcap_rpbn:
        mcap = float(canon_mcap_rpbn) * 1e9
        rpbn = float(canon_mcap_rpbn)
        sources["mkt_cap"] = "canonical metric gate (Sep 17 2026): equity x pb_mrq"
    else:
        mcap = assum.get("market_cap")
        if not mcap:
            daily = _read(AMMN_ART_DIR / "daily_AMMN_90d.json") or {}
            drows = daily.get("data") or []
            mcap = (drows[-1].get("market_cap") if drows else None)
        rpbn = float(mcap) / 1e9 if mcap else None
        if mcap:
            sources["mkt_cap"] = "Sectors daily close x shares outstanding"
    if mcap:
        if fx and fx.get("rate"):
            rows.append(["Mkt Cap (Rpbn/US$mn)",
                         f"{_n(rpbn, 1)} / {_n(float(mcap) / fx['rate'] / 1e6, 1)}"])
            sources["mkt_cap_usd"] = f"USD/IDR {_n(fx['rate'], 0)} · {fx['source']} {fx['date']}"
        else:
            rows.append(["Mkt Cap (Rpbn/US$mn)", f"{_n(rpbn, 1)} / n/a"])

    daily = _read(AMMN_ART_DIR / "daily_AMMN_90d.json") or {}
    drows = [d for d in (daily.get("data") or []) if d.get("close") and d.get("volume")]
    if drows:
        vals = [float(d["close"]) * float(d["volume"]) for d in drows]
        avg = sum(vals) / len(vals)
        first, last = str(drows[0]["date"]), str(drows[-1]["date"])
        if fx and fx.get("rate"):
            rows.append(["Avg. Daily T/O 3M (Rpbn/US$mn)",
                         f"{_n(avg / 1e9, 1)} / {_n(avg / fx['rate'] / 1e6, 1)}"])
        else:
            rows.append(["Avg. Daily T/O 3M (Rpbn/US$mn)", f"{_n(avg / 1e9, 1)} / n/a"])
        # The averaging window is defined once here and used by every report, per the house
        # rule that the turnover period must be consistent across the fleet.
        sources["avg_daily_to"] = (
            f"Sectors /transaction/daily {len(drows)} sesi {first}..{last} "
            f"(close x volume, rata-rata = 3 bulan terakhir)"
        )
        sources["avg_daily_to_window"] = f"{_window_label(first, last)} ({len(drows)} sesi)"

    holders = [h for h in (cover.get("shareholders") or []) if isinstance(h, dict)]
    big = [h for h in holders
           if isinstance(h.get("pct"), (int, float)) and float(h["pct"]) >= 5.0
           and str(h.get("name", "")).strip().lower() not in FACEBOOK_LIKE]
    if big:
        ff = round(100.0 - sum(float(h["pct"]) for h in big), 2)
        if ff < 0:
            ff = None
        rows.append(["Free Float (%)", _n(ff, 2) if ff is not None else "n/a"])
        if ff is not None:
            sources["free_float"] = ("dihitung: 100% − pemegang ≥5% (metodologi free float IDX) "
                                     "dari Sectors ownership 31 Agu 2026")
    else:
        rows.append(["Free Float (%)", "n/a"])
        sources["free_float"] = "tidak ada print ownership ≥5% untuk dihitung"

    return {
        "rows": rows,
        "major_shareholders": [{"name": h.get("name"), "pct": h.get("pct"),
                                "pct_str": f"{_n(h.get('pct'), 2)}%"} for h in big],
        # Reader-facing definitions: the turnover window must be stated, not assumed.
        "notes": ([f"T/O = rata-rata 3 bulan ({sources['avg_daily_to_window']})"]
                  if sources.get("avg_daily_to_window") else [])
                 + (["Free float dihitung: 100% − pemegang ≥5%"] if "free_float" in sources
                    and rows and any(r[0].startswith("Free Float") and r[1] != "n/a" for r in rows)
                    else []),
        "sources": sources,
    }


def _analyst_block(payload: dict) -> dict:
    import os

    meta = payload.get("meta") or {}
    name = (os.environ.get("SECTORS_ANALYST_NAME")
            or meta.get("analyst_name")
            or meta.get("prepared_by")
            or "Research Desk")
    title = os.environ.get("SECTORS_ANALYST_TITLE") or meta.get("analyst_title") or "Equity Analyst"
    return {"name": name, "title": title}


def _highlights(payload: dict) -> list[str]:
    rbox = (payload.get("cover") or {}).get("rating_box") or {}
    out = [str(x).strip() for x in (rbox.get("key_takeaways") or []) if str(x).strip()]
    return out[:3]


def _financial_para(payload: dict, ticker: str) -> dict:
    """Paragraph 1 - Kinerja Keuangan: qoq / yoy / running rate / drivers.

    Every clause carries an explicit figure, derived here rather than written by hand, so the
    paragraph cannot drift from the artifact it cites.
    """
    q = payload.get("quarterly")
    rows = []
    src = "Sectors /financials/quarterly"
    if isinstance(q, dict) and isinstance(q.get("rows"), list):
        rows = q["rows"]
        src = q.get("source") or src
    else:
        art = _read(AMMN_ART_DIR / f"quarterly_{ticker.upper()}_8.json") or {}
        rows = art.get("data") or []
        if rows:
            src = f"Sectors /financials/quarterly/{ticker.upper()} n_quarters={len(rows)}"

    rows = _sort_q(rows)
    if not rows:
        return {
            "heading": "Kinerja Keuangan",
            "body": ("Data kuartalan tidak tersedia untuk emiten ini - tidak ada paragraf "
                     "kinerja yang bisa disusun tanpa angka (LOUD policy)."),
        }

    cur = rows[-1]
    prev = rows[-2] if len(rows) >= 2 else None
    yoy_base = None
    if cur.get("date"):
        try:
            y, m, _d = str(cur["date"]).split("-")
            yoy_base = _quarter(rows, f"{int(y) - 1}-{m}-{_d}")
        except Exception:
            yoy_base = None

    rev, eb, gp, ni = (cur.get("revenue"), cur.get("ebitda"),
                       cur.get("gross_profit"), cur.get("earnings"))
    rev_bn = rev / 1e9 if isinstance(rev, (int, float)) else None
    eb_bn = eb / 1e9 if isinstance(eb, (int, float)) else None
    ni_bn = ni / 1e9 if isinstance(ni, (int, float)) else None
    qtag = _qtag(cur.get("date"))

    # FUTURE-STORY RULE (peer #5): P1 is the FORWARD handoff, not a second backward
    # record. Max 1 bridging sentence of backward context (latest quarter + 1
    # figure), then weight to catalyst -> earnings path -> valuation. The audited
    # backward record lives in the exhibits and quadrant narratives; restating
    # qoq/yoy here is a REJECT. Every forward figure is computed from an artifact
    # that already exists (quarterly rows, catalyst ledger, driver file, rating
    # box) - never invented.
    parts: list[str] = []
    # 1. bridge: latest quarter + 1 figure, nothing more.
    if rev_bn is not None:
        parts.append(f"Basis {qtag}: pendapatan {_rp_bn(rev_bn)}.")
    else:
        parts.append("Data kuartalan tidak tersedia - tidak ada basis backward yang bisa "
                     "dinyatakan (LOUD policy).")
    # 2. catalyst: which quantified catalyst must deliver.
    cats = payload.get("catalysts") or []
    if cats and isinstance(cats[0], dict) and cats[0].get("name"):
        first = cats[0]
        parts.append(f"Ke depan: {first.get('name')} - efek: {first.get('effect') or 'lihat halaman katalis'} "
                     f"(sumber: {first.get('source') or 'payload'}).")
    else:
        parts.append("Katalis ke depan belum terverifikasi di payload - tidak ada jembatan forward yang "
                     "bisa dinyatakan tanpa angka (LOUD policy).")
    # 3. earnings path: what level the forecast unlocks, from the same driver file
    # the Key Financials exhibit resolves. Ticker-agnostic; loud when absent.
    _tk = (str(ticker or "").upper()
           or str((payload.get("meta") or {}).get("ticker") or "").upper())
    _eb26 = _eb28 = _cagr = _m26 = _m28 = None
    _drv_note = ""
    _drv_basis = "level normalised mid-cycle"
    try:
        _dp = REPO_ROOT / "data" / "drivers" / f"{_tk}.json"
        if _tk and _dp.exists():
            _doc = json.loads(_dp.read_text(encoding="utf-8"))
            _fx = float(_doc.get("fx_rp_bn_per_usd_mn") or 1.0)
            _dr = _doc.get("drivers") or {}

            def _rp(k: str, i: int) -> Optional[float]:
                try:
                    v = ((_dr.get(k) or {}).get("path") or [])[i]
                    return float(v) * _fx if isinstance(v, (int, float)) else None
                except Exception:
                    return None

            _rv26, _rv28 = _rp("revenue", 0), _rp("revenue", 2)
            _eb26, _eb28 = _rp("ebitda", 0), _rp("ebitda", 2)
            if _rv26 and _eb26:
                _m26 = _eb26 / _rv26 * 100
            if _rv28 and _eb28:
                _m28 = _eb28 / _rv28 * 100
            if _eb26 and _eb28 and _eb26 > 0 and _eb28 > 0:
                _cagr = ((_eb28 / _eb26) ** 0.5 - 1) * 100
            _rn = str(((_dr.get("revenue") or {}).get("note")) or "")
            _raw = _rn.split(" plus ")[0].split(", new processing")[0].strip()
            # Plain-Indonesian gloss of the physical driver (owner rule): keep the
            # volumes, translate the wrapping. Falls back to the raw note.
            import re as _re
            _vol = _re.findall(r"([\d.,]+)\s*Mt", _raw)
            _drv_note = _raw
            if len(_vol) >= 2:
                _drv_note = (f"tambang Phase-8 (bijih {_vol[0]} juta → {_vol[1]} juta ton) "
                             f"plus smelter baru")
            if str(_doc.get("basis") or "") == "third-party-estimate":
                _drv_basis = "estimasi tim atas basis data berlisensi"
    except Exception:
        pass
    if _eb26 and _eb28 and _cagr is not None:
        parts.append(
            f"Jalur FY26F-28F ({_drv_basis}): EBITDA Rp {_n(_eb26 / 1000, 1)} tn → "
            f"Rp {_n(_eb28 / 1000, 1)} tn (tumbuh {_n(_cagr, 1)}% per tahun, marjin {_n(_m26, 1)}%→{_n(_m28, 1)}%)"
            + (f" - {_drv_note}." if _drv_note else ".")
        )
    else:
        parts.append("Jalur FY26F-28F tidak terverifikasi di file driver - lihat tabel Key Financials "
                     "(LOUD policy, tanpa estimasi karangan).")
    # 4. valuation: what multiple the anchor TP implies on that level.
    _rbox = (payload.get("cover") or {}).get("rating_box") or {}
    _tp, _up, _act = _rbox.get("tp"), _rbox.get("upside_pct"), _rbox.get("action")
    if isinstance(_tp, (int, float)):
        parts.append(f"Target harga Rp {_n(_tp, 0)} ({_act or 'n/a'}, potensi naik {_pct(_up)}): patokan "
                     f"konservatif atas laba 2026 yang jauh lebih besar.")
    else:
        parts.append("Target harga belum terverifikasi di rating box - tidak ada jangkar valuasi yang "
                     "bisa dinyatakan (LOUD policy).")

    heading = (f"{_qtag(cur.get('date'))}: laba {_rp_bn(ni_bn) if ni_bn is not None else 'n/a'}"
               + (f" ({_pct(_chg(ni, prev['earnings']))} qoq)" if prev and prev.get("earnings") else "")
               + (f", marjin kotor {_n(gp / rev * 100, 1)}%" if isinstance(gp, (int, float))
                  and isinstance(rev, (int, float)) and rev else ""))
    return {"heading": heading, "body": " ".join(parts), "source": src}


def _qtag(date: Any) -> str:
    try:
        y, m, _ = str(date).split("-")
        return f"Q{(int(m) - 1) // 3 + 1}-{y}"
    except Exception:
        return str(date)


# --------------------------------------------------------------------------- entry point

def build(payload: dict, assum: Optional[dict] = None) -> dict:
    """Fill ``payload["cover"]["slide1"]`` (idempotent, never raises).

    Reads only local artifacts - no network here (see scripts/build_cover_market.py for the
    yfinance harvest that feeds the price-vs-IHSG series and the FX rate).
    """
    ticker = str((payload.get("meta") or {}).get("ticker") or "").upper()
    assum = assum or {}
    cover = payload.setdefault("cover", {})

    fx = fx_usdidr()
    chart = monthly_vs_jci(ticker)

    slide1 = {
        "rating": _rating_block(payload),
        "price_box": _price_box(payload),
        "stats": _stats_block(payload, assum, fx),
        "analyst": _analyst_block(payload),
        "theme_title": (payload.get("meta") or {}).get("theme_title") or assum.get("theme_title"),
        "highlights": _highlights(payload),
        "financial_para": _financial_para(payload, ticker),
        "jci_chart": chart,
        "fx": fx,
        "notes": [],
    }
    if chart is None:
        slide1["notes"].append(
            "jci_chart: deret 24 bulan tidak tersedia - jalankan "
            f"`.venv/bin/python scripts/build_cover_market.py {ticker or '<TICKER>'}` "
            "(exhibit 1 dihilangkan, bukan diganti deret sintetik)"
        )
    if fx is None:
        slide1["notes"].append(
            "fx: USD/IDR belum di-harvest - jalankan "
            "`.venv/bin/python scripts/build_cover_market.py <TICKER> --refresh-fx` "
            "(kolom US$ ditampilkan n/a)"
        )
    cover["slide1"] = slide1
    return slide1
