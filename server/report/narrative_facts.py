"""Verified fact sheet for the News/Sentimen/Katalis section (paragraph 2).

One place that owns the numbers for this paragraph, so two consumers agree:

  1. the deterministic template in `server/report/slide2.py` (fallback path), and
  2. the ADK narrative writer (`agents/adk/narrative_runner.py`), which is allowed
     to restate these facts in flowing plain-Indonesian prose and NOTHING else.

That is what makes the anti-fabrication gate possible: `fact_numbers()` returns
every numeric token the sheet carries, and `audit_katalis_narrative` fails the
render when the written copy prints a number that is not in that set. A writer
that invents a figure cannot ship, no matter how good the prose reads.

Numbers are stored as the exact reader-facing strings the deck prints (Indonesian
decimal comma, "Rp x,xx tn", "US$ x.xxx/ton"), so a restatement is a copy of a
verified token, not a re-formatting of a float.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

#: Impact facts stated in the section. Kept here (not in the template) so the
#: writer, the template and the gate read the same strings.
#: `*_note` entries spell out the verified READING of a group of fields: a writer that
#: recombines two raw fields on its own can invent a relationship the data never had
#: (observed 19 Sep 2026: "posisi direksi naik 37,0% menjadi Rp 4.860" merged a stake
#: gain with an average price). Restate the note, do not re-derive it.
IMPACT_FACTS: dict[str, str] = {
    "capex_q1_pct": "69,6%",
    "capex_from": "Rp 5,26 tn",
    "capex_to": "Rp 1,60 tn",
    "fcf_turn": "+Rp 1,69 tn",
    "routine_capex": "Rp 6,39 tn/tahun",
    "director_position": "+37,0%",
    "director_price": "Rp 4.860",
    "director_position_note": "posisi direksi kini untung 37,0% di harga Rp 4.860",
    "capex_note": "belanja modal turun dari Rp 5,26 tn ke Rp 1,60 tn (turun 69,6%) dan kas bebas berbalik positif +Rp 1,69 tn",
    "routine_capex_note": "asumsi belanja modal rutin Rp 6,39 tn/tahun",
}

#: The one honest gap this section must keep disclosing.
IMPACT_GAP = ("harga tembaga rekor tidak bisa dihitung ke laba "
              "(pipeline tanpa tonase/grade/C1, GAP G10)")

#: Sentence the template prints for the gap, and the pointer it keeps.
IMPACT_GAP_SENTENCE = (f"Dampak {IMPACT_GAP} - yang tersedia hanya sensitivitas "
                       "laba operasi di paragraf Valuasi.")

#: Priced-in verdict tail: the multiple comparison is the mandate, not a flourish.
PRICED_IN_TAIL = ("katalis kuartal ini sebagian tercermin, tetapi EV/EBITDA pasar kini "
                  "{ev_ebitda}× masih ~37% di bawah rata-rata 4 tahun 28,42×")
PRICED_IN_MANDATE_TOKENS = ("Priced-in", "EV/EBITDA")

#: Units a printed figure can carry. A bare single digit (C1, G10, "I" in Kuartal I) is
#: too ambiguous to police; a digit with a unit, or two-or-more digits, is a claim.
_NUM_RE = re.compile(r"\d[\d.,]*\s*(?:%|×|pp|tn|md|ton|juta|sh|kali)?")


def _pct(v: Any) -> str:
    try:
        return f"{float(v):+.2f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "n/a"


def _dec(t: str) -> str:
    """`-33.40%` -> `-33,40%` (the deck prints Indonesian decimals)."""
    return re.sub(r"(\d)\.(\d)", r"\1,\2", t)


def printed_numbers(text: str) -> set[str]:
    """Numeric tokens a reader sees, normalized to their digit core.

    `Rp 5,26 tn`, `5.26`, `5,26`, and `23,99 pp` / `23,99 poin` all compare on the
    digits alone, so the gate asks "did this figure come from the fact sheet", not
    "did the writer reformat it". Bare single digits are ignored (they are codes like
    C1, G10, not claims).

    Trade-off, stated on purpose: two unrelated facts that share a digit core (5,26
    as capex vs a fabricated 5,26 laba) are indistinguishable here. The gate is a
    fabrication filter over a small, specific sheet, not an arithmetic verifier - the
    valuation gate and the Critic cover the rest.
    """
    out: set[str] = set()
    for raw in _NUM_RE.findall(str(text or "")):
        token = raw.strip()
        token = re.sub(r"^(?:Rp|US\$)\s*", "", token)
        digits = re.sub(r"[^\d,.]", "", token).strip(".,")
        if not digits:
            continue
        for v in {digits, digits.replace(".", ""), digits.replace(".", "").replace(",", "."),
                  re.sub(r"[.,]", "", digits)}:
            if v and len(re.sub(r"[^\d]", "", v)) >= 2:
                out.add(v)
    return out


def fact_numbers(facts: Optional[dict]) -> set[str]:
    """Every numeric token the sheet carries, in the same normalization."""
    return printed_numbers(json.dumps(facts or {}, ensure_ascii=False))


def facts_hash(facts: Optional[dict]) -> str:
    """Stable hash of the sheet: a frozen narrative is only valid for the facts it saw."""
    blob = json.dumps(facts or {}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]



def _quant_phrase(q: dict) -> str:
    """Reader-facing phrase for the quantified dict a catalyst carries.

    Lives here (not in slide2) so the template, the fact sheet and the writer all read
    the same phrase: one place owns how a harvested field becomes words.
    """
    labels = {"shares": "{} saham", "avg_price": "harga rata-rata {}", "copper": "tembaga {}",
              "broker": "arus beli broker {}", "note": "{}"}
    skip = {"capex_q1", "fcf_q1", "by"}
    bits = []
    for k, v in (q or {}).items():
        if k in skip or k not in labels:
            continue
        val = str(v).strip()
        if k == "note":
            val = val.split(";")[0].strip()
        bits.append(labels[k].format(val))
    return ", ".join(bits)


def impact_statements(impact: Optional[dict] = None) -> list[str]:
    """The impact facts as complete plain sentences.

    A sheet of bare key/value pairs invites a writer to recombine them into a claim the
    data never made (observed: a stake gain "+37,0%" and a price "Rp 4.860" became
    "posisi direksi naik 37,0% menjadi Rp 4.860"). Statements cannot be recombined
    without inventing words, so the sheet hands over statements.
    """
    imp = impact or IMPACT_FACTS
    return [
        f"belanja modal turun dari {imp['capex_from']} ke {imp['capex_to']} "
        f"(turun {imp['capex_q1_pct']} dari kuartal sebelumnya), dan kas bebas berbalik "
        f"positif {imp['fcf_turn']}",
        f"asumsi belanja modal rutin {imp['routine_capex']} - ini bukan potensi naik baru",
        f"posisi direksi kini untung {imp['director_position']} di harga {imp['director_price']}",
    ]


def priced_in_statements(priced: dict, ev_ebitda: str, avg_4y: str = "28,42",
                         discount: str = "~37%") -> list[str]:
    """The priced-in prints as complete plain sentences."""
    out: list[str] = []
    if priced.get("rel_24m"):
        out.append(f"24 bulan terakhir harga {priced.get('abs_24m')} sementara IHSG "
                   f"{priced.get('idx_24m')} (relatif {priced['rel_24m']})")
    if priced.get("rel_90d"):
        # the harvested print already ends in "pp"; the statement spells the unit out, so
        # drop the abbreviation rather than printing "23,99 pp poin persentase"
        pp = re.sub(r"\s*pp\s*$", "", str(priced.get("rel_90d_pp") or "")).strip()
        out.append(f"90 hari terakhir harga {priced.get('rel_90d')} sementara IHSG "
                   f"{priced.get('idx_90d')} (relatif {pp} poin persentase)")
    out.append(f"EV/EBITDA pasar kini {ev_ebitda} kali, dibanding rata-rata 4 tahun {avg_4y} "
               f"kali (diskon {discount})")
    return out


#: The one honest gap, as a statement a writer can restate without our internal code.
GAP_STATEMENT = ("harga tembaga yang naik ke rekor belum bisa dihitung ke laba karena datanya "
                 "belum lengkap - belum ada tonase, kadar, dan biaya produksi per unit")


def build_katalis_facts(payload: Optional[dict], chart: Optional[dict] = None) -> dict:
    """Assemble the verified fact sheet for paragraph 2 from the payload.

    Returns a plain dict: catalysts verbatim, the impact facts, the flows the
    harvest quantified, the priced-in prints and the one gap. No number is
    computed here that the payload does not already carry.
    """
    payload = payload or {}
    chart = chart or {}
    cover = payload.get("cover") or {}
    jci = cover.get("vs_jci") or {}
    meta = cover.get("meta") or {}
    canon = payload.get("canonical_metrics") or {}
    canon_mcap_bn = (canon.get("market_cap_rpbn") or {}).get("value") \
        if isinstance(canon.get("market_cap_rpbn"), dict) else canon.get("market_cap_rpbn")

    # EV/EBITDA the market is paying now, from the canonical block (same source as
    # every other page), so the paragraph cannot quote a second opinion.
    ttm_ev_eb: Optional[float] = None
    nd = meta.get("net_debt_after_cash") or 0.0
    ttm_ebitda = meta.get("ebitda_ttm") or 0.0
    if canon_mcap_bn is not None and nd and ttm_ebitda:
        ttm_ev_eb = (canon_mcap_bn * 1e9 + nd) / ttm_ebitda

    priced: dict[str, str] = {}
    rel24 = chart.get("rel_pct")
    if isinstance(rel24, list) and rel24:
        priced["rel_24m"] = _pct(rel24[-1])
        priced["abs_24m"] = _pct(chart.get("abs_chg_pct"))
        priced["idx_24m"] = _pct(chart.get("idx_chg_pct"))
    m = re.search(r"90d\s+\S+\s+([+\-0-9.,]+%)\s+vs\s+IHSG\s+([+\-0-9.,]+%)\s*\(rel\s+([+\-0-9.,]+\s*pp)\)",
                  str(jci.get("note") or ""))
    if m:
        priced["rel_90d"] = _dec(m.group(1))
        priced["idx_90d"] = _dec(m.group(2))
        priced["rel_90d_pp"] = _dec(m.group(3))

    catalysts = []
    for c in (payload.get("catalysts") or [])[:4]:
        q = {k: str(v).strip() for k, v in (c.get("quantified") or {}).items()}
        catalysts.append({
            "name": str(c.get("name") or "").strip().rstrip("."),
            "quantified": q,
            "effect": str(c.get("effect") or "").strip(),
            "source": str(c.get("source") or "").strip(),
        })

    ev_eb = f"{ttm_ev_eb:.2f}".replace(".", ",") if ttm_ev_eb else "n/a"
    return {
        "section": "katalis",
        "ticker": str((payload.get("meta") or {}).get("ticker") or ""),
        "as_of": str((payload.get("meta") or {}).get("as_of") or ""),
        # --- what the writer sees: complete statements, no bare pairs it could recombine ---
        "catalysts": [{"name": c["name"], "detail": _quant_phrase(c["quantified"]),
                       "effect": c["effect"]} for c in catalysts],
        "impact_statements": impact_statements(),
        "priced_in_statements": priced_in_statements(priced, ev_eb),
        "gap_statement": GAP_STATEMENT,
        "mandate": ("the paragraph must still say Priced-in and compare EV/EBITDA pasar with the "
                    "4-year average"),
        "allowed_terms": ["EV/EBITDA", "IHSG", "GDX", "GDXJ", "PAC", "BUY", "SELL", "HOLD",
                          "Priced-in", "C1", "GAP"],
        # --- what the template and the gate read: the raw values behind those statements ---
        "raw": {
            "catalysts": catalysts,
            "impact": dict(IMPACT_FACTS),
            "impact_gap": IMPACT_GAP,
            "priced_in": priced,
            "ev_ebitda_market": ev_eb,
            "ev_ebitda_4y_avg": "28,42",
            "ev_ebitda_discount_pct": "~37%",
        },
    }


# ------------------------------------------------------------------ frozen narrative

#: Where the ADK narrative writer drops its output. One file per ticker+section.
NARRATIVE_DIR = Path(__file__).resolve().parents[2] / "data" / "narrative"


def narrative_path(ticker: str, section: str = "katalis") -> Path:
    return NARRATIVE_DIR / f"{str(ticker or '').upper()}_{section}.json"


def load_frozen_narrative(ticker: str, facts: Optional[dict], section: str = "katalis") -> Optional[dict]:
    """Read the frozen narrative for this ticker, but only if it matches these facts.

    A narrative written against different numbers is stale by definition: the
    sheet hash has to match, otherwise the caller falls back to the deterministic
    template and the deck says so. Silent reuse of stale prose is the failure mode
    this check exists to prevent.
    """
    path = narrative_path(ticker, section)
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if str(doc.get("section") or "") != section:
        return None
    if str(doc.get("facts_hash") or "") != facts_hash(facts):
        return None
    paragraphs = [str(p).strip() for p in (doc.get("paragraphs") or []) if str(p).strip()]
    if not paragraphs:
        return None
    doc["paragraphs"] = paragraphs
    doc["body"] = " ".join(paragraphs)
    return doc

