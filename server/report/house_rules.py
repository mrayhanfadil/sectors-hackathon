"""Slide rules — shared validator for `docs/rules/house-report-format.md` §7-§9.

The exhibit/header/footer rules are owned by the renderer, so agents can only break them by
emitting layout themselves (the Critic already catches that). The slide-structure rules are
different: they constrain CONTENT that agents produce or that the cover builders derive, and
until now nothing checked them — the only thing standing between a bad cover and the PDF was a
human reading it.

This module is the single implementation of those checks, imported by:
  - `agents/critic.py`            — the ADK gate (REJECTs the document)
  - `server/report/slide2.py`     — attaches the audit to the render payload
  - `tests/test_house_format_adoption.py` — adoption guards

Every check returns human-readable violation strings; an empty list means compliant. Checks never
raise: a payload that is missing a section is itself a violation, not an exception.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

# --- §7 cover (one-pager) ------------------------------------------------------------------
#: Paragraph 1 + 2 + 3 must share one page with the Key Financials exhibit. Measured at the
#: typography in templates/macros.html this is the point where the exhibit stops fitting and
#: silently moves to page 2, which breaks the layout the cover contract describes.
COVER_COPY_BUDGET = 2600
COVER_BULLETS = 3

# --- §9 Key Financials exhibit --------------------------------------------------------------
KF_HEADER_FIRST = "Year to 31 Dec"
KF_COLUMNS = ("2024A", "2025A", "2026F", "2027F", "2028F")
#: row labels in order; the renderer appends the unit ("Revenue (Rpbn)"), so match by prefix
KF_ROWS = (
    "Revenue", "EBITDA", "EBITDA Growth (%)", "Net Profit", "EPS (Rp)",
    "EPS Growth (%)", "PER (x)", "PBV (x)", "EV/EBITDA (x)",
)
#: absolute Rp figures carry no decimals, percentages and multiples one, EPS one
KF_NO_DECIMAL_ROWS = ("Revenue", "EBITDA", "Net Profit")

# --- §8 narrative mandates ------------------------------------------------------------------
KATALIS_HEADING = "News, Sentimen & Katalis"

# Slide 2 (docs/ammn-slides/slide2-industry-spec.md): three narrative paragraphs, no mandatory
# object. Paragraph 3 reads market positioning only — valuation language there is a domain
# violation, not a style nit, because the numbers live on the valuation page.
INDUSTRY_PAGE_HEADINGS = (
    "1. Kondisi Industri",
    "2. Katalis Spesifik Emiten",
    "3. Sentimen Pasar",
)
# Matched as whole words: a substring test would fire on ordinary copy (and on English
# headlines, where "Copper " contains "per ").
SENTIMENT_FORBIDDEN_TERMS = (
    "target price", "fair value", "harga wajar", "nilai wajar", "multiple", "valuasi",
    "ev/ebitda", "wacc", "pbv", "p/bv", "p/e", "dcf", "tp",
)
SENTIMENT_FORBIDDEN_CS = (r"\bPER\b",)  # the multiple is written in caps
VALUASI_HEADING = "Valuasi"
#: the four sentence blocks the valuation paragraph must carry, in order
VALUASI_BLOCKS = (
    ("methodology", ("menggunakan", "TP Rp")),
    ("forecast linkage", ("CAGR",)),
    ("trading multiple", ("dibandingkan", "rata-rata historis")),
    ("risk to view", ("Risiko terhadap pandangan ini",)),
)
#: a catalyst paragraph either quantifies the impact or says why it cannot be quantified
NO_BASIS_MARKERS = ("tidak dapat dikuantifikasi", "tanpa basis", "tidak ada basis")

_NUM = re.compile(r"\d")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _has_number(text: str) -> bool:
    return bool(_NUM.search(text or ""))


def _rows_of(kf: dict) -> list[Any]:
    rows = (kf or {}).get("rows") or []
    return [r for r in rows if isinstance(r, (list, tuple)) and r]


# ------------------------------------------------------------------ §7 cover structure
def audit_cover(slide1: dict, slide2: dict) -> list[str]:
    """Structure of the one-pager cover: sidebar blocks, highlight claims, theme title."""
    out: list[str] = []
    s1 = slide1 or {}

    # sidebar: rating, its change status, and the price box with the previous target
    rating = s1.get("rating") or {}
    if not _text(rating.get("action")):
        out.append("cover: rating block missing (`rating.action`)")
    if not _text(rating.get("action_status")):
        out.append("cover: rating change status missing (`rating.action_status`) — the reader "
                   "scans this before reading anything else")
    labels = [_text(r[0]) for r in ((s1.get("price_box") or {}).get("rows") or []) if r]
    for needed in ("Last Price", "Target Price", "Previous TP", "Upside/Downside"):
        if not any(lbl.startswith(needed) for lbl in labels):
            out.append(f"cover: price box is missing the {needed!r} row")
    stats = [(_text(r[0]), _text(r[1])) for r in ((s1.get("stats") or {}).get("rows") or []) if r]
    for needed in ("No. of Shares", "Mkt Cap", "Free Float"):
        if not any(lbl.startswith(needed) for lbl, _ in stats):
            out.append(f"cover: secondary stats missing {needed!r}")
    if not (s1.get("stats") or {}).get("major_shareholders"):
        out.append("cover: major shareholder block is empty")
    if not (s1.get("jci_chart") or {}).get("price"):
        out.append("cover: relative-performance chart has no series")
    if not _text((s1.get("analyst") or {}).get("name")):
        out.append("cover: analyst block missing a name")
    if not _text(s1.get("theme_title")):
        out.append("cover: theme title missing — the report must state its thesis, not a "
                   "generic product name")
    elif s1["theme_title"].strip().lower() in {"company update", "update", "equity research"}:
        out.append(f"cover: theme title {s1['theme_title']!r} is generic")

    bullets = s1.get("highlights") or []
    if len(bullets) != COVER_BULLETS:
        out.append(f"cover: {len(bullets)} highlights, expected {COVER_BULLETS}")
    for i, b in enumerate(bullets, 1):
        if not _has_number(_text(b)):
            out.append(f"cover: highlight {i} carries no number — every highlight is a "
                       "quantitative claim, not an adjective")
    if not _text((s1.get("financial_para") or {}).get("body")):
        out.append("cover: paragraph 1 (financial performance) missing")
    if slide2 is not None and not _text((slide2 or {}).get("valuasi", {}).get("body")):
        out.append("cover: paragraph 3 (valuation) missing")
    return out


# ------------------------------------------------------------------ §8 paragraph mandates
def audit_katalis(text: str) -> list[str]:
    """Paragraph 2: quantified catalysts + an explicit priced-in verdict."""
    out: list[str] = []
    body = _text(text)
    if not body:
        return ["paragraph 2 (news/sentiment/catalysts) is missing"]
    if "Katalis" not in body:
        out.append("paragraph 2 does not identify the period's catalysts")
    if "Priced-in" not in body and "price-in" not in body:
        out.append("paragraph 2 has no verdict on whether the market has priced the "
                   "catalysts in — required, and it must read off relative performance")
    if not _has_number(body):
        out.append("paragraph 2 carries no number")
    if not any(mark in body for mark in NO_BASIS_MARKERS) and body.count("Rp") < 2:
        out.append("paragraph 2 neither quantifies each catalyst's impact nor states that it "
                   "cannot be quantified (silence reads as an implied zero)")
    return out


def audit_valuasi(text: str) -> list[str]:
    """Paragraph 3: the four mandated sentence blocks, in order."""
    body = _text(text)
    if not body:
        return ["paragraph 3 (valuation) is missing"]
    out: list[str] = []
    for name, markers in VALUASI_BLOCKS:
        if not all(m in body for m in markers):
            out.append(f"paragraph 3 missing the {name} block (expected "
                       f"{' + '.join(repr(m) for m in markers)})")
    if "peer" not in body.lower() and "subsector" not in body.lower():
        out.append("paragraph 3 compares against no peer or sector reference")
    return out


def audit_industry_page(page: Optional[dict], payload: Optional[dict] = None) -> list[str]:
    """Audit slide 2 of the deck (`docs/ammn-slides/slide2-industry-spec.md`).

    Three paragraphs are mandatory and none may be empty; paragraph 3 must not carry valuation
    language. A payload with no such page is not applicable rather than a violation, so an
    archetype that never renders it cannot be failed for a page it does not have.
    """
    if not isinstance(page, dict) or not page:
        return []
    paras = [p for p in (page.get("paragraphs") or []) if isinstance(p, dict)]
    violations: list[str] = []
    headings = [str(p.get("heading") or "") for p in paras]
    for want in INDUSTRY_PAGE_HEADINGS:
        if want not in headings:
            violations.append(f"slide 2 is missing paragraph '{want}'")
    for p in paras:
        if not _text(p.get("body")):
            violations.append(f"slide 2 paragraph '{p.get('heading') or '?'}' has no body")
    sentiment = _text(next(
        (p.get("body") for p in paras if str(p.get("heading") or "").startswith("3.")), ""
    )).lower()
    leaked = sorted(
        {t for t in SENTIMENT_FORBIDDEN_TERMS if re.search(rf"\b{re.escape(t)}\b", sentiment)}
    )
    leaked += sorted({m for pat in SENTIMENT_FORBIDDEN_CS for m in re.findall(pat, _text(
        next((p.get("body") for p in paras if str(p.get("heading") or "").startswith("3.")), "")
    ))})
    if leaked:
        violations.append(
            "slide 2 paragraph 3 (sentiment) carries valuation language: " + ", ".join(leaked)
        )

    # §6.1 one-sided related-party flow. The filings block carries both directions, and the press
    # leads with the buys, so a page that reports one side is sourced and still misleading. Checked
    # only when the payload carries BOTH sides; an absent block is the copy's problem, not this
    # audit's.
    digest = (payload or {}).get("filings_digest") or {}
    buy_n = int((digest.get("buy") or {}).get("n") or 0)
    sell_n = int((digest.get("sell") or {}).get("n") or 0)
    if buy_n and sell_n:
        catalysts = _text(
            next(
                (p.get("body") for p in paras if str(p.get("heading") or "").startswith("2.")), ""
            )
        ).lower()
        for direction in ("beli", "jual"):
            if direction not in catalysts:
                violations.append(
                    f"slide 2 paragraph 2 omits related-party '{direction}' transactions although "
                    f"the filings carry both ({buy_n} beli / {sell_n} jual)"
                )
    return violations


def audit_copy_budget(bodies: Iterable[Any]) -> list[str]:
    total = sum(len(_text(b)) for b in bodies)
    if total > COVER_COPY_BUDGET:
        return [
            f"cover copy is {total} chars, over the {COVER_COPY_BUDGET}-char one-page budget — "
            "the Key Financials exhibit will be pushed off page 1 and the layout contract breaks"
        ]
    return []


# ------------------------------------------------------------------ §9 Key Financials
def audit_key_financials(kf: Optional[dict]) -> list[str]:
    out: list[str] = []
    kf = kf or {}
    if not kf:
        return ["Key Financials exhibit missing from the cover"]
    headers = [_text(h) for h in (kf.get("headers") or [])]
    if headers[:1] != [KF_HEADER_FIRST]:
        out.append(f"Key Financials first header cell is {headers[:1]} — expected "
                   f"{KF_HEADER_FIRST!r}")
    if tuple(headers[1:]) != KF_COLUMNS:
        out.append(f"Key Financials columns are {headers[1:]} — expected two actuals and "
                   f"three forecasts {list(KF_COLUMNS)}")
    labels = [_text(r[0]) for r in _rows_of(kf)]
    if len(labels) != len(KF_ROWS):
        out.append(f"Key Financials has {len(labels)} rows — expected {len(KF_ROWS)}")
    for expected, got in zip(KF_ROWS, labels):
        if not got.startswith(expected):
            out.append(f"Key Financials row {got!r} where {expected!r} was expected (order is "
                       "part of the contract)")
    # units belong in the row labels once the column caption is a date
    for row in _rows_of(kf):
        label = _text(row[0])
        if label in KF_ROWS and label in ("Revenue", "EBITDA", "Net Profit"):
            out.append(f"Key Financials row {label!r} carries no unit — with a "
                       f"{KF_HEADER_FIRST!r} caption every Rp figure needs (Rpbn) in its label")
    # negatives read (28,8) in a house table, never -28,8
    for row in _rows_of(kf):
        for cell in row[1:]:
            if _text(cell).startswith("-"):
                out.append(f"Key Financials {_text(row[0])!r} prints {cell!r} — negative values "
                           "use the accounting parenthesis form")
                break
    # Decimals: none for the absolute Rp rows, one for multiples, percentages and EPS. The
    # parenthesis form must be unwrapped first or "(59,5)" counts as two decimals.
    def _decimals(cell: Any) -> Optional[int]:
        c = _text(cell).strip().strip("()").strip()
        if c in ("", "n/a", "-", "NA"):
            return None
        return len(c.split(",")[1]) if "," in c else 0

    for row in _rows_of(kf):
        label = _text(row[0])
        is_rpbn = label.endswith("(Rpbn)")
        for cell in row[1:]:
            digits = _decimals(cell)
            if digits is None:
                continue
            if is_rpbn and digits:
                out.append(f"Key Financials {label!r} shows {cell!r} — absolute Rp figures carry "
                           "no decimals")
            elif not is_rpbn and digits != 1:
                out.append(f"Key Financials {label!r} shows {cell!r} — percentages, multiples and "
                           "EPS carry exactly one decimal")
    if not kf.get("notes"):
        out.append("Key Financials has no derivation note (the forecast basis must be printed)")
    return out


PERFORMANCE_PAGE_QUADRANTS = (
    "Revenue & Revenue Growth",
    "EBITDA & EBITDA Margin",
    "Net Profit & EPS Growth",
    "DER vs ROE",
)


def audit_performance_page(page: Optional[dict], payload: Optional[dict] = None) -> list[str]:
    """Audit slide 3 of the deck (`docs/ammn-slides/slide3-visual-spec.md`).

    Four quadrants, each a chart that carries its own narrative block — the spec is explicit that the
    narrative must sit with its chart, not collected at the end of the page. Two things make this
    page worth gating rather than trusting: the cross-exhibit tie-out rule, and the fact that a
    forecast series can be built from assumptions the page itself should be warning about.
    """
    if not isinstance(page, dict) or not page:
        return []
    # The source table can be absent from a payload (a fixture, a non-financial archetype). In that
    # case an empty quadrant is honest rather than a violation; when the table IS there, an empty
    # quadrant means the page failed to use the data it had, and that is a violation.
    kf = ((payload or {}).get("cover") or {}).get("slide2") or {}
    has_source_table = bool((kf.get("key_financials") or {}).get("rows"))
    violations: list[str] = []
    quads = [q for q in (page.get("quadrants") or []) if isinstance(q, dict)]
    titles = [str(q.get("title") or "") for q in quads]
    for want in PERFORMANCE_PAGE_QUADRANTS:
        if want not in titles:
            violations.append(f"slide 3 is missing quadrant '{want}'")
    for q in quads:
        title = str(q.get("title") or "?")
        bars = [v for v in (q.get("bars") or []) if v is not None]
        line = [v for v in (q.get("line") or []) if v is not None]
        if has_source_table and len(bars) < 2:
            violations.append(f"slide 3 quadrant '{title}' has no usable bar series")
        if has_source_table and not line:
            violations.append(f"slide 3 quadrant '{title}' has no line series")
        narrative = _text(q.get("narrative"))
        if len(narrative) < 120:
            violations.append(f"slide 3 quadrant '{title}' has no attached narrative block")
        labels = q.get("labels") or []
        if bars and labels and len(bars) != len(labels):
            violations.append(f"slide 3 quadrant '{title}' bars do not match its period labels")
        if q.get("actual_n") is None:
            violations.append(f"slide 3 quadrant '{title}' does not mark which bars are actual")

    # Tie-out (spec: no number may differ between this slide and Key Financials for the same period).
    # Only checked against the block the quadrant names, so the check is real rather than decorative.
    if payload:
        kf_rows = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {}).get(
            "rows"
        ) or []
        kf_headers = (
            (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {}).get(
                "headers"
            )
            or []
        )[1:]
        if kf_rows and kf_headers:
            for label in ("revenue", "ebitda", "net profit"):
                row = next(
                    (
                        r
                        for r in kf_rows
                        if label in str(r[0] if isinstance(r, (list, tuple)) and r else "").lower()
                    ),
                    None,
                )
                if not row:
                    continue
                cover_values = [p for p in (_parse_id_like(v) for v in row[1:]) ]
                quad = next((q for q in quads if q.get("title", "").lower().startswith(label.split()[0])), None)
                if not quad:
                    continue
                for i, value in enumerate(quad.get("bars") or []):
                    if value is None or i >= len(cover_values):
                        continue
                    reference = cover_values[i]
                    if reference is None:
                        continue
                    if abs(float(value) - float(reference)) > max(0.5, abs(reference) * 0.001):
                        violations.append(
                            f"slide 3 '{quad.get('title')}' {kf_headers[i]} = {value} but the Key "
                            f"Financials exhibit says {reference} (tie-out)"
                        )
    return violations


def _parse_id_like(value: Any) -> Optional[float]:
    """Parse the cover table's pre-formatted cells the Indonesian way (see performance_page)."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if text in ("", "—", "-", "n/a", "N/A"):
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("%", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") == 1 and len(text.split(".")[1]) == 3:
        text = text.replace(".", "")
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


# ------------------------------------------------------------------ entry point
def audit_house_rules(payload: Optional[dict]) -> dict:
    """Audit a render payload against §7-§9.

    Returns {ok, applicable, violations, sections, copy_chars, copy_budget}. `applicable` is
    False for documents that carry no cover spread at all (an archetype that is not `single`),
    so the gate does not reject a document for a section it never had.
    """
    payload = payload or {}
    cover = payload.get("cover") or {}
    slide1 = cover.get("slide1") or {}
    slide2 = cover.get("slide2") or {}
    applicable = bool(slide1 or slide2)

    violations: list[str] = []
    if applicable:
        violations += audit_cover(slide1, slide2)
        violations += audit_katalis((slide2.get("katalis") or {}).get("body", ""))
        violations += audit_valuasi((slide2.get("valuasi") or {}).get("body", ""))
        violations += audit_copy_budget([
            (slide1.get("financial_para") or {}).get("body", ""),
            (slide2.get("katalis") or {}).get("body", ""),
            (slide2.get("valuasi") or {}).get("body", ""),
        ])
        violations += audit_key_financials(slide2.get("key_financials") or {})
    # Slide 2 of the deck is audited regardless of the cover spread: it is its own page.
    violations += audit_industry_page(payload.get("industry_page"), payload)
    # Slide 3 of the deck is its own page as well.
    violations += audit_performance_page(payload.get("performance_page"), payload)
    return {
        "ok": not violations,
        "applicable": applicable,
        "violations": violations,
        "sections": [
            "7-cover",
            "8-paragraphs",
            "9-key-financials",
            "slide2-industry",
            "slide3-performance",
        ],
        "copy_chars": sum(len(_text(b)) for b in (
            (slide1.get("financial_para") or {}).get("body", ""),
            (slide2.get("katalis") or {}).get("body", ""),
            (slide2.get("valuasi") or {}).get("body", ""),
        )),
        "copy_budget": COVER_COPY_BUDGET,
    }
