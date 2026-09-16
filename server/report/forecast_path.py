"""Forecast-path resolver - one place that decides where the deck's FY26F-FY28F numbers come from.

Every page that shows a forecast column (cover Key Financials, the performance quadrants, the valuation
legs, the statement page) reads the same resolved path, so the deck cannot disagree with itself.

Resolution order, and every branch is labelled so the page can say which one it used:

  1. `analyst`               - Sectors carries a per-year company forecast (`company_value_forecasts` /
                               `company_growth_forecasts`). Best case: a third party's own numbers, already
                               inside the licensed dataset.
  2. `third-party-estimate`  - a per-ticker driver file in `data/drivers/<TICKER>.json` that cites a
                               published estimate (broker initiation, company guidance) per driver, with an
                               attribution and an as-of date. The file is REJECTED rather than half-used.
  3. `midcycle-normalised`   - no path available: FY26F is last actual x the sector growth forecast and the
                               level is then held flat, EBITDA at the mid-cycle average. This is the honest
                               fallback, and the page must print that the columns are a normalised level,
                               not a growth path.

Rules this module enforces (the reason it exists):
  * A driver without a `source` invalidates the file - a forecast nobody can trace is not a forecast.
  * A third-party path without `attribution` + `as_of` invalidates the file.
  * Cross-currency paths declare the FX rate and how it was derived.
  * Magnitudes are sanity-checked (margins, growth, net <= EBITDA) so a percentage can never be read as a
    level, and an implausible path degrades to the labelled fallback instead of printing.
"""
from __future__ import annotations

import json
import re
import pathlib
from typing import Any, Optional
from server.report import numfmt as _nf

PATH_DIR = pathlib.Path(__file__).resolve().parents[2] / "data" / "drivers"

SPINE_KEYS = ("revenue", "ebitda", "net_profit")
#: bvps_path carries per-year BVPS in `path_unit == "Rp per share"`; the slide writes PBV(t) = price / path[t].
#: Without it the slide can only divide by a single equity scalar and PBV collapses to one number across the row.
OPTIONAL_KEYS = ("dna", "capex", "interest_expense", "interest_income", "minority", "gross_debt",
                 "other_income", "inventory", "receivables", "payables", "fcf", "working_capital",
                 "bvps_path")
BASIS_LABEL = {
    "analyst": "estimasi analis (Sectors company_value_forecasts)",
    "third-party-estimate": "estimasi tim yang diselaraskan ke basis data berlisensi",
    "midcycle-normalised": "level normalised mid-cycle (bukan kurva pertumbuhan)",
}


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _driver_file(ticker: str) -> Optional[pathlib.Path]:
    p = PATH_DIR / f"{ticker.upper()}.json"
    return p if p.exists() else None


def _validate(doc: dict, ticker: str) -> tuple[list[str], dict]:
    """Return (problems, usable). A file with problems is not used at all."""
    problems: list[str] = []
    drivers = doc.get("drivers") or {}
    years = [str(y) for y in (doc.get("years") or [])]
    if len(years) < 1:
        problems.append("driver file declares no forecast years")
    if str(doc.get("ticker", "")).upper() != ticker.upper():
        problems.append(f"driver file is for {doc.get('ticker')!r}, not {ticker}")
    basis = str(doc.get("basis") or "")
    if basis == "third-party-estimate":
        for key in ("attribution", "as_of"):
            if not doc.get(key):
                problems.append(f"a third-party path must state `{key}`")
    fx = _num(doc.get("fx_rp_bn_per_usd_mn") or doc.get("fx_idr_per_usd")) or 1.0
    if str(doc.get("currency", "")).lower().startswith("usd") and not doc.get("fx_basis"):
        problems.append("a USD path must state how the conversion factor was derived (`fx_basis`)")
    out: dict = {}
    for key in SPINE_KEYS + OPTIONAL_KEYS:
        block = drivers.get(key)
        if not block:
            if key in SPINE_KEYS:
                problems.append(f"driver file is missing the required `{key}` path")
            continue
        path = block.get("path")
        if not isinstance(path, list) or len(path) != len(years):
            problems.append(f"`{key}` path has {len(path) if isinstance(path, list) else 'no'} values "
                            f"against {len(years)} years")
            continue
        raw = [_num(v) for v in path]
        if any(v is None for v in raw):
            problems.append(f"`{key}` path carries a non-numeric value")
            continue
        vals = [float(v) for v in raw if v is not None]
        if not str(block.get("source") or "").strip():
            problems.append(f"`{key}` has no `source` - an untraceable forecast is not a forecast")
            continue
        if key == "bvps_path":
            # BVPS is Rp/share, not Rp bn: never FX-multiply. The slide divides price by it to get PBV(t).
            unit = str(block.get("path_unit") or "").strip().lower()
            if "rp" not in unit or "share" not in unit:
                problems.append("`bvps_path.path_unit` must declare the per-share unit "
                                "(e.g. 'Rp per share') so it cannot be confused with a Rp bn spine")
                continue
            out[key] = {
                "rp_per_share": vals,
                "source": str(block["source"]),
                "note": block.get("note"),
            }
            continue
        out[key] = {
            "rp_bn": [v * fx for v in vals],
            "source": str(block["source"]),
            "note": block.get("note"),
        }
    # If the file carries the three spine keys but no bvps_path the renderer can only divide by a scalar
    # equity and silently prints a flat PBV row. Refuse the file loudly so the slide fails loud, not quiet.
    if all(out.get(k) for k in SPINE_KEYS) and not out.get("bvps_path"):
        problems.append(
            "driver file declares revenue/ebitda/net_profit but no `bvps_path` - PBV would collapse to a "
            "constant scalar across the row; either publish a per-year BVPS array or drop the PBV row")
    if out.get("revenue"):
        for i, _y in enumerate(years):
            if out["revenue"]["rp_bn"][i] <= 0:
                problems.append(f"revenue path is not positive in {years[i]}")
    if out.get("ebitda") and out.get("revenue"):
        for i, _y in enumerate(years):
            m = out["ebitda"]["rp_bn"][i] / out["revenue"]["rp_bn"][i] if out["revenue"]["rp_bn"][i] else 0
            if not 0.02 <= m <= 0.95:
                problems.append(f"EBITDA margin reads {_nf.pcfrac(m, 1)} in {years[i]} - implausible, refusing the file")
    if out.get("net_profit") and out.get("ebitda"):
        for i, _y in enumerate(years):
            if out["net_profit"]["rp_bn"][i] > out["ebitda"]["rp_bn"][i]:
                problems.append(f"net profit exceeds EBITDA in {years[i]}")
    return problems, out


def _from_analyst(sectors_payload: Optional[dict], years: list[str]) -> Optional[dict]:
    """Sectors per-year company forecast, when the dataset carries one."""
    fut = ((sectors_payload or {}).get("future") or {}) if sectors_payload else {}
    cvf = fut.get("company_value_forecasts")
    if not isinstance(cvf, dict) or not cvf:
        return None
    out: dict = {}
    for key, needles in (("revenue", ("revenue", "sales", "pendapatan")),
                         ("ebitda", ("ebitda",)),
                         ("net_profit", ("net_income", "net_profit", "earnings", "laba"))):
        series = None
        for name, vals in cvf.items():
            if any(n in str(name).lower() for n in needles) and isinstance(vals, list) and len(vals) >= len(years):
                series = [_num(v) for v in vals[: len(years)]]
                break
        if series and all(v is not None for v in series):
            out[key] = {"rp_bn": [float(v) for v in series if v is not None],
                        "source": "Sectors future.company_value_forecasts"}
    return out if all(k in out for k in SPINE_KEYS) else None


def _from_midcycle(spine: Optional[dict], years_a: list[str]) -> tuple[dict, list[str]]:
    """The existing behaviour: sector growth applied once, then held flat, EBITDA at mid-cycle."""
    notes = ["Kolom proyeksi adalah LEVEL NORMALISED, bukan kurva pertumbuhan: pertumbuhan sektor dipakai "
             "sekali untuk FY26F lalu levelnya ditahan, dan EBITDA memakai rata-rata mid-cycle."]
    return {"kind": "midcycle"}, notes


# Research houses are never named on a shipped page: the deck cites the licensed dataset, the issuer's own
# filings, public news and the team's own estimates. The calibration trail stays in the repo instead.
RESEARCH_HOUSE_PATTERN = re.compile(
    r"\b(BRIDS|BRI Danareksa|Danareksa Sekuritas|Bahana Sekuritas|Mandiri Sekuritas|BCA Sekuritas|"
    r"BNI Sekuritas|Trimegah Sekuritas|Samuel Sekuritas|Maybank Sekuritas|Mirae Asset|Ciptadana|"
    r"MNC Sekuritas|Panin Sekuritas|Phillip Sekuritas|RHB Sekuritas|CGS[- ]?CIMB|CLSA|Nomura|Macquarie|"
    r"Morgan Stanley|Goldman Sachs|JP ?Morgan|J\.P\. Morgan|Citi Research|UBS Securities|HSBC|"
    r"Jefferies|DBS Group Research|OCBC|UOB Kay Hian|KGI Sekuritas|Kiwoom Sekuritas|BofA|"
    r"BofA Securities|Credit Suisse|Deutsche Bank|Barclays|Nomura Securities)\b", re.I)


def display_attribution(text: str | None, fallback: str = "estimasi tim") -> str:
    """Strip any research-house name from a label that will be printed on a page."""
    if not text:
        return fallback
    cleaned = RESEARCH_HOUSE_PATTERN.sub("", str(text))
    # what is left after the house name is usually not a label: strip the genre words and any bare date, and
    # fall back when nothing identifying survives
    cleaned = re.sub(r"\b(equity research|research|initiation|sekuritas|securities|insight|report|note)\b",
                     "", cleaned, flags=re.I)
    cleaned = re.sub(r"\(?\b(as of )?\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}\b\)?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", cleaned)
    # A literal hyphen inside a character class has to be escaped when it follows an escape: the
    # dash sweep that removed the two dash codepoints here left "[\s,;:\--\(\)\.]", which Python
    # reads as the descending range "\-".."\(" and refuses to compile at all.
    cleaned = re.sub(r"[\s,;:\-\(\)\.]+$", "", re.sub(r"^[\s,;:\-\(\)\.]+", "", cleaned)).strip()
    return cleaned if len(cleaned) >= 8 else fallback


def resolve_forecast_path(
    ticker: str,
    *,
    assum: Optional[dict] = None,
    sectors_payload: Optional[dict] = None,
    actual_years: Optional[list[str]] = None,
    path_dir: Optional[pathlib.Path] = None,
) -> dict:
    """Resolve the FY26F+ columns for `ticker`. Always returns a dict with `basis`, `years`, `available`."""
    global PATH_DIR
    keep, PATH_DIR = PATH_DIR, (path_dir or PATH_DIR)
    try:
        years = ["2026F", "2027F", "2028F"]
        years_a = [str(y) for y in (actual_years or ["2024A", "2025A"])]

        def labelled(result: dict) -> dict:
            result["basis_label"] = BASIS_LABEL.get(result.get("basis"), result.get("basis"))
            return result

        analyst = _from_analyst(sectors_payload, years)
        if analyst:
            return labelled({
                "available": True, "ticker": ticker, "basis": "analyst", "years": years,
                "drivers": analyst, "problems": [],
                "attribution": "Sectors company_value_forecasts",
                "notes": ["Kolom proyeksi berasal dari estimasi analis di dalam dataset Sectors."],
            })

        fp = (path_dir or PATH_DIR) / f"{ticker.upper()}.json"
        if fp.exists():
            doc = json.loads(fp.read_text())
            problems, drivers = _validate(doc, ticker)
            if problems:
                return labelled({
                    "available": False, "ticker": ticker, "basis": "invalid-driver-file", "years": years,
                    "problems": problems, "file": str(fp),
                    "notes": ["File driver tidak dipakai: " + p for p in problems],
                })
            return labelled({
                "available": True, "ticker": ticker, "basis": str(doc.get("basis") or "third-party-estimate"),
                "years": [str(y) for y in doc["years"]], "drivers": drivers, "problems": [],
                "attribution": doc.get("attribution"), "as_of": doc.get("as_of"),
                "independence_note": doc.get("independence_note"),
                "fx_rp_bn_per_usd_mn": _num(doc.get("fx_rp_bn_per_usd_mn") or doc.get("fx_idr_per_usd")),
                "notes": [n for n in [doc.get("independence_note")] if n],
                "file": str(fp),
            })

        path, notes = _from_midcycle(assum, years_a)
        return labelled({"available": True, "ticker": ticker, "basis": "midcycle-normalised", "years": years,
                         "drivers": {}, "problems": [], "notes": notes})
    finally:
        PATH_DIR = keep
