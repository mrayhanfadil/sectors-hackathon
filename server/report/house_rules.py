"""Slide rules - shared validator for `docs/rules/house-report-format.md` §7-§9.

The exhibit/header/footer rules are owned by the renderer, so agents can only break them by
emitting layout themselves (the Critic already catches that). The slide-structure rules are
different: they constrain CONTENT that agents produce or that the cover builders derive, and
until now nothing checked them - the only thing standing between a bad cover and the PDF was a
human reading it.

This module is the single implementation of those checks, imported by:
  - `agents/critic.py`            - the ADK gate (REJECTs the document)
  - `server/report/slide2.py`     - attaches the audit to the render payload
  - `tests/test_house_format_adoption.py` - adoption guards

Every check returns human-readable violation strings; an empty list means compliant. Checks never
raise: a payload that is missing a section is itself a violation, not an exception.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional
from server.report import numfmt as _nf
from server.report.narrative_facts import printed_numbers

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
# object. Paragraph 3 reads market positioning only - valuation language there is a domain
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
        out.append("cover: rating change status missing (`rating.action_status`) - the reader "
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
        out.append("cover: theme title missing - the report must state its thesis, not a "
                   "generic product name")
    elif s1["theme_title"].strip().lower() in {"company update", "update", "equity research"}:
        out.append(f"cover: theme title {s1['theme_title']!r} is generic")

    bullets = s1.get("highlights") or []
    if len(bullets) != COVER_BULLETS:
        out.append(f"cover: {len(bullets)} highlights, expected {COVER_BULLETS}")
    for i, b in enumerate(bullets, 1):
        if not _has_number(_text(b)):
            out.append(f"cover: highlight {i} carries no number - every highlight is a "
                       "quantitative claim, not an adjective")
    if not _text((s1.get("financial_para") or {}).get("body")):
        out.append("cover: paragraph 1 (financial performance) missing")
    if slide2 is not None and not _text((slide2 or {}).get("valuasi", {}).get("body")):
        out.append("cover: paragraph 3 (valuation) missing")
    return out


# ------------------------------------------------------------------ §8 paragraph mandates
def audit_katalis(text: str, written: bool = False) -> list[str]:
    """Paragraph 2: quantified catalysts + an explicit priced-in verdict.

    `written=True` for a paragraph a language model wrote: the literal-word arm ("the
    paragraph must contain 'Katalis'") is template-shaped - written prose says the same
    thing in its own words, and `audit_katalis_narrative` already checks the real
    question (does the copy mention a catalyst the fact sheet carried).
    """
    out: list[str] = []
    body = _text(text)
    if not body:
        return ["paragraph 2 (news/sentiment/catalysts) is missing"]
    if not written and "Katalis" not in body:
        out.append("paragraph 2 does not identify the period's catalysts")
    if "Priced-in" not in body and "price-in" not in body:
        out.append("paragraph 2 has no verdict on whether the market has priced the "
                   "catalysts in - required, and it must read off relative performance")
    if not _has_number(body):
        out.append("paragraph 2 carries no number")
    if not any(mark in body for mark in NO_BASIS_MARKERS) and body.count("Rp") < 2:
        out.append("paragraph 2 neither quantifies each catalyst's impact nor states that it "
                   "cannot be quantified (silence reads as an implied zero)")
    return out


#: A written paragraph 2 is prose about the issuer, not a dump of the deck's own plumbing.
DECK_SELF_REFERENCE = ("slide ", "halaman ini", "paragraf ini", "bagian ini", "seksi ini",
                       "exhibit ini", "narasi ini", "layout", "template")
NARRATIVE_PLUMBING = ("via sectors", "freeze", "payload", "harvest", "artifact", "cache",
                      "gap g", "pipeline", "sectors_", "api ", "assumptions")
#: The written paragraph still shares one page with the Key Financials exhibit. Measured:
#: the deterministic template is 1,094 chars and P1+P2+P3 must stay under the 2,600-char
#: cover budget, so written prose gets 1,100 (a longer, prettier paragraph moves the
#: exhibit to the next page).
NARRATIVE_MAX_CHARS = 1100


def audit_katalis_narrative(katalis: Optional[dict]) -> list[str]:
    """A WRITTEN paragraph 2 stays inside its fact sheet (NARRATIVE RULE).

    Only the `writer_frozen` path is checked: the deterministic template is covered
    by `audit_katalis` + `audit_plain_language`, and both run on whichever body the
    payload carries. What is new for written prose is that a language model produced
    it, so four things are enforced:

      1. no number outside the fact sheet (a writer that invents a figure cannot ship);
      2. plain Indonesian, same denylist as every other reader-facing surface;
      3. it talks about the company, not about the deck, and never leaks pipeline
         plumbing ("freeze", "payload", "via Sectors");
      4. it still fits the page.
    """
    k = katalis or {}
    if str(k.get("narrative_source") or "") != "writer_frozen":
        return []
    body = str(k.get("body") or "")
    prov = k.get("narrative_provenance") or {}
    out: list[str] = []

    allowed = {str(x) for x in (prov.get("allowed_numbers") or [])}
    if not allowed:
        out.append("paragraph 2: written narrative carries no fact-sheet numbers - the "
                   "anti-fabrication check cannot run (NARRATIVE RULE)")
    else:
        for tok in sorted(printed_numbers(body) - allowed):
            out.append(f"paragraph 2: written narrative prints '{tok}', which is not in the fact "
                       f"sheet - the writer may only restate verified figures (NARRATIVE RULE)")

    low = body.lower()
    for tok in PLAIN_JARGON:
        if tok.lower() in low:
            out.append(f"paragraph 2: written narrative uses method jargon '{tok}' - plain "
                       f"Indonesian only (PLAIN-LANGUAGE RULE)")
    for pat in PLAIN_JARGON_PATTERNS:
        m = re.search(pat, body)
        if m:
            out.append(f"paragraph 2: written narrative prints '{m.group(0)}' - use the plain form "
                       f"(PLAIN-LANGUAGE RULE)")
    # Word-boundary matching, not substring: "api " would otherwise fire on "tapi".
    for tok in DECK_SELF_REFERENCE:
        if re.search(rf"\b{re.escape(tok.strip())}\b", low):
            out.append(f"paragraph 2: written narrative talks about the deck ('{tok.strip()}') - "
                       f"the copy talks about the company (NARRATIVE RULE)")
    for tok in NARRATIVE_PLUMBING:
        if re.search(rf"\b{re.escape(tok.strip())}\b", low):
            out.append(f"paragraph 2: written narrative leaks pipeline plumbing ('{tok.strip()}') "
                       f"- reader-facing copy carries no internal vocabulary (NARRATIVE RULE)")
    if len(body) > NARRATIVE_MAX_CHARS:
        out.append(f"paragraph 2: written narrative is {len(body)} chars, over the "
                   f"{NARRATIVE_MAX_CHARS}-char page budget (NARRATIVE RULE)")
    # The section still has to be about this period's catalysts. Checking the literal word
    # "Katalis" would fail good prose (the heading already says it), so the check asks the
    # real question: does the copy mention at least one catalyst the sheet carried?
    names = [str(n) for n in (prov.get("catalyst_names") or [])]
    if names:
        mentioned = 0
        for name in names:
            words = [w.lower() for w in re.findall(r"[A-Za-z]{5,}", name)]
            if any(w in low for w in words):
                mentioned += 1
        if not mentioned:
            out.append("paragraph 2: written narrative mentions none of the period's catalysts "
                       "- the section mandate still binds (NARRATIVE RULE)")
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
            f"cover copy is {total} chars, over the {COVER_COPY_BUDGET}-char one-page budget - "
            "the Key Financials exhibit will be pushed off page 1 and the layout contract breaks"
        ]
    return []


#: PLAIN-LANGUAGE RULE denylist: method-jargon tokens that must never reach a
#: lay-reader surface (highlights, P1, thesis rail, risk details). The P3
#: valuation paragraph keeps its gate-pinned markers and valuation/audit pages
#: keep precise terms - those surfaces are never scanned, by design.
#:
#: AWAM RULE (owner, 19 Sep 2026, page-1 readability pass): the first block on the cover is
#: the first thing a lay reader meets, and tokens that are really CODE were still getting
#: through - "Basis Q1-2026: pendapatan ...", "Jalur FY26F-28F", "Cluster-buy direksi",
#: "sinyal keyakinan insider", "vs mid-cycle", "re-rating". Those read as plumbing, so they
#: join the denylist alongside the method jargon. Two shapes need a pattern rather than a
#: literal: fiscal-year tags (FY26F) and compact quarter tags (Q1-2026) - the plain forms are
#: "2026" / "2026-2028" and "Kuartal I 2026". Terms the owner keeps in English because the
#: market uses them (EBITDA, Priced-in, BUY/SELL/HOLD, DCF, WACC) stay, but they must be
#: glossed in plain words the first time they appear.
PLAIN_JARGON = (
    "CAGR", "deleveraging", "Deleveraging", "re-rating", "Re-rating",
    "fresh ore", "Fresh ore", "anchor EV", "anchor ", "Anchor ",
    "TTM print", "print 20", "capex", "Capex", "Upside", "upside",
    "FCF", "qoq", "QoQ", "yoy ", "YoY ",
    # AWAM RULE additions (19 Sep 2026)
    "Basis ", "mid-cycle", "Mid-cycle", "Cluster-buy", "cluster-buy",
    "insider", "Insider", "Rebalancing", "rebalancing", "run-rate", "Run-rate",
    "kualitatif", "Kualitatif", "multiple", "Multiple", "exit multiple",
    # the mirror of "upside": the P3 rewrite dropped it, so the list must catch it coming back
    "downside", "Downside",
)

#: Code-shaped tokens caught by pattern (the literal list cannot enumerate year/quarter tags).
PLAIN_JARGON_PATTERNS = (
    r"FY\d{2}F",
    r"\bQ[1-4][- ]20\d\d\b",
)

#: Paragraph 3's own mandate requires four markers verbatim, two of which are ON the jargon
#: list ("CAGR" and the FY tag). They are carved out by name before P3 is scanned - the
#: mandate wins - and the carve-out is written down here so it cannot quietly grow.
VALUASI_MANDATE_TOKENS = ("CAGR EBITDA FY26F-FY28F", "FY26F-FY28F", "CAGR")


def _plain_scan_text(text: str, carve_outs: tuple[str, ...] = ()) -> str:
    """The text as the jargon scan sees it: the mandated markers removed, nothing else."""
    out = text
    for token in carve_outs:
        out = out.replace(token, " ")
    return out


def audit_plain_language(payload: Optional[dict]) -> list[str]:
    """Reader-facing copy stays plain Indonesian (PLAIN-LANGUAGE RULE).

    Scans only lay surfaces: the cover theme title, cover highlights, P1+P2 bodies, the P1
    heading, thesis headlines/details/labels, and risk details. A hit names the surface and the
    token so the fix is mechanical (translate the wrapping, keep the figure). P3 (valuation)
    joined the set with its four mandated markers carved out by name (VALUASI_MANDATE_TOKENS);
    valuation/audit pages stay out of scope.

    AWAM RULE (19 Sep 2026): the theme title joined the scanned set - it is the headline a lay
    reader meets first, and it carried exactly the tokens this rule exists to stop
    ("Multiple 2026 di 18,38× vs mid-cycle 28,42× - re-rating belum tercermin dalam harga").
    """
    fields: list[tuple[str, str]] = []
    p = payload or {}
    cover = p.get("cover") or {}
    s1 = cover.get("slide1") or {}
    fields.append(("cover theme title", _text(s1.get("theme_title"))))
    for i, h in enumerate(s1.get("highlights") or [], 1):
        fields.append((f"highlight {i}", _text(h)))
    fp = s1.get("financial_para") or {}
    fields.append(("P1 body", _text(fp.get("body"))))
    fields.append(("P1 heading", _text(fp.get("heading"))))
    fields.append(("P2 body", _text((cover.get("slide2") or {}).get("katalis", {}).get("body"))))
    # P3 joined the scanned set on the owner's call ("bungkus juga, biar enak bacanya"), with the
    # four mandated markers carved out by name - see VALUASI_MANDATE_TOKENS.
    fields.append(("P3 body", _plain_scan_text(
        _text((cover.get("slide2") or {}).get("valuasi", {}).get("body")), VALUASI_MANDATE_TOKENS)))
    for i, t in enumerate(p.get("thesis") or [], 1):
        if isinstance(t, dict):
            fields.append((f"thesis {i} headline", _text(t.get("headline"))))
            fields.append((f"thesis {i} detail", _text(t.get("detail"))))
            fields.append((f"thesis {i} label", _text(t.get("stat_label"))))
    for r in p.get("risks") or []:
        if isinstance(r, dict):
            fields.append((f"risk {str(r.get('bucket') or '?')}", _text(r.get("detail"))))
    violations: list[str] = []
    for surface, text in fields:
        for token in PLAIN_JARGON:
            if token and token in text:
                violations.append(
                    f"{surface} uses method jargon {token!r} - translate the wrapping "
                    f"(PLAIN-LANGUAGE RULE), keep the figure"
                )
                break
        else:
            for pat in PLAIN_JARGON_PATTERNS:
                m = re.search(pat, text)
                if m:
                    violations.append(
                        f"{surface} uses the code-shaped tag {m.group(0)!r} - write the plain "
                        f"form instead (PLAIN-LANGUAGE RULE): 2026-2028, Kuartal I 2026"
                    )
                    break
    return violations


# ------------------------------------------------------------------ §9 Key Financials
def audit_key_financials(kf: Optional[dict]) -> list[str]:
    out: list[str] = []
    kf = kf or {}
    if not kf:
        return ["Key Financials exhibit missing from the cover"]
    headers = [_text(h) for h in (kf.get("headers") or [])]
    if headers[:1] != [KF_HEADER_FIRST]:
        out.append(f"Key Financials first header cell is {headers[:1]} - expected "
                   f"{KF_HEADER_FIRST!r}")
    if tuple(headers[1:]) != KF_COLUMNS:
        out.append(f"Key Financials columns are {headers[1:]} - expected two actuals and "
                   f"three forecasts {list(KF_COLUMNS)}")
    # The forecast columns must say WHERE they came from. An unlabelled forecast reads as the house's own.
    basis = str(kf.get("forecast_basis") or "")
    notes_blob = " ".join(str(n) for n in (kf.get("notes") or [])).lower()
    if not basis:
        out.append("Key Financials does not declare a forecast basis for the FY26F-FY28F columns")
    elif basis == "third-party-estimate":
        if not kf.get("forecast_attribution") or not kf.get("forecast_as_of"):
            out.append("Key Financials uses a third-party path without attribution/as-of - the reader "
                       "cannot tell whose estimate is on the page")
        # The page presents the path as the team's own estimate over the licensed dataset, so it must not
        # read as realised figures; the origin is traced in docs/ammn-slides/forecast-inputs-provenance.md.
        if not any(k in notes_blob for k in ("estimasi tim", "proyeksi", "bukan realisasi")):
            out.append("Key Financials' forecast columns come from estimates but the note never says the "
                       "columns are a projection - they would read as realised figures")
    elif basis == "midcycle-normalised" and "normalised" not in notes_blob:
        out.append("Key Financials columns are a normalised mid-cycle level but the note does not say "
                   "'normalised' - a flat level would read as a growth forecast")
    elif basis == "invalid-driver-file":
        names = "; ".join(str(p) for p in (kf.get("forecast_problems") or []))
        out.append(f"Key Financials fell back because its forecast path file is unusable: {names}")
    labels = [_text(r[0]) for r in _rows_of(kf)]
    if len(labels) != len(KF_ROWS):
        out.append(f"Key Financials has {len(labels)} rows - expected {len(KF_ROWS)}")
    for expected, got in zip(KF_ROWS, labels):
        if not got.startswith(expected):
            out.append(f"Key Financials row {got!r} where {expected!r} was expected (order is "
                       "part of the contract)")
    # units belong in the row labels once the column caption is a date
    for row in _rows_of(kf):
        label = _text(row[0])
        if label in KF_ROWS and label in ("Revenue", "EBITDA", "Net Profit"):
            out.append(f"Key Financials row {label!r} carries no unit - with a "
                       f"{KF_HEADER_FIRST!r} caption every Rp figure needs (Rpbn) in its label")
    # negatives read (28,8) in a house table, never -28,8
    for row in _rows_of(kf):
        for cell in row[1:]:
            if _text(cell).startswith("-"):
                out.append(f"Key Financials {_text(row[0])!r} prints {cell!r} - negative values "
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
                out.append(f"Key Financials {label!r} shows {cell!r} - absolute Rp figures carry "
                           "no decimals")
            elif not is_rpbn and digits != 1:
                out.append(f"Key Financials {label!r} shows {cell!r} - percentages, multiples and "
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

    Four quadrants, each a chart that carries its own narrative block - the spec is explicit that the
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
    if text in ("", "-", "-", "n/a", "N/A"):
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


def _audit_ddm_page(page: dict) -> list[str]:
    """Opsi B (DDM) half of deck slide 4: dividend rows, Cost of Equity discounting, and the payout
    consistency test the rules' narrative section asks for."""
    violations: list[str] = []
    periods = [str(p) for p in (page.get("periods") or [])]
    if len(periods) != 5:
        violations.append("slide 4 (DDM) must project five explicit periods")
    rows = (page.get("blocks") or {}).get("build_up") or {}
    for name in ("Net Profit", "Payout Ratio (%)", "DPS", "DPS growth (%)",
                 "Discount factor (Cost of Equity)", "PV of DPS"):
        series = rows.get(name)
        if series is None:
            violations.append(f"slide 4 (DDM) is missing the '{name}' row the rules require")
        elif len(series) != len(periods):
            violations.append(f"slide 4 (DDM) row '{name}' has {len(series)} values against {len(periods)} periods")
    if not any(abs(v or 0) > 0 for v in (rows.get("DPS") or [])):
        violations.append("slide 4 (DDM) has no dividend per share to discount")
    coe_rows = [r for r in (page.get("wacc_rows") or []) if "cost of equity" in str(r[0]).lower()]
    if not coe_rows:
        violations.append("slide 4 (DDM) Exhibit 9 must state the Cost of Equity it discounts with")
    for row in coe_rows:
        if len(row) < 3 or not str(row[2]).strip():
            violations.append("slide 4 (DDM) gives a Cost of Equity without naming its source")
    stated = " ".join(
        [str(r[0]) + " " + str(r[1]) + " " + str(r[2]) for r in (page.get("wacc_rows") or [])]
        + [str(n) for n in (page.get("notes") or [])]
        + [str(page.get("subtitle") or "")]
    ).lower()
    if not ("cost of equity" in stated and "wacc" in stated):
        violations.append("slide 4 (DDM) does not state that the discount rate is the Cost of Equity, not WACC")
    bridge = page.get("bridge") or {}
    if bridge.get("fv_gordon") is None:
        violations.append("slide 4 (DDM) has no fair value per share")
    if not any("payout" in str(n).lower() for n in (page.get("notes") or [])):
        violations.append("slide 4 (DDM) must test payout sustainability, as the rules' narrative section requires")
    if bridge.get("fv_exit") is None and not any("inverse" in str(n).lower() for n in (page.get("notes") or [])):
        violations.append("slide 4 (DDM) neither shows the Inverse Cost of Equity path nor explains its absence")
    sensitivity = page.get("sensitivity") or {}
    grid = sensitivity.get("fair_value")
    cells = len([v for row in grid.values.tolist() for v in row if v is not None]) if grid is not None and hasattr(grid, "values") else 0
    if cells == 0 or cells != (len(sensitivity.get("wacc_axis") or []) * len(sensitivity.get("g_axis") or [])):
        violations.append("slide 4 (DDM) Exhibit 10 must fill every cell")
    if sensitivity.get("base") is None:
        violations.append("slide 4 (DDM) Exhibit 10 must mark the base case")
    return violations


def _audit_rnav_page(page: dict) -> list[str]:
    """Opsi C (RNAV) half of deck slide 4: valued asset by asset, with the discount justified or declared
    as pure judgment."""
    violations: list[str] = []
    assets = page.get("assets") or []
    if not assets:
        violations.append("slide 4 (RNAV) renders without a single asset row")
    for asset in assets:
        name = str(asset.get("name") or "?")
        if asset.get("nav") is None:
            violations.append(f"slide 4 (RNAV) asset '{name}' has no NAV per aset")
        if asset.get("ownership") is None:
            violations.append(f"slide 4 (RNAV) asset '{name}' has no ownership share")
        if asset.get("nav_attributable") is None:
            violations.append(f"slide 4 (RNAV) asset '{name}' has no attributable NAV")
        source = str(asset.get("nav_source") or "").strip()
        if not source or source == "sumber tidak dicantumkan":
            violations.append(f"slide 4 (RNAV) asset '{name}' does not name where its NAV comes from")
        elif "sectors" not in source.lower():
            violations.append(
                f"slide 4 (RNAV) asset '{name}' takes its NAV from outside Sectors ('{source[:40]}'); the "
                "project rule allows Sectors data only"
            )
    bridge = page.get("bridge") or {}
    for key, label in (("sum_nav", "sum of NAV"), ("total_rnav", "total RNAV"),
                       ("rnav_per_share", "RNAV per share"), ("target_price", "target price")):
        if bridge.get(key) is None:
            violations.append(f"slide 4 (RNAV) bridge has no {label}")
    if bridge.get("discount") is None:
        violations.append("slide 4 (RNAV) does not state the discount to RNAV")
    notes = [str(n).lower() for n in (page.get("notes") or [])]
    if not any("judgment" in n or "pembanding" in n for n in notes):
        violations.append(
            "slide 4 (RNAV) must either cite a comparable discount level or declare the discount a pure "
            "judgment assumption (rules for Opsi C)"
        )
    rows = page.get("block1_rows") or []
    if len(rows) != len(assets):
        violations.append("slide 4 (RNAV) asset table does not list every asset")
    return violations

def audit_valuation_page(page: dict | None, payload: dict | None = None) -> list[str]:
    """Deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md).

    Checks the three exhibits the rules define, and - because the rules make it mandatory - that a
    material gap between the terminal methods is DISCLOSED rather than averaged away. An empty page is
    not applicable: a ticker whose assumptions carry no WACC has no intrinsic page to audit.
    """
    if not isinstance(page, dict) or not page or not page.get("available"):
        return []
    if str(page.get("method") or "dcf") == "ddm":
        return _audit_ddm_page(page)
    if str(page.get("method") or "dcf") == "rnav":
        return _audit_rnav_page(page)
    violations: list[str] = []
    periods = [str(p) for p in (page.get("periods") or [])]

    if len(periods) != 5:
        violations.append("slide 4 must project five explicit periods (rules: 5 tahun)")

    build = ((page.get("blocks") or {}).get("build_up") or {})
    required_rows = (
        "Revenue", "EBIT", "Tax on EBIT", "NOPAT", "(+) D&A", "(-) Capex",
        "(-/+) Delta NWC", "FCFF (build-up)", "FCFF growth (%)", "Discount factor", "PV of FCFF",
    )
    for name in required_rows:
        series = build.get(name)
        if series is None:
            violations.append(f"slide 4 block 1 is missing the '{name}' row the rules require")
        elif len(series) != len(periods):
            violations.append(f"slide 4 row '{name}' has {len(series)} values against {len(periods)} periods")
    fcff = [v for v in (build.get("FCFF (build-up)") or []) if v is not None]
    if not fcff or not any(abs(v) > 0 for v in fcff):
        violations.append("slide 4 block 1 has no usable FCFF line")

    bridge = page.get("bridge") or {}
    for key, label in (
        ("pv_explicit", "sum of PV of FCFF"), ("pv_tv_gordon", "PV of terminal value"),
        ("ev_gordon", "enterprise value"), ("equity_gordon", "equity value"),
        ("fv_gordon", "fair value per share"),
    ):
        if bridge.get(key) is None:
            violations.append(f"slide 4 block 3 has no {label}")
    if bridge.get("tv_exit") is None:
        violations.append(
            "slide 4 block 2 shows a single terminal method; the rules ask for Gordon and the exit "
            "multiple side by side when both are computed"
        )

    wacc_rows = page.get("wacc_rows") or []
    if len(wacc_rows) < 8:
        violations.append("slide 4 Exhibit 9 must break the WACC into its components (risk-free, beta, ERP, CoE, Kd, tax, after-tax Kd, weights, WACC)")
    for parameter in ("risk-free", "beta", "equity risk premium"):
        row = next((r for r in wacc_rows if parameter in str(r[0]).lower()), None)
        if row is None:
            violations.append(f"slide 4 Exhibit 9 does not state the {parameter} parameter")
        elif len(row) < 3 or not str(row[2]).strip():
            violations.append(f"slide 4 Exhibit 9 gives {parameter} without naming its source")

    sensitivity = page.get("sensitivity") or {}
    grid = sensitivity.get("fair_value")
    cells = 0
    if grid is not None and hasattr(grid, "values"):
        cells = len([v for row in grid.values.tolist() for v in row if v is not None])
    if cells != (len(sensitivity.get("wacc_axis") or []) * len(sensitivity.get("g_axis") or [])) or cells == 0:
        violations.append("slide 4 Exhibit 10 must fill every sensitivity cell; a partial grid invites the reader to trust a gap")
    if sensitivity.get("base") is None:
        violations.append("slide 4 Exhibit 10 must mark the base case cell (rules: highlight warna beda)")

    notes = page.get("notes") or []
    if not notes:
        violations.append("slide 4 carries no disclosure block")
    gap = None
    if bridge.get("fv_gordon") and bridge.get("fv_exit") and bridge["fv_gordon"] > 0:
        gap = max(bridge["fv_exit"], bridge["fv_gordon"]) / min(bridge["fv_exit"], bridge["fv_gordon"])
    if gap is not None and gap >= 2.0:
        if not any("UNRESOLVED" in str(n).upper() for n in notes):
            violations.append(
                f"the two terminal methods differ {_nf.dec(gap, digits=1)}× and the page does not flag it as an "
                "unresolved assumption (rules: wajib di-flag eksplisit, bukan dirata-rata diam-diam)"
            )
    if not any("reserve" in str(n).lower() or "perpetual" in str(n).lower() for n in notes):
        violations.append("slide 4 does not disclose the perpetual-growth limitation on a depleting reserve")

    subtitle = str(page.get("subtitle") or "")
    if "DDM" not in subtitle or "RNAV" not in subtitle:
        violations.append("slide 4 does not state why the other two methods were excluded (the choice is the analyst's and must be auditable)")

    return violations


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
        violations += audit_katalis((slide2.get("katalis") or {}).get("body", ""),
                                    written=str((slide2.get("katalis") or {}).get(
                                        "narrative_source") or "") == "writer_frozen")
        # A paragraph 2 that a language model wrote is checked against its own fact sheet.
        violations += audit_katalis_narrative(slide2.get("katalis") or {})
        violations += audit_valuasi((slide2.get("valuasi") or {}).get("body", ""))
        violations += audit_copy_budget([
            (slide1.get("financial_para") or {}).get("body", ""),
            (slide2.get("katalis") or {}).get("body", ""),
            (slide2.get("valuasi") or {}).get("body", ""),
        ])
        violations += audit_plain_language(payload)
        violations += audit_key_financials(slide2.get("key_financials") or {})
    # Slide 2 of the deck is audited regardless of the cover spread: it is its own page.
    violations += audit_industry_page(payload.get("industry_page"), payload)
    # Slide 3 of the deck is its own page as well.
    violations += audit_performance_page(payload.get("performance_page"), payload)
    violations += audit_valuation_page(payload.get("valuation_page"), payload)
    # Slide 5 of the deck is its own page as well.
    violations += audit_peer_page(payload.get("peers_page"), payload)
    # Slide 6 of the deck is its own page as well.
    violations += audit_statements_page(payload.get("statements_page"), payload)
    # Slide 7: the cash flow and the ratio block, with their tie-outs.
    violations += audit_cashflow_page(payload.get("cashflow_page"), payload)
    violations += audit_key_ratio_page(payload.get("key_ratio_page"), payload)
    # No third-party research house is named on a printed page.
    violations += audit_source_independence(payload)
    # One number format across the deck.
    violations += audit_number_format(payload)
    # Slide 4: a priced leg must state which level and which multiple produced it, and what was rejected.
    # The instruction rule says so; this makes it enforced rather than optional.
    vnotes = " ".join(str(n) for n in ((payload.get("valuation_page") or {}).get("notes") or []))
    vrows = " ".join(str(c) for r in (((payload.get("valuation") or {}).get("midcycle") or {}).get("rows") or [])
                     for c in r)
    if (payload.get("valuation_page") or {}).get("available"):
        if "BASIS MULTIPLE" not in vnotes and "basis TP" not in vrows:
            violations.append("slide 4 valuation does not state the basis of the level and the multiple "
                              "behind the target price (level, multiple, source, as-of)")
        if "DITOLAK" not in vnotes and "tidak dipakai" not in vrows:
            violations.append("slide 4 valuation names no rejected basis - a silent rejection reads as "
                              "never considered")
    return {
        "ok": not violations,
        "applicable": applicable,
        "violations": violations,
        "sections": [
            "7-cover",
            "8-paragraphs",
            "9-key-financials",
            "slide2-industry",
            "slide3-performance", "slide4-valuation", "slide5-peers", "slide6-statements", "slide7-cashflow-ratio", "source-independence", "number-format",
        ],
        "copy_chars": sum(len(_text(b)) for b in (
            (slide1.get("financial_para") or {}).get("body", ""),
            (slide2.get("katalis") or {}).get("body", ""),
            (slide2.get("valuasi") or {}).get("body", ""),
        )),
        "copy_budget": COVER_COPY_BUDGET,
    }


def audit_peer_page(page: dict | None, payload: dict | None = None) -> list[str]:
    """Deck slide 5 (docs/ammn-slides/slide5-peer-spec.md).

    The rules put two methodologies on one page and demand they stay distinguishable, so this gate
    checks each half against its own contract and then checks the ONE thing that keeps them honest:
    when the cross-sectional read and the time-series read point in different directions, the page has
    to say so instead of letting the reader assume they confirm each other.
    """
    if page is None or page == {}:
        # not applicable: a ticker whose deck has no slide-5 data never had this page
        return []
    if not isinstance(page, dict) or not page.get("available"):
        return ["slide 5 has no peers page available - the page cannot be silently dropped"]
    violations: list[str] = []
    a = page.get("part_a") or {}
    b = page.get("part_b") or {}

    # ---- Part A: the peer table -------------------------------------------
    cols = [str(c).lower() for c in (a.get("columns") or [])]
    for required in ("p/e", "p/bv", "ev/ebitda"):
        if not any(required in c for c in cols):
            violations.append(f"slide 5 peer table is missing the '{required}' column the rules require")
    rows = a.get("rows") or []
    if len(rows) < 3:
        violations.append(f"slide 5 peer table carries only {len(rows)} rows - a peer set needs comparables")
    covered = [r for r in rows if r.get("is_covered")]
    if not covered:
        violations.append("slide 5 peer table does not flag the covered issuer's row (rules: highlight)")
    for key in ("median", "average"):
        stat = a.get(key) or {}
        if not stat:
            violations.append(f"slide 5 peer table is missing the {key.upper()} closing row (rules: dua baris terpisah)")
    if a.get("median") and a.get("average") and a["median"].get("pe") == a["average"].get("pe"):
        violations.append("slide 5 median and average rows are identical - they must be two separate rows")
    # the statistics must be reproducible from the printed rows
    pe_vals = sorted(r["pe"] for r in rows if not r.get("is_covered") and r.get("pe") is not None)
    med = a.get("median") or {}
    if pe_vals and med.get("pe") is not None:
        n = len(pe_vals)
        expect = pe_vals[n // 2] if n % 2 else (pe_vals[n // 2 - 1] + pe_vals[n // 2]) / 2
        if abs(expect - med["pe"]) > 0.02:
            violations.append(f"slide 5 median P/E {_nf.dec(med['pe'], digits=2)} does not match the printed peer rows "
                              f"(recomputed {_nf.dec(expect, digits=2)})")
    if not str(a.get("as_of") or "").strip():
        violations.append("slide 5 peer table states no 'as of' date for the price data it uses")
    if not (a.get("sources") or []):
        violations.append("slide 5 peer table records no data provenance (the rules require a source line)")
    if not (b.get("sources") or []):
        violations.append("slide 5 relative-valuation half records no data provenance")
    criteria = str(a.get("criteria") or "").lower()
    if len(criteria) < 40 or "market cap" not in criteria:
        violations.append("slide 5 peer-selection criteria are not stated (rules: sector + market-cap range + as-of)")
    if not (a.get("narrative") or a.get("narrative_text")):
        violations.append("slide 5 peer table has no narrative positioning the issuer against median/average")
    if any(r.get("pe_nm") for r in rows if not r.get("is_covered")) and "n.m." not in str(a.get("narrative_text", "")):
        violations.append("slide 5 prints an n.m. P/E without disclosing why or that it left the median")

    # ---- Part B: bands + implied price ------------------------------------
    bands = b.get("bands") or []
    if len(bands) < 2:
        violations.append(f"slide 5 shows {len(bands)} band charts - the rules require at least P/E and P/BV")
    have = {blk.get("key") for blk in bands}
    for key, exhibit in (("pe", 12), ("pbv", 13)):
        if key not in have:
            violations.append(f"slide 5 is missing the {key.upper()} band chart (rules: Exhibit {exhibit})")
    for blk in bands:
        label = blk.get("label", "?")
        if not blk.get("series"):
            violations.append(f"slide 5 {label} band has no series")
        for field, why in (("mean", "mean line"), ("median", "median line"), ("current", "current marker")):
            if blk.get(field) is None:
                violations.append(f"slide 5 {label} band is missing its {why}")
        if blk.get("series"):
            last = blk["series"][-1]["value"]
            if blk.get("current") is not None and abs(last - blk["current"]) > 1e-6:
                violations.append(f"slide 5 {label} band current marker is not the last observation")
        narr = str(blk.get("narrative") or "")
        if not narr:
            violations.append(f"slide 5 {label} has no narrative (rules: narasi per chart, bukan satu paragraf)")
        elif "persentil" not in narr.lower():
            violations.append(f"slide 5 {label} narrative does not state the current percentile")
    implied = b.get("implied") or []
    covered_keys = {i["key"]: i for i in implied}
    for key in ("pe", "pbv"):
        row = covered_keys.get(key)
        if not row:
            violations.append(f"slide 5 implied price omits {key.upper()} (rules: minimal P/E dan P/BV)")
            continue
        if row.get("to_mean") is None or row.get("to_median") is None:
            violations.append(f"slide 5 implied {key.upper()} must show both reversion methods as numbers")
        if row.get("is_range") is not True and (row.get("high") or 0) and                 abs(row["high"] - row["low"]) > 0.10 * abs(row["high"]):
            violations.append(f"slide 5 implied {key.upper()} mean and median differ materially but are "
                              f"not presented as a range")
    if not bands:
        pass
    elif not any("persentil" in str(blk.get("narrative", "")).lower() for blk in bands):
        violations.append("slide 5 band narratives never state a percentile")
    disclaimer = str(b.get("disclaimer") or "")
    low = disclaimer.lower()
    if len(disclaimer) < 80:
        violations.append("slide 5 has no implied-price disclaimer (rules: disclaimer eksplisit wajib)")
    elif not any(k in low for k in ("bukan target price", "not the target price", "bukan target harga")):
        violations.append("slide 5 disclaimer does not say the implied prices are NOT the slide-4 target price")

    # ---- the one rule that keeps the two halves honest --------------------
    pe_a = (a.get("median") or {}).get("pe")
    pe_cov = (covered[0].get("pe") if covered else None)
    band_pe = next((blk for blk in bands if blk.get("key") == "pe"), None)
    premium_vs_peers = (pe_cov is not None and pe_a and pe_cov > pe_a * 1.10)
    cheap_vs_self = (band_pe is not None and band_pe.get("percentile") is not None
                     and band_pe["percentile"] < 45)
    if premium_vs_peers and cheap_vs_self:
        joined = (str(a.get("narrative_text", "")) + " " + " ".join(
            str(blk.get("narrative", "")) for blk in bands)).lower()
        if not any(k in joined for k in ("bertentangan", "berbeda arah", "tidak saling mengonfirmasi",
                                         "disagree", "opposite", "berlawanan")):
            violations.append("slide 5 shows a peer premium while its own history reads cheap - the page "
                              "must state that the two readings disagree instead of implying confirmation")
    return violations


def audit_statements_page(page: dict | None, payload: dict | None = None) -> list[str]:
    """Deck slide 6 (docs/ammn-slides/slide6-statements-spec.md): Exhibit 14 + 15.

    The rules fix the row list and the column set, so this gate checks structure; then it checks the two
    things that make the statements trustworthy - that the balance sheet ties EXACTLY, and that every
    figure the model could not source is disclosed rather than printed as a number.
    """
    if page is None or page == {}:
        return []
    if not isinstance(page, dict) or not page.get("available"):
        return ["slide 6 has no statements page available - the page cannot be silently dropped"]
    violations: list[str] = []
    years = [str(y) for y in (page.get("years") or [])]
    if years != ["2024A", "2025A", "2026F", "2027F", "2028F"]:
        violations.append(f"slide 6 columns must be 2024A-2028F, got {years}")

    if str(page.get("variant") or "corporate") == "bank":
        want_in = ("Interest Income", "Interest Expense", "Net Interest Income", "Non-Interest Income",
                   "PPOP", "Provisions")
        want_bs = ("Gross Loans", "Net Loans", "Customer Deposits", "Shareholders' Funds")
    else:
        want_in = ("Revenue / Sales", "Cost of Goods Sold", "Gross Profit", "Operating Expenses",
                   "EBIT", "Interest Income", "Interest Expense", "Other Income", "Pre-tax Profit",
                   "Income Tax", "Minority Interest", "Net Profit")
        want_bs = ("Cash & Cash Equivalents", "Trade Receivables", "Inventory", "Other Current Assets",
                   "Total Current Assets", "Fixed Assets", "Other Non-Current Assets", "Total Assets",
                   "Short-term Debt", "Trade Payables", "Other Current Liabilities",
                   "Total Current Liabilities", "Long-term Debt", "Other Non-Current Liabilities",
                   "Total Liabilities", "Shareholders' Equity", "Total Liabilities & Equity")

    for block_key, wanted, label in (("income", want_in, "Exhibit 14 income statement"),
                                     ("balance", want_bs, "Exhibit 15 balance sheet")):
        block = page.get(block_key) or {}
        rows = [str(r.get("label", "")) for r in (block.get("rows") or [])]
        for name in wanted:
            if not any(r.startswith(name) for r in rows):
                violations.append(f"{label} is missing the '{name}' row the rules require")
        seen: list = []
        for r in rows:
            match = max((i for i, w in enumerate(wanted) if r.startswith(w)),
                        key=lambda i: len(wanted[i]), default=None)
            if match is not None:
                if not seen or seen[-1] != match:
                    seen.append(match)
        if seen != sorted(set(seen)) or sorted(set(seen)) != list(range(len(wanted))):
            got = [wanted[i] for i in seen]
            violations.append(f"{label} rows are out of the order the rules specify (got {got})")
        headers = [str(h) for h in (block.get("headers") or [])]
        if headers[1:] != years:
            violations.append(f"{label} header row does not carry the five year columns")
        for r in block.get("rows") or []:
            vals = r.get("cells") or []
            if len(vals) != len(years):
                violations.append(f"{label} row '{r.get('label')}' has {len(vals)} values against "
                                  f"{len(years)} years")
            if r.get("kind") in ("na",) and not r.get("note"):
                violations.append(f"{label} prints 'n/a' for '{r.get('label')}' without saying why")

    # subtotals must actually foot, and the balance sheet must tie exactly
    def find(block_key: str, label: str) -> dict:
        return next((r for r in ((page.get(block_key) or {}).get("rows") or [])
                     if str(r.get("label", "")).startswith(label)), {})

    for label, kind in (("Gross Profit", "subtotal"), ("EBIT", "subtotal"), ("Pre-tax Profit", "subtotal"),
                        ("Net Profit", "highlight"), ("Total Assets", "subtotal"),
                        ("Total Liabilities & Equity", "subtotal")):
        block_key = "income" if label in ("Gross Profit", "EBIT", "Pre-tax Profit", "Net Profit") else "balance"
        r = find(block_key, label)
        if r and r.get("kind") != kind:
            violations.append(f"slide 6 row '{label}' must be flagged {kind}, got '{r.get('kind') or 'plain'}'")
    for label in ("Cost of Goods Sold", "Operating Expenses", "Interest Expense", "Income Tax"):
        r = find("income", label)
        if r and r.get("kind") != "deduction":
            violations.append(f"slide 6 row '{label}' is a deduction and must be flagged as one")
    # recompute the tie from the rows as printed - a reported tie-out the page could contradict is worthless
    bs_rows = {str(r.get("label", "")): (r.get("cells") or [])
               for r in ((page.get("balance") or {}).get("rows") or [])}
    def longest(prefix: str):
        hits = [(len(k), v) for k, v in bs_rows.items() if k.startswith(prefix)]
        return max(hits)[1] if hits else None

    ta_row = longest("Total Assets")
    tle_row = max([(len(k), v) for k, v in bs_rows.items()
                   if k.startswith("Total Liabilities")], default=None)
    tle_row = tle_row[1] if tle_row else None
    if ta_row and tle_row and len(ta_row) == len(tle_row) == len(years):
        for i, y in enumerate(years):
            if isinstance(ta_row[i], (int, float)) and isinstance(tle_row[i], (int, float)):
                if abs(float(tle_row[i]) - float(ta_row[i])) > 1.0:
                    violations.append(f"slide 6 printed balance sheet does not tie in {y}: "
                                      f"final liabilities+equity row {_nf.idn(float(tle_row[i]), digits=0)} vs "
                                      f"Total Assets {_nf.idn(float(ta_row[i]), digits=0)}")
    tie = page.get("tie_out") or {}
    for y in years:
        gap = tie.get(y)
        if gap is None:
            violations.append(f"slide 6 reports no balance tie-out for {y}")
        elif abs(float(gap)) > 1.0:
            violations.append(f"slide 6 balance sheet does not tie in {y}: Total L&E - Total Assets = "
                              f"{_nf.idn(float(gap), digits=0)}")
    if not page.get("tied"):
        violations.append("slide 6 balance check failed (rules: Total Liabilities & Equity must equal Total Assets)")
    if not (page.get("notes") or []):
        violations.append("slide 6 prints no notes - the reconciling lines and the cash plug must be disclosed")
    notes = " ".join(str(n) for n in (page.get("notes") or [])).lower()
    for needed, why in (("rekonsiliasi", "the residual 'Other income' line must be named as a reconciling item"),
                        ("penyeimbang", "cash as the balance-sheet plug must be stated"),
                        ("dipublikasikan", "unpublished rows must be disclosed as such")):
        if needed not in notes:
            violations.append(f"slide 6 notes are missing the disclosure that: {why}")
    return violations


def audit_cashflow_page(page: dict | None, payload: dict | None = None) -> list[str]:
    """Deck slide 7 (docs/ammn-slides/slide7-cashflow-ratio-spec.md): Exhibit 16 cash flow.

    Structure first, then the tie-outs - this page exists to prove the model's sheets are linked, so a
    mismatch here is a defect, not a rounding difference.
    """
    if page is None or page == {}:
        return []
    if not isinstance(page, dict) or not page.get("available"):
        return ["slide 7 has no cash-flow page available - the page cannot be silently dropped"]
    violations: list[str] = []
    years = [str(y) for y in (page.get("years") or [])]
    if years != ["2024A", "2025A", "2026F", "2027F", "2028F"]:
        violations.append(f"slide 7 columns must be 2024A-2028F, got {years}")

    want = {
        "Cash Flow from Operations": ("Net Profit", "(+) Depreciation & Amortization",
                                      "Increase/Decrease in Working Capital", "Other Operating Items",
                                      "Net Cash from Operations"),
        "Cash Flow from Investing": ("Capital Expenditure", "Other Investing Items",
                                     "Net Cash from Investing"),
        "Cash Flow from Financing": ("Debt Raised/(Repaid)", "Dividends Paid", "Equity Raised/(Buyback)",
                                     "Net Cash from Financing"),
    }
    got_sections = {str(sec.get("title")): [str(r.get("label")) for r in (sec.get("rows") or [])]
                    for sec in (page.get("sections") or [])}
    for title, rows in want.items():
        labels = got_sections.get(title)
        if labels is None:
            violations.append(f"slide 7 is missing the '{title}' section")
            continue
        for needle in rows:
            if not any(needle.lower() in l.lower() for l in labels):
                violations.append(f"{title} is missing the '{needle}' row the rules require")
    for needle in ("Net Change in Cash", "Beginning Cash Balance", "Ending Cash Balance"):
        if not any(needle.lower() in str(r.get("label", "")).lower() for r in (page.get("closing") or [])):
            violations.append(f"slide 7 closing block is missing '{needle}'")
    if not page.get("memo"):
        violations.append("slide 7 has no Free Cash Flow memo line below the divider")

    def find(rows: list, needle: str) -> dict:
        return next((r for r in rows if needle.lower() in str(r.get("label", "")).lower()), {})

    def block(title: str) -> list:
        return next((sec.get("rows") or [] for sec in (page.get("sections") or [])
                     if str(sec.get("title")) == title), [])

    # every subtotal must foot across all five columns
    for title, subtotal, parts in (
            ("Cash Flow from Operations", "Net Cash from Operations",
             ("Net Profit", "Depreciation", "Working Capital", "Other Operating")),
            ("Cash Flow from Investing", "Net Cash from Investing", ("Capital Expenditure", "Other Investing")),
            ("Cash Flow from Financing", "Net Cash from Financing",
             ("Debt Raised", "Dividends Paid", "Equity Raised"))):
        rows = block(title)
        sub = find(rows, subtotal)
        for i in range(len(years)):
            total = sub.get("cells", [None] * 5)[i] if sub else None
            if total is None:
                continue
            parts_sum = 0.0
            present = False
            for needle in parts:
                r = find(rows, needle)
                if r and i < len(r.get("cells") or []):
                    v = r["cells"][i]
                    if isinstance(v, (int, float)):
                        parts_sum += -abs(v) if r.get("kind") == "deduction" else v
                        present = True
            if present and abs(total - parts_sum) > 1.0:
                violations.append(f"{title} does not foot in {years[i]}: subtotal {_nf.idn(total, digits=0)} vs parts "
                                  f"{_nf.idn(parts_sum, digits=0)}")

    # the source's own sections may not foot; if they do not, the reconciliation row must be visible
    net_change = find(page.get("closing") or [], "Net Change")
    begin = find(page.get("closing") or [], "Beginning")
    end = find(page.get("closing") or [], "Ending Cash")
    if net_change and begin and end:
        for i in range(len(years)):
            try:
                left = float(begin["cells"][i]) + float(net_change["cells"][i])
                right = float(end["cells"][i])
            except (TypeError, ValueError, IndexError):
                continue
            gap = right - left
            disclosed = any("selisih" in str(r.get("label", "")).lower() for r in (page.get("closing") or []))
            if abs(gap) > 1.0 and not disclosed:
                violations.append(f"slide 7 closing cash does not reconcile in {years[i]} (gap {_nf.idn(gap, digits=0)}) "
                                  f"and no reconciliation row says why")

    # TIE-OUT 1: the starting line must be the income statement's net profit, and the cover's
    if payload:
        cf_net = find(block("Cash Flow from Operations"), "Net Profit")
        is_net = next((r for r in (((payload.get("statements_page") or {}).get("income") or {}).get("rows")
                                   or []) if str(r.get("label", "")).startswith("Net Profit")), {})
        for i, y in enumerate(years):
            a = (cf_net.get("cells") or [None] * 5)[i] if cf_net else None
            b = (is_net.get("cells") or [None] * 5)[i] if is_net else None
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > 1.0:
                violations.append(f"slide 7 starts from net profit {_nf.idn(a, digits=0)} in {y} while the income "
                                  f"statement prints {_nf.idn(b, digits=0)} - the sheets are not linked")
        # TIE-OUT 2: ending cash == balance-sheet cash, same period
        bs_cash = next((r for r in (((payload.get("statements_page") or {}).get("balance") or {}).get("rows")
                                    or []) if str(r.get("label", "")).startswith("Cash & Cash")), {})
        for i, y in enumerate(years):
            a = (end.get("cells") or [None] * 5)[i] if end else None
            b = (bs_cash.get("cells") or [None] * 5)[i] if bs_cash else None
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(a - b) > max(1.0, abs(b) * 0.001):
                    violations.append(f"slide 7 ending cash {_nf.idn(a, digits=0)} vs balance-sheet cash {_nf.idn(b, digits=0)} in {y} - "
                                      f"above the 0.1% the rules allow, so the sheets are not linked")
    # TIE-OUT 3: the FCF memo must be OCF minus capex, and the FCFF gap must be explained
    memo = (page.get("memo") or [{}])[0]
    ocf = find(block("Cash Flow from Operations"), "Net Cash from Operations")
    capex = find(block("Cash Flow from Investing"), "Capital Expenditure")
    for i in range(len(years)):
        try:
            want = float(ocf["cells"][i]) + float(capex["cells"][i])
            got = float(memo["cells"][i])
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        if abs(want - got) > 1.0:
            violations.append(f"slide 7 FCF memo does not equal OCF - capex in {years[i]} "
                              f"({_nf.idn(got, digits=0)} vs {_nf.idn(want, digits=0)})")
    fcff = page.get("fcff_exhibit8")
    if fcff:
        fcf26 = memo["cells"][2] if len(memo.get("cells") or []) > 2 else None
        if isinstance(fcf26, (int, float)) and abs(fcf26 - fcff) / abs(fcff) > 0.6:
            if not any("cross-check fcff" in str(n).lower() for n in (page.get("notes") or [])):
                violations.append("slide 7 FCF is more than 60% away from the FCFF the DCF leg uses and "
                                  "the page does not investigate it in print")
    if not (page.get("notes") or []):
        violations.append("slide 7 prints no tie-out notes")
    return violations


def audit_key_ratio_page(page: dict | None, payload: dict | None = None) -> list[str]:
    """Deck slide 7 (Exhibit 17): the ratio block, recomputed from the exhibits on the same page."""
    if page is None or page == {}:
        return []
    if not isinstance(page, dict) or not page.get("available"):
        return ["slide 7 has no key-ratio page available - the page cannot be silently dropped"]
    violations: list[str] = []
    want = {
        "Growth (%)": ("Sales", "EBITDA", "Operating Profit", "Net Profit"),
        "Profitability (%)": ("Gross Margin", "EBITDA Margin", "Operating Margin", "Net Margin", "ROAA",
                              "ROAE"),
        "Leverage": ("Net Gearing (x)", "Interest Coverage (x)"),
    }
    sections = {str(sec.get("title")): sec.get("rows") or [] for sec in (page.get("sections") or [])}
    for title, rows in want.items():
        got = [str(r.get("label")) for r in sections.get(title, [])]
        if not got:
            violations.append(f"Exhibit 17 is missing the '{title}' section")
            continue
        for needle in rows:
            if not any(needle.lower() in l.lower() for l in got):
                violations.append(f"{title} is missing the '{needle}' row")
    for title, rows in sections.items():
        for r in rows:
            cells = r.get("cells") or []
            if not any(isinstance(c, (int, float)) for c in cells):
                violations.append(f"Exhibit 17 row '{r.get('label')}' is n/a in every column - an exhibit "
                                  f"of blanks is not an exhibit")
    if payload:
        is_rows = {str(r.get("label", "")).split(" /")[0].split(" (")[0].strip(): r.get("cells") or []
                   for block in ("income", "balance")
                   for r in (((payload.get("statements_page") or {}).get(block) or {}).get("rows") or [])}

        def sheet(needle: str, i: int):
            row = next((v for k, v in is_rows.items() if k.lower().startswith(needle.lower())), None)
            return row[i] if row and i < len(row) and isinstance(row[i], (int, float)) else None

        def printed(title: str, needle: str, i: int):
            for r in sections.get(title, []):
                if needle.lower() in str(r.get("label")).lower():
                    cells = r.get("cells") or []
                    return cells[i] if i < len(cells) else None
            return None

        for i, y in enumerate(page.get("years") or []):
            rev, ebitda, op, net = (sheet("Revenue", i), sheet("EBITDA", i), sheet("EBIT", i),
                                    sheet("Net Profit", i))
            checks = (
                ("Gross Margin", sheet("Gross Profit", i), rev),
                ("EBITDA Margin", ebitda, rev),
                ("Operating Margin", op, rev),
                ("Net Margin", net, rev),
            )
            for label, num, den in checks:
                got = printed("Profitability (%)", label, i)
                want_v = (num / den * 100) if (isinstance(num, (int, float)) and den) else None
                if got is not None and want_v is not None and abs(got - want_v) > 0.15:
                    violations.append(f"Exhibit 17 {label} prints {_nf.dec(got, digits=1)}% in {y} but the income statement "
                                      f"implies {_nf.dec(want_v, digits=1)}%")
            got_cov = printed("Leverage", "Interest Coverage", i)
            eb, intr = sheet("EBIT", i), sheet("Interest Expense", i)
            if got_cov is not None and isinstance(eb, (int, float)) and intr:
                if abs(got_cov - eb / intr) > 0.05:
                    violations.append(f"Exhibit 17 interest coverage {_nf.dec(got_cov, digits=2)}× in {y} does not equal "
                                      f"EBIT/interest {_nf.dec(eb / intr, digits=2)}×")
            got_gear = printed("Leverage", "Net Gearing", i)
            st, lt, cash, eq = (sheet("Short-term Debt", i), sheet("Long-term Debt", i),
                                sheet("Cash & Cash", i), sheet("Shareholders'", i))
            if got_gear is not None and None not in (st, lt, cash, eq) and eq:
                want_g = ((st + lt) - cash) / eq
                if abs(got_gear - want_g) > 0.02:
                    violations.append(f"Exhibit 17 net gearing {_nf.dec(got_gear, digits=2)}× in {y} does not equal "
                                      f"(debt - cash)/equity {_nf.dec(want_g, digits=2)}×")
    return violations


def audit_source_independence(payload: dict | None) -> list[str]:
    """The deck cites the licensed dataset, the issuer's filings, public news and the team's own estimates.

    No other research house is named anywhere a page prints. The calibration trail for the forecast inputs
    lives in the repo (docs/ammn-slides/forecast-inputs-provenance.md), not on the page - so this checks the
    positions a reader can actually see, and the attribution form in free text, without failing on a news
    wire that reports which broker was buying (that is published flow data, not a citation of someone's
    analysis).
    """
    if not isinstance(payload, dict):
        return []
    from server.report.forecast_path import RESEARCH_HOUSE_PATTERN

    out: list[str] = []
    attribution_form = re.compile(
        r"(" + RESEARCH_HOUSE_PATTERN.pattern + r")\s*[,\-–-]?\s*"
        r"(equity research|research|sekuritas|securities|initiation|insight|report)\b", re.I)
    attr_keys = re.compile(r"(attribution|source|sumber|basis|dikutip|provenance|cite)", re.I)

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).endswith("_internal"):
                    continue                       # the internal trail keeps the citation on purpose
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and node.strip():
            key = path.split(".")[-1].split("[")[0]
            if attr_keys.search(key):
                hit = RESEARCH_HOUSE_PATTERN.search(node) or attribution_form.search(node)
                if hit:
                    out.append(f"a printed source label names another research house ({hit.group(0).strip()!r} "
                               f"at {path}) - the deck cites the licensed dataset, filings, news and team "
                               f"estimates only")
            elif attribution_form.search(node):
                hit = attribution_form.search(node)
                out.append(f"the page text cites another research house's work ({hit.group(0).strip()!r} at "
                           f"{path})")

    walk(payload, "")
    return out[:12]

def audit_number_format(payload: dict | None) -> list[str]:
    """One number format per deck: dot thousands, comma decimals.

    A dot with one or two digits behind it is an English decimal, and the deck is written in Indonesian - so
    `43.04` next to `17,99` reads as sloppiness at best and as a hundred-fold error at worst. Three digits after
    the dot is a thousands group and stays allowed, as do dates and domain names.
    """
    if not isinstance(payload, dict):
        return []
    import re as _re

    english_decimal = _re.compile(r"(?<![\d.])\d+\.\d{1,2}(?![\d])")
    # `17,99x` reads as a typo next to `17,99×`; the letter x is also how a unit is spelled ("x (bar)"), so the
    # rule only fires when a figure sits directly in front of it.
    ascii_multiple = _re.compile(r"(?<![\w,.])\d+(?:[.,]\d+)?\s?x(?![a-zA-Z0-9(])")
    allowed = _re.compile(r"(sectors\.app|sectors\.|www\.|@|^\(?\d{1,2}\.\d{1,2}\)?$)")
    out: list[str] = []

    # Its own violation messages quote the offending figure, and a news headline is quoted source text: the
    # deck does not restyle what somebody else wrote, so both are skipped here.
    quoted = ("news", "house_rules")

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                key = str(k)
                if key.endswith("_internal") or (not path and key in quoted):
                    continue
                walk(v, f"{path}.{k}" if path else key)
        elif isinstance(node, (list, tuple)):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and node.strip():
            text = node.strip()
            if allowed.search(text):
                return
            m = english_decimal.search(text)
            if m:
                out.append(f"a printed figure uses an English decimal separator ({m.group(0)!r} at {path}) - "
                           f"the deck prints dot thousands and comma decimals")
            m = ascii_multiple.search(text)
            if m:
                out.append(f"a printed figure uses the ASCII letter x as a multiplication sign ({m.group(0)!r} at "
                           f"{path}) - the deck writes ×")

    walk(payload, "")
    return out[:10]
