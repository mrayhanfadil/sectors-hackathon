"""News → forward-assumptions ledger.

Bridges ``news_output`` (ADK state key, see
``agents/adk/agents/instructions.py`` news schema) into quantified
forward drivers consumed by the modeler. The social leg is retired
(14 Sep 2026) — ``extract_drivers`` keeps its ``social`` param for
back-compat and treats None as no social drivers.

Placement: ``agents/valuation/`` (not ``agents/adk/tools/``) because this is
deterministic valuation input math consumed by the modeler / ``dcf_full``
path — same reason ``assumptions.py`` and ``gates.py`` live here.

LOUD rules (enforced, never silent):
  1. No driver without citation (url + date + verbatim quote) becomes an
     overlay. Uncited quantified claims are dropped AND counted in
     ``dropped_uncited``.
  2. Conflicting signals for the same driver kind are ALL recorded; the
     overlay uses the conservative one (min growth for revenue/NI, max
     capex_pct for capex since higher capex lowers FCF) and the conflict
     is flagged in the overlay provenance.

Schema extension (never breaks existing keys):
  - Numeric assumption keys stay plain floats (``dcf_full`` does
    ``float(...)`` casts) — provenance travels in parallel
    ``{key}_overlay`` detail objects plus a top-level ``news_overlays`` block.
  - New keys introduced only as additions: ``ni_growth`` (+ provenance),
    ``news_overlays``, ``assumption_ledger``.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# State unwrapping (ADK state values are often str-wrapped / fenced JSON)
# ---------------------------------------------------------------------------

def _unwrap(value: Any) -> Any:
    """Unwrap ADK state values: fenced ```json, {"news_output": [...]} envelope, raw JSON str."""
    if not isinstance(value, str):
        return value
    s = value.strip()
    if "```" in s:
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
        if m:
            s = m.group(1).strip()
    try:
        parsed = json.loads(s)
    except Exception:
        return value
    if isinstance(parsed, dict) and len(parsed) == 1:
        sole = next(iter(parsed.values()))
        if isinstance(sole, (list, dict)):
            return sole
    return parsed


def _as_list(payload: Any) -> List[Dict[str, Any]]:
    payload = _unwrap(payload)
    if isinstance(payload, list):
        return [i for i in payload if isinstance(i, dict)]
    if isinstance(payload, dict):
        for k in ("items", "articles", "results", "sources"):
            v = payload.get(k)
            if isinstance(v, list):
                return [i for i in v if isinstance(i, dict)]
        return [payload]
    return []


# ---------------------------------------------------------------------------
# Quantified-driver extraction
# ---------------------------------------------------------------------------

_PCT = r"([+-]?\d+(?:[.,]\d+)?)\s*%"

REVENUE_KW = re.compile(
    r"sssg|same[-\s]?store|revenue|pendapatan|penjualan|sales|top[-\s]?line|"
    r"target\s+penjualan|store\s+sales|like[-\s]?for[-\s]?like",
    re.IGNORECASE,
)
NI_KW = re.compile(
    r"net\s+(income|profit)|laba\s+bersih|bottom[-\s]?line|earnings?\s+growth|"
    r"\bni\s+growth\b|net\s+earnings|profit\s+growth",
    re.IGNORECASE,
)
CAPEX_KW = re.compile(
    r"capex|belanja\s+modal|capital\s+expenditure|capital\s+spending|"
    r"store\s+expansion|gerai\s+baru|new\s+stores?|expansion|store\s+refresh|"
    r"rebrand\s+capex|expansion\s+capex",
    re.IGNORECASE,
)
UP_KW = re.compile(
    r"\b(naik|meningkat|tumbuh|tambah|ekspansi|accelerat|increas|rais|boost|"
    r"expand|growth|up\s+\d|higher|tambah\s+gerai|buka\s+gerai)\b",
    re.IGNORECASE,
)
DOWN_KW = re.compile(
    r"\b(turun|menurun|pangkas|potong|cut|reduc|decreas|delay|tunda|hold|"
    r"slow|lower|scale\s+back)\b",
    re.IGNORECASE,
)
HORIZON = re.compile(
    r"\b(FY\s?\d{2,4}|20\d{2}[A-Z]?|H[12][-\s]?20\d{2}|Q[1-4][-\s]?20\d{2}|"
    r"semester\s+[IVX1-2]+|full[-\s]?year|next\s+year|tahun\s+depan|"
    r"2026F?|2027F?|2028F?)\b",
    re.IGNORECASE,
)
IDR_AMOUNT = re.compile(
    r"(?:Rp|IDR)\s?([\d.,]+\s?(?:T|B|M|triliun|miliar|juta)?)",
    re.IGNORECASE,
)


def _to_float(num: str) -> Optional[float]:
    try:
        return float(num.replace(",", "."))
    except (ValueError, TypeError):
        return None


def _cite(item: Dict[str, Any], text_keys: tuple = ("snippet", "text", "content", "key_fact")) -> Optional[Dict[str, str]]:
    """Return {url, date, quote} or None when any citation part is missing (LOUD rule 1)."""
    url = str(item.get("url") or "").strip()
    date = str(item.get("date") or "").strip()
    quote = ""
    for k in text_keys:
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            quote = v.strip()
            break
    if not url or not date or not quote:
        return None
    return {"url": url, "date": date, "quote": quote}


def _classify(text: str) -> Optional[str]:
    has_rev = bool(REVENUE_KW.search(text))
    has_ni = bool(NI_KW.search(text))
    has_capex = bool(CAPEX_KW.search(text))
    # NI keywords win ties (more specific); capex only when no growth % context claims it
    if has_ni:
        return "ni_growth"
    if has_rev:
        return "revenue_growth"
    if has_capex:
        return "capex"
    return None


# % mentions that are valuation-ratio levels, not forward growth guides.
_RATIO_CTX = re.compile(
    r"yield|payout|\bpe\b|p\/bv?|\bpbv?\b|ev\/ebitda|roe|roic|margin|beta|"
    r"dividend|div\b",
    re.IGNORECASE,
)
_PROXIMITY_CHARS = 80


def _proximate_candidates(blob: str) -> List[tuple]:
    """Classify each % mention by nearest growth keyword within ±80 chars.

    Skips %s sitting in valuation-ratio context (yield, PE, ROE, margin...).
    Returns [(kind, value_pct), ...].
    """
    cands: List[tuple] = []
    rev_spans = [m.start() for m in REVENUE_KW.finditer(blob)]
    ni_spans = [m.start() for m in NI_KW.finditer(blob)]
    if not rev_spans and not ni_spans:
        return cands
    for m in re.finditer(_PCT, blob):
        val = _to_float(m.group(1))
        if val is None:
            continue
        ctx = blob[max(0, m.start() - 25): m.end() + 25]
        if _RATIO_CTX.search(ctx):
            continue
        d_rev = min((abs(m.start() - s) for s in rev_spans), default=float("inf"))
        d_ni = min((abs(m.start() - s) for s in ni_spans), default=float("inf"))
        if min(d_rev, d_ni) > _PROXIMITY_CHARS:
            continue
        kind = "ni_growth" if d_ni <= d_rev else "revenue_growth"
        cands.append((kind, val))
    return cands


def extract_drivers(
    news: Any = None,
    social: Any = None,
    *,
    ticker: str = "",
) -> Dict[str, Any]:
    """Extract quantified forward drivers, each with url + date + verbatim quote.

    Returns ledger dict: {ticker, drivers: [...], dropped_uncited: int,
    conflicts: [...]}. Never raises on malformed input (returns empty ledger).
    """
    drivers: List[Dict[str, Any]] = []
    dropped = 0

    def _ingest(items: List[Dict[str, Any]], origin: str) -> None:
        nonlocal dropped
        for item in items:
            texts: List[str] = []
            for k in ("snippet", "text", "content", "key_fact", "relevance", "narrative", "title"):
                v = item.get(k)
                if isinstance(v, str) and v.strip():
                    texts.append(v.strip())
            blob = " | ".join(texts)
            if not blob:
                continue
            cands = _proximate_candidates(blob)
            has_capex = bool(CAPEX_KW.search(blob))
            if not cands and not has_capex:
                continue
            cite = _cite(item)
            if cite is None:
                # Quantified-or-not: a forward-looking claim without citation is dropped loudly.
                dropped += 1
                continue
            horizon_m = HORIZON.search(blob)
            horizon = horizon_m.group(0) if horizon_m else ""
            for kind in ("revenue_growth", "ni_growth"):
                vals = [v for k, v in cands if k == kind]
                if not vals:
                    continue
                # Conservative pre-pick per item is NOT done here; conflicts
                # resolve at overlay time. Keep the max-magnitude % mentioned
                # as the item's read (explicit, single number per item).
                value = max(vals, key=abs)
                drivers.append({
                    "kind": kind,
                    "value_pct": round(value, 4),
                    "horizon": horizon,
                    "origin": origin,
                    **cite,
                })
            if has_capex:  # capex signal: direction + magnitude + horizon
                direction = "flat"
                if UP_KW.search(blob):
                    direction = "up"
                elif DOWN_KW.search(blob):
                    direction = "down"
                pcts = [_to_float(m) for m in re.findall(_PCT, blob)]
                pcts = [p for p in pcts if p is not None]
                # Prefer a % proximate to the capex keyword over a stray % elsewhere.
                cap_spans = [m.start() for m in CAPEX_KW.finditer(blob)]
                near: List[float] = []
                for m in re.finditer(_PCT, blob):
                    v = _to_float(m.group(1))
                    if v is None:
                        continue
                    if min((abs(m.start() - s) for s in cap_spans), default=float("inf")) <= _PROXIMITY_CHARS:
                        near.append(v)
                magnitude = near[0] if near else (pcts[0] if pcts else None)
                idr_m = IDR_AMOUNT.search(blob)
                drivers.append({
                    "kind": "capex",
                    "direction": direction,
                    "magnitude_pct": round(magnitude, 4) if magnitude is not None else None,
                    "magnitude_idr_raw": idr_m.group(0).strip() if idr_m else "",
                    "horizon": horizon,
                    "origin": origin,
                    **cite,
                })

    try:
        _ingest(_as_list(news), "news")
    except Exception:
        pass
    try:
        social_unwrapped = _unwrap(social)
        items: List[Dict[str, Any]] = []
        if isinstance(social_unwrapped, dict):
            src = social_unwrapped.get("sources")
            if isinstance(src, list):
                items.extend([i for i in src if isinstance(i, dict)])
            # Narratives/timeline carry no per-item url -> ingested but dropped
            # loudly by _cite (counts toward dropped_uncited).
            for k in ("top_3_narratives", "timeline"):
                v = social_unwrapped.get(k)
                if isinstance(v, list):
                    for n in v:
                        if isinstance(n, dict):
                            items.append(n)
                        elif isinstance(n, str):
                            items.append({"narrative": n})
        elif isinstance(social_unwrapped, list):
            items.extend([i for i in social_unwrapped if isinstance(i, dict)])
        _ingest(items, "social")
    except Exception:
        pass

    # Conflict scan per kind (distinct values -> conflict flagged, LOUD rule 2)
    conflicts: List[Dict[str, Any]] = []
    for kind in ("revenue_growth", "ni_growth"):
        vals = sorted({d["value_pct"] for d in drivers if d["kind"] == kind})
        if len(vals) > 1:
            conflicts.append({
                "kind": kind,
                "values_pct": vals,
                "conservative_pct": min(vals),
                "sources": [
                    {"url": d["url"], "date": d["date"], "quote": d["quote"]}
                    for d in drivers if d["kind"] == kind
                ],
            })
    cap_dirs = {d["direction"] for d in drivers if d["kind"] == "capex"}
    if len(cap_dirs) > 1:
        conflicts.append({
            "kind": "capex",
            "directions": sorted(cap_dirs),
            "sources": [
                {"url": d["url"], "date": d["date"], "quote": d["quote"]}
                for d in drivers if d["kind"] == "capex"
            ],
        })

    return {
        "ticker": (ticker or "").upper().strip(),
        "drivers": drivers,
        "dropped_uncited": dropped,
        "conflicts": conflicts,
    }


# ---------------------------------------------------------------------------
# Overlay application (extend base schema, never break it)
# ---------------------------------------------------------------------------

def apply_ledger_overlays(
    base_assumptions: Dict[str, Any],
    ledger: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply ledger drivers as overlays onto a copy of base_assumptions.

    - Numeric keys stay plain floats (``dcf_full``-compatible); provenance
      travels in ``{key}_overlay`` detail objects + ``news_overlays`` block.
    - No cited driver -> no overlay key touched, ``overlays_applied`` == [].
    - Conflicts: both recorded, conservative value used, conflict flagged.
    """
    out = copy.deepcopy(base_assumptions) if base_assumptions else {}
    ledger = ledger or {}
    drivers = ledger.get("drivers", []) or []
    conflicts = {c.get("kind"): c for c in (ledger.get("conflicts", []) or []) if c.get("kind")}

    applied: List[str] = []
    overlays: Dict[str, Any] = {}

    def _prov(ds: List[Dict[str, Any]], extra: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **extra,
            "drivers": [
                {"url": d["url"], "date": d["date"], "quote": d["quote"], "origin": d.get("origin", "")}
                for d in ds
            ],
        }

    # -- revenue growth -> g1 (dcf engine key) + revenue_growth alias --------
    rev = [d for d in drivers if d["kind"] == "revenue_growth"]
    if rev:
        conservative = min(d["value_pct"] for d in rev)  # LOUD rule 2
        g_decimal = round(conservative / 100.0, 6)
        conflict = conflicts.get("revenue_growth")
        prov = _prov(rev, {
            "value": g_decimal,
            "value_pct": conservative,
            "conflict": bool(conflict),
            "conflict_note": (
                f"Conflicting revenue guides {conflict['values_pct']} — "
                f"using conservative {conservative}%." if conflict else ""
            ),
        })
        for key in ("g1", "revenue_growth", "rev_growth"):
            if key == "g1" or key in out:
                out[key] = g_decimal
                out[f"{key}_overlay"] = prov
        overlays["revenue_growth"] = prov
        applied.append("revenue_growth")

    # -- NI growth -> ni_growth (new key, additive only) ----------------------
    ni = [d for d in drivers if d["kind"] == "ni_growth"]
    if ni:
        conservative = min(d["value_pct"] for d in ni)
        g_decimal = round(conservative / 100.0, 6)
        conflict = conflicts.get("ni_growth")
        prov = _prov(ni, {
            "value": g_decimal,
            "value_pct": conservative,
            "conflict": bool(conflict),
            "conflict_note": (
                f"Conflicting NI guides {conflict['values_pct']} — "
                f"using conservative {conservative}%." if conflict else ""
            ),
        })
        out["ni_growth"] = g_decimal
        out["ni_growth_overlay"] = prov
        overlays["ni_growth"] = prov
        applied.append("ni_growth")

    # -- capex: numeric overlay ONLY when an explicit % magnitude is cited ----
    cap = [d for d in drivers if d["kind"] == "capex"]
    quantified = [d for d in cap if d.get("magnitude_pct") is not None]
    if quantified and isinstance(out.get("capex_pct"), (int, float)):
        # Relative adjustment off base; conflicting %s -> max (conservative:
        # higher capex lowers FCF/FV).
        shifts = [d["magnitude_pct"] / 100.0 * (1 if d["direction"] != "down" else -1) for d in quantified]
        conservative_shift = max(shifts)
        new_val = round(float(out["capex_pct"]) * (1 + conservative_shift), 6)
        conflict = conflicts.get("capex")
        prov = _prov(quantified, {
            "value": new_val,
            "base_capex_pct": out["capex_pct"],
            "relative_shift": round(conservative_shift, 6),
            "conflict": bool(conflict),
            "conflict_note": (
                f"Conflicting capex signals {conflict.get('directions')} — "
                "using highest capex (conservative for FCF)." if conflict else ""
            ),
        })
        out["capex_pct"] = new_val
        out["capex_pct_overlay"] = prov
        overlays["capex"] = prov
        applied.append("capex")
    elif cap:
        # Directional-only signal: recorded, NO numeric overlay (LOUD rule 1
        # extended — never invent a magnitude).
        overlays["capex"] = _prov(cap, {
            "value": None,
            "non_quantified": True,
            "note": "Cited capex direction without explicit % magnitude — "
                    "recorded for modeler judgment, no numeric overlay applied.",
            "conflict": bool(conflicts.get("capex")),
        })

    out["news_overlays"] = {
        "overlays_applied": applied,
        "overlays": overlays,
        "n_drivers": len(drivers),
        "dropped_uncited": ledger.get("dropped_uncited", 0),
        "conflicts": ledger.get("conflicts", []),
    }
    out["assumption_ledger"] = ledger
    return out


__all__ = ["extract_drivers", "apply_ledger_overlays"]
