"""Friend-supplied generator rules (v3 system prompt) as DETERMINISTIC checks.

Ruleset: `docs/rules/friend-system-prompt-v3.md` (handed over Sep 2026). Reconciliation, i.e.
which arms are adopted, which are amended and which are declined with a reason:
`docs/rules/friend-system-prompt-v3-reconciliation.md`.

Only the arms that can be decided from the render payload are implemented here. The ruleset
also carries architecture and language instructions (one model staging intake, forecast,
valuation and narration top to bottom, with Indonesian body copy); those contradict owner
decisions taken on this project and are recorded as declined, not implemented.

Rule ids follow the ruleset's own numbering so a violation can be traced back to its clause:

    G1.1  period freshness      - a report older than 45 days after a period close must use
                                  that period, or say on the page that it cannot
    G1.2  unit scale            - one declared unit per table, and the same metric must agree
                                  across the surfaces that print it
    G2.2  margin sanity         - a forecast margin above the issuer's own record needs a
                                  stated driver in the narrative that owns it
    G2.3  operating leverage    - a printed price/demand sensitivity must carry the
                                  margin-implied elasticity, never a flat pass-through
    G2.6  forecast variation    - no two consecutive forecast years with identical levels
    G3.4  scenario ladder       - the downside must price below the base case, the upside above
    G4.2  currency discipline   - one currency, and no country risk premium added twice
    G5.2  headline caps         - thesis title, headline paragraph and bullets fit their
                                  word budgets; a title that is a statistic is not a thesis
    G5.3  catalyst curation     - every printed catalyst clears the curation score, the caps
                                  hold, and an insider item below the materiality floor is
                                  reported as a net direction instead of a single trade

Every check returns human-readable violations; an empty list means compliant. Checks never
raise: a missing section is a violation or nothing at all, never an exception.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date as _date
from typing import Any, Iterable, Optional

# --- rule constants (kept here so a clause change is one edit) --------------------------------
STALE_AFTER_DAYS = 45            # G1.1: after a period closes, that period must be available
MARGIN_TOLERANCE_PP = 2.0        # G2.2: above the record by more than this needs a driver
FLAT_TOLERANCE = 0.005           # G2.6: 0.5% relative counts as "the same number"
CROSS_SURFACE_TOLERANCE = 0.01   # G1.2: 1% between two surfaces printing one metric
INSIDER_MATERIALITY_PCT = 0.5    # G5.3: below this share of the float, one trade is not news
CATALYST_SCORE_FLOOR = 7         # G5.3: sum of the four 0-3 axes
CATALYST_TABLE_MAX = 7           # G5.3: the catalyst table prints at most this many
CATALYST_COVER_MAX = 3           # G5.3: the cover thesis paragraph names at most this many
TITLE_MAX_WORDS = 10             # G5.2
HEADLINE_MAX_WORDS = 9           # G5.2
BULLET_MAX_WORDS = 30            # G5.2
MAX_NUMBERS_PER_SENTENCE = 3     # G5.2

# The Key Financials contract lives in `house_rules`; the two constants below are duplicated on
# purpose (importing it here would be a cycle) and `tests/test_friend_v3_gates.py` asserts the
# copies agree, so a contract change cannot drift silently.
KF_HEADER_FIRST = "Year to 31 Dec"
KF_LEVEL_ROWS = ("Revenue", "EBITDA", "Net Profit", "EPS")

# --- G1.1 markers -----------------------------------------------------------------------------
#: A deck whose newest narrated period is older than the period the calendar already requires
#: must SAY so on the cover. These are the phrases that count as saying it.
STALE_DISCLOSURE_MARKERS = (
    "latest available", "newest available", "most recent available", "latest period available",
    "newest period available", "most recent period available", "not yet available",
    "not yet released",
)

# --- G2.2 markers -----------------------------------------------------------------------------
#: A forecast margin above the issuer's own record has to be explained where the margin is
#: argued. These are COST, MIX or CAPACITY drivers: "margin" itself is deliberately absent,
#: because a narrative that merely repeats the word "margin" has explained nothing (observed:
#: "Margins move to the end of the period." passed the first draft of this arm).
MARGIN_DRIVER_MARKERS = (
    "operating leverage", "efficiency", "efficient", "unit cost", "cash cost", "cost per",
    "cost base", "product mix", "mix", "utilisation", "utilization", "smelter", "ramp",
    "grade", "yield", "throughput", "royalt", "tariff", "hedge", "price deck", "indexation",
    "pass-through", "volume growth", "scale", "capacity", "downtime", "fuel", "energy cost",
)

# --- G5.2 verb lexicon ------------------------------------------------------------------------
#: G5.2 wants a thesis, not a statistic: the title must carry a verb. The list holds INFLECTED
#: forms only - a base form collides with the nouns this deck's titles are made of ("fund",
#: "record", "price", "cost"), and a proxy that accepts them would pass any statistic. Tokens
#: ending in -ed or -ing are accepted on top of the list. Documented as a PROXY in the
#: reconciliation; the violation message says which arm failed.
THESIS_VERBS = (
    "rises", "falls", "grows", "lifts", "drives", "pressures", "expands", "eases", "returns",
    "turns", "peaks", "cuts", "boosts", "supports", "keeps", "resumes", "normalises",
    "normalizes", "widens", "narrows", "rebuilds", "accelerates", "funds", "pays", "unlocks",
    "derisks", "de-risks", "closes", "starts", "finishes", "adds", "drops", "recovers",
    "slows", "beats", "meets", "outpaces", "leads", "trails", "cushions", "absorbs",
    "relieves", "clears", "restores", "shrinks", "doubles", "halves", "offsets",
)

# --- G5.3 curation ----------------------------------------------------------------------------
DRIVER_AXIS_MARKERS = ("revenue", "sales", "margin", "ebitda", "capex", "capital spending",
                       "debt", "cash flow", "demand", "price", "volume", "cost", "capacity",
                       "production", "contract", "dividend", "payout", "tariff", "royalt")
DURABILITY_MARKERS = ("smelter", "capacity", "contract", "policy", "regulation", "tariff",
                      "dividend", "index", "structural", "multi-year", "long-term", "permanent",
                      "guidance", "policy", "expansion", "reserve", "licence", "license")
#: G5.3 excludes these outright: a daily move, a daily broker print, an index reshuffle with no
#: concrete flow figure, and an insider block under the materiality floor.
BANNED_CATALYST_PATTERNS = (
    (re.compile(r"\b(share price|saham)\b.{0,40}\b(naik|turun|rose|fell|jumped|slipped)\b.{0,20}\b\d"),
     "a daily share-price move"),
    (re.compile(r"\b(broker|net buy|net sell|arus beli|arus jual)\b.{0,30}\b(today|hari ini|daily|harian)\b"),
     "daily broker flow"),
    (re.compile(r"\b(rebalanc|reshuffle|index review)\b(?!.{0,60}(bn|miliar|juta|million))"),
     "an index rebalancing print with no concrete flow figure"),
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'.,%/&-]*", text or "")


#: A FIGURE is a standalone numeric token: currency-prefixed ('rp 33,9'), suffixed ('27,7%'),
#: or bare ('2028'). A digit welded into a name ('Phase-8', 'FY26F', '1Q26') is a name, and a
#: range ('2026-2028') counts once, so the count matches what a reader sees.
_FIGURE_RE = re.compile(r"(?<![a-z0-9\-])(?:rp|us\$|\$)?\s?\d[\d.,]*(?![\da-z])", re.I)


def _num_tokens(text: str) -> int:
    """Count FIGURES in a sentence: 'Rp 33,9 tn' is one figure, and a digit inside a name
    ('Phase-8', 'FY26F', '1Q26') is not a figure at all."""
    return len(_FIGURE_RE.findall((text or "").lower()))


def parse_house_number(value: Any) -> Optional[float]:
    """Read a house-formatted printed figure back into a float.

    House numbers are id-ID: dot thousands, comma decimals ("43.036", "(28,8)", "Rp 5.667").
    Returns None for an honest blank ("n/a", "-", "n.m.") so a blank never reads as zero.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = _text(value)
    if not s or s.lower() in {"n/a", "na", "-", "--", "nm", "n.m.", "x", ""}:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").lower()
    s = re.sub(r"(rp|us\$|\$|usd|idr|bn|tn|mn|md|\btriliun\b|\bmiliar\b|\bjuta\b)", " ", s)
    s = s.replace("x", " ").replace("%", " ")
    s = re.sub(r"[^\d.,\-]", "", s).strip()
    if not s or s in {"-", ".", ","}:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif "." in s:
        head, _, tail = s.rpartition(".")
        if len(tail) == 3 and head:
            s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


# =============================================================== G1.1 period freshness
_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
           "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
_DATE_RE = re.compile(
    r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})", re.I)

#: sub-period rank inside a year: a quarter is a quarter of the year's information, a semester
#: half of it, nine months three quarters, and the audited year the whole thing.
_RANKS = {"1Q": 0.25, "2Q": 0.5, "3Q": 0.75, "4Q": 1.0, "1H": 0.5, "2H": 1.0, "9M": 0.75,
          "FY": 1.0}


def parse_report_date(text: Any) -> Optional[_date]:
    m = _DATE_RE.search(_text(text))
    if not m:
        return None
    day, mon, year = int(m.group(1)), _MONTHS.get(m.group(2).lower()[:3]), int(m.group(3))
    if not mon or not year:
        return None
    try:
        return _date(year, mon, day)
    except ValueError:
        return None


def expected_period_rank(when: _date) -> tuple[float, str]:
    """The oldest period a report dated `when` is allowed to lead with (G1.1, 45 days).

    A period is expected once 45 days have passed since it closed: 1H by mid-August, 9M by
    mid-November, the audited year by mid-February, 1Q by mid-May. Returns (rank, label) where
    the rank is `year + fraction` so periods compare across years.
    """
    key = when.month * 100 + when.day
    if key >= 1115:                      # from 15 Nov: nine months of this year
        return when.year + _RANKS["9M"], f"9M{when.year % 100:02d}"
    if key >= 815:                       # from 15 Aug: the first half of this year
        return when.year + _RANKS["1H"], f"1H{when.year % 100:02d}"
    if key >= 516:                       # from 16 May: the first quarter of this year
        return when.year + _RANKS["1Q"], f"1Q{when.year % 100:02d}"
    if key >= 215:                       # from 15 Feb: the audited year just closed
        return (when.year - 1) + _RANKS["FY"], f"FY{(when.year - 1) % 100:02d}"
    # early January to mid February: the nine months of the year that just ended
    return (when.year - 1) + _RANKS["9M"], f"9M{(when.year - 1) % 100:02d}"


def plain_period_label(label: str) -> str:
    """A period tag in words a lay reader parses: '1H26' -> 'first-half' (G1.1 disclosure copy)."""
    tag = _text(label).upper()
    word = {"1Q": "first-quarter", "2Q": "second-quarter", "3Q": "third-quarter",
            "4Q": "fourth-quarter", "1H": "first-half", "2H": "second-half",
            "9M": "nine-month", "FY": "full-year"}.get(tag[:2], "")
    return word or "period"


_PERIOD_RES = (
    (re.compile(r"\b([1-4])Q(\d{2})\b", re.I), lambda m: (2000 + int(m.group(2)), f"{m.group(1)}Q")),
    (re.compile(r"\b([12])H(\d{2})\b", re.I), lambda m: (2000 + int(m.group(2)), f"{m.group(1)}H")),
    (re.compile(r"\b9M(\d{2})\b", re.I), lambda m: (2000 + int(m.group(2)), "9M")),
    (re.compile(r"\bFY(\d{2})\b", re.I), lambda m: (2000 + int(m.group(2)), "FY")),
    (re.compile(r"\bfirst quarter (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "1Q")),
    (re.compile(r"\bsecond quarter (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "2Q")),
    (re.compile(r"\bthird quarter (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "3Q")),
    (re.compile(r"\bfourth quarter (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "4Q")),
    (re.compile(r"\bfirst half (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "1H")),
    (re.compile(r"\bnine months (?:of )?(?:fy)?(\d{4})", re.I), lambda m: (int(m.group(1)), "9M")),
    (re.compile(r"\bfull year (?:of )?(\d{4})", re.I), lambda m: (int(m.group(1)), "FY")),
)


def newest_period_rank(text: str) -> tuple[float, str]:
    """The newest period a piece of copy names, as (rank, label)."""
    best: tuple[float, str] = (0.0, "")
    for rx, decode in _PERIOD_RES:
        for m in rx.finditer(_text(text)):
            try:
                year, tag = decode(m)
            except Exception:  # pragma: no cover - a decode that cannot happen is not a crash
                continue
            frac = _RANKS.get(tag)
            if frac is None:
                continue
            rank = year + frac
            if rank > best[0]:
                best = (rank, f"{tag}{year % 100:02d}")
    return best


def _cover_copy(payload: dict) -> str:
    s1 = ((payload.get("cover") or {}).get("slide1") or {})
    s2 = ((payload.get("cover") or {}).get("slide2") or {})
    bits = [s1.get("theme_title")]
    bits += list(s1.get("highlights") or [])
    bits += [(s1.get("financial_para") or {}).get("heading"),
             (s1.get("financial_para") or {}).get("body")]
    bits += [(s2.get("katalis") or {}).get("body"), (s2.get("valuasi") or {}).get("body")]
    return " ".join(_text(b) for b in bits if _text(b))


def check_period_freshness(payload: dict) -> list[str]:
    """G1.1 - the newest period in the copy must be the period the calendar already requires."""
    out: list[str] = []
    meta = payload.get("meta") or {}
    when = parse_report_date(meta.get("date"))
    if when is None:
        return out                      # a payload with no readable date is another arm's problem
    need_rank, need_label = expected_period_rank(when)
    have_rank, have_label = newest_period_rank(_cover_copy(payload))
    if not have_label:
        return out                      # no period in the copy at all: nothing to be stale about
    if have_rank >= need_rank:
        return out
    copy = _cover_copy(payload).lower()
    if any(marker in copy for marker in STALE_DISCLOSURE_MARKERS):
        return out
    out.append(
        f"G1.1 period freshness: the report is dated {when.isoformat()} (a {need_label} report is "
        f"already due 45 days after that close) but the newest period on the cover is {have_label}, "
        "and nothing on the cover says the newer period is unavailable - state it on the page or "
        "use the newer period")
    return out


# =============================================================== G1.2 unit scale
def _unit_cell(value: Any) -> Optional[str]:
    """Read a declared unit out of a row label: 'Revenue (Rpbn)' -> 'rpbn'."""
    m = re.search(r"\(([^)]+)\)", _text(value))
    if not m:
        return None
    return re.sub(r"[^a-z]", "", m.group(1).lower()) or None


def _decimals_in(text: Any) -> Optional[int]:
    s = _text(text).strip("()")
    if not s or s.lower() in {"n/a", "-", "nm", "n.m."}:
        return None
    if "," in s:
        return len(s.rsplit(",", 1)[1])
    return 0 if s else None


def _table_rows(page: Any, *keys: str) -> list[dict]:
    """Collect {label, cells, unit} rows out of a page payload, whichever shape it uses."""
    rows: list[dict] = []
    if not isinstance(page, dict):
        return rows
    for key in keys:
        block = page.get(key)
        if isinstance(block, dict):
            rows += [r for r in (block.get("rows") or []) if isinstance(r, dict)]
        elif isinstance(block, list):
            rows += [r for r in block if isinstance(r, dict)]
    return rows


def _surface_series(payload: dict) -> dict[tuple[str, int], list[tuple[float, str]]]:
    """(canonical metric, fiscal year) -> EVERY observation as (value in Rp bn, surface name).

    All observations are kept, not the first one: the point of the arm is that two surfaces
    printing the same metric for the same year agree. A first-wins dict silently dropped the
    second surface, so a scale disagreement could never be seen.
    """
    out: dict[tuple[str, int], list[tuple[float, str]]] = {}
    kf = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {})
    headers = [str(h) for h in (kf.get("headers") or [])]
    for row in kf.get("rows") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        label = _text(row[0])
        metric = _canonical_metric(label)
        if not metric:
            continue
        for i, cell in enumerate(row[1:], start=1):
            year = _year_of(headers[i] if i < len(headers) else "")
            value = parse_house_number(cell)
            if year is None or value is None:
                continue
            out.setdefault((metric, year), []).append((value, "cover.slide2.key_financials"))
    fh = payload.get("financial_highlights") or {}
    years = [str(y) for y in (fh.get("years") or [])]
    for row in fh.get("rows") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        metric = _canonical_metric(_text(row[0]))
        if not metric:
            continue
        for i, cell in enumerate(row[1:]):
            year = _year_of(years[i]) if i < len(years) else None
            value = parse_house_number(cell)
            if year is None or value is None:
                continue
            out.setdefault((metric, year), []).append((value, "financial_highlights"))
    statements = payload.get("statements_page") or {}
    cols = [str(c) for c in (statements.get("columns") or [])]
    if cols:
        for row in _table_rows(statements, "income"):
            metric = _canonical_metric(_text(row.get("label")))
            if not metric:
                continue
            for i, cell in enumerate(row.get("cells") or []):
                year = _year_of(cols[i]) if i < len(cols) else None
                value = parse_house_number(cell)
                if year is None or value is None:
                    continue
                out.setdefault((metric, year), []).append((value, "statements_page.income"))
    return out


def _year_of(label: Any) -> Optional[int]:
    m = re.search(r"(?:FY)?(\d{2}|\d{4})\s*[AFE]?\b", _text(label))
    if not m:
        return None
    raw = m.group(1)
    return 2000 + int(raw) if len(raw) == 2 else int(raw)


#: A row label that names a RATIO is not the level this arm compares: 'Marjin EBITDA (%)',
#: 'EBITDA Growth (%)' and 'EBITDA/ton' are all built out of the same word as the level row, and
#: reading them as levels produced ten false disagreements on the first live run.
_RATIO_TOKENS = ("margin", "marjin", "%", "growth", "yield", "per share", "(x)", " x)", "ratio",
                 "return", "/ton", "/lb", "per ton", "multiple", "bps", "payout")


def _canonical_metric(label: str) -> Optional[str]:
    low = _text(label).lower()
    if not low:
        return None
    if any(tok in low for tok in _RATIO_TOKENS):
        return None
    if "revenue" in low or "pendapatan" in low or low.startswith("sales"):
        return "revenue"
    if low.startswith("ebitda") or " ebitda" in low:
        return "ebitda"
    if "net profit" in low or "laba bersih" in low:
        return "net_profit"
    return None


def check_unit_scale(payload: dict) -> list[str]:
    """G1.2 - every table declares its unit, and one metric agrees across surfaces."""
    out: list[str] = []
    surfaces = _surface_series(payload)
    for key in sorted(surfaces):
        observations = sorted(surfaces[key], key=lambda obs: obs[1])
        if len(observations) < 2:
            continue
        first, first_surface = observations[0]
        if not first:
            continue
        for value, surface in observations[1:]:
            rel = abs(value - first) / abs(first)
            if rel > CROSS_SURFACE_TOLERANCE:
                metric, year = key
                out.append(
                    f"G1.2 unit scale: {metric} FY{year} reads {first:,.1f} in {first_surface} and "
                    f"{value:,.1f} in {surface} - {rel * 100:.1f}% apart, which is a scale or a "
                    "basis error, not a rounding difference")

    # A table that prints figures but declares no unit anywhere is unreadable at the margin.
    kf = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {})
    declared = sum(1 for row in (kf.get("rows") or [])
                   if isinstance(row, (list, tuple)) and _unit_cell(row[0]))
    level_rows = sum(1 for row in (kf.get("rows") or [])
                     if isinstance(row, (list, tuple)) and _canonical_metric(_text(row[0])))
    if level_rows and declared == 0:
        out.append("G1.2 unit scale: the Key Financials exhibit declares no unit in any row label "
                   "(house format puts it inside the label: 'Revenue (Rpbn)')")

    # A figure far outside the band its declared unit implies is a decimal-place bug.
    for row in (kf.get("rows") or []):
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        unit = _unit_cell(row[0])
        if unit not in {"rpbn", "rpmn", "rptn"}:
            continue
        for cell in row[1:]:
            value = parse_house_number(cell)
            if value is None:
                continue
            if unit == "rpbn" and abs(value) >= 1e7:
                out.append(
                    f"G1.2 unit scale: {_text(row[0])} prints {cell}, which is Rp "
                    f"{abs(value) / 1e6:,.0f} tn - a magnitude no issuer reaches, so the row and "
                    "its unit disagree")
            if unit == "rptn" and 0 < abs(value) < 0.01:
                out.append(
                    f"G1.2 unit scale: {_text(row[0])} prints {cell} in Rp tn, which is Rp "
                    f"{abs(value) * 1000:,.1f} bn - the unit looks one step too large")
    return out


# =============================================================== G2.2 / G2.3 / G2.6 forecast
def _forecast_columns(payload: dict) -> list[int]:
    kf = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {})
    headers = [str(h) for h in (kf.get("headers") or [])]
    return [i for i, h in enumerate(headers) if h.strip().upper().endswith("F")]


def _historical_ebitda_margin(payload: dict) -> list[float]:
    fh = payload.get("financial_highlights") or {}
    for row in fh.get("rows") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        label = _text(row[0]).lower()
        if "ebitda" in label and "%" in label:
            vals = [parse_house_number(c) for c in row[1:]]
            return [v for v in vals if v is not None and v > 0]
    return []


def _forecast_ebitda_margin(payload: dict) -> list[float]:
    quad = None
    for q in ((payload.get("performance_page") or {}).get("quadrants") or []):
        if "ebitda" in _text(q.get("title")).lower():
            quad = q
            break
    if isinstance(quad, dict):
        n_actual = int(quad.get("actual_n") or 0)
        series = [parse_house_number(v) for v in (quad.get("line") or [])]
        out = [v for v in series[n_actual:] if v is not None]
        if out:
            return out
    # fall back to the Key Financials exhibit when the quadrant is absent
    kf = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {})
    fcols = _forecast_columns(payload)
    rev = ebi = None
    for row in kf.get("rows") or []:
        if not isinstance(row, (list, tuple)):
            continue
        metric = _canonical_metric(_text(row[0]))
        vals = [parse_house_number(c) for c in row[1:]]
        if metric == "revenue":
            rev = vals
        elif metric == "ebitda":
            ebi = vals
    out = []
    if rev and ebi:
        for i in fcols:
            if i < len(rev) and i < len(ebi) and rev[i] and ebi[i] is not None:
                out.append(ebi[i] / rev[i] * 100.0)
    return out


def check_forecast_margin(payload: dict) -> list[str]:
    """G2.2 - a forecast margin above the issuer's own record needs a stated driver."""
    out: list[str] = []
    hist = _historical_ebitda_margin(payload)
    fcast = _forecast_ebitda_margin(payload)
    if len(hist) < 3 or not fcast:
        return out
    record = max(hist)
    peak = max(fcast)
    if peak <= record + MARGIN_TOLERANCE_PP:
        return out
    quad = next((q for q in ((payload.get("performance_page") or {}).get("quadrants") or [])
                 if "ebitda" in _text(q.get("title")).lower()), {})
    narrative = _text((quad or {}).get("narrative"))
    if narrative and any(mark in narrative.lower() for mark in MARGIN_DRIVER_MARKERS):
        return out
    where = "the EBITDA quadrant narrative" if narrative else "the page that owns the margin"
    out.append(
        f"G2.2 margin sanity: the forecast EBITDA margin peaks at {peak:.1f}% against a "
        f"historical record of {record:.1f}%, and {where} names no cost, price, volume or "
        "mix driver for the gap")
    return out


def check_flat_forecast_years(payload: dict) -> list[str]:
    """G2.6 - consecutive forecast years must not print the same level without saying why."""
    out: list[str] = []
    kf = (((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {})
    headers = [str(h) for h in (kf.get("headers") or [])]
    fore = _forecast_columns(payload)
    declared_flat = any(
        "flat" in _text(n).lower() or "held constant" in _text(n).lower()
        for n in (kf.get("notes") or []))
    for row in kf.get("rows") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        label = _text(row[0])
        if not any(label.startswith(prefix) for prefix in KF_LEVEL_ROWS):
            continue
        cells = [parse_house_number(c) for c in row[1:]]
        # headers[0] is the row-label column, so a header index maps to a cell one place lower.
        for a, b in zip(fore, fore[1:]):
            ia, ib = a - 1, b - 1
            if ia < 0 or ib < 0 or ia >= len(cells) or ib >= len(cells):
                continue
            va, vb = cells[ia], cells[ib]
            if va is None or vb is None or va == 0:
                continue
            if abs(vb - va) / abs(va) <= FLAT_TOLERANCE:
                if declared_flat:
                    continue
                out.append(
                    f"G2.6 forecast variation: {label} prints the same level in "
                    f"{headers[a] if a < len(headers) else a} and "
                    f"{headers[b] if b < len(headers) else b} ({va:,.1f}) - a flat year needs an "
                    "explicit reason, otherwise the row is a placeholder")
    return out


def elasticity_from_margin(margin_pct: float) -> Optional[float]:
    """G2.3 - a 10% price/demand shock moves EBITDA by 10% / margin when costs are fixed.

    This is the pass-through the ruleset asks for, recomputed from the model's OWN margin, so a
    printed sensitivity can be checked against it instead of trusted.
    """
    if not margin_pct or margin_pct <= 0 or margin_pct > 100:
        return None
    return 10.0 / (margin_pct / 100.0)


def check_operating_leverage(payload: dict) -> list[str]:
    """G2.3 - if an operating-leverage figure is printed, it must be the margin-implied one.

    The arm judges a sentence only when it links a shock to EBITDA: any other percentage in the
    same sentence (a WACC, a growth rate) would otherwise read as a claim about elasticity.
    """
    out: list[str] = []
    hist = _historical_ebitda_margin(payload)
    fcast = _forecast_ebitda_margin(payload)
    margin = (fcast[0] if fcast else (hist[-1] if hist else None))
    expected = elasticity_from_margin(margin or 0)
    if expected is None:
        return out
    notes = " ".join(_text(n) for n in ((payload.get("valuation_page") or {}).get("notes") or []))
    notes += " " + " ".join(_text(n) for n in ((payload.get("performance_page") or {}).get("notes") or []))
    shock_tokens = ("10%", "10 %", "±10", "price move", "price shock", "demand shock",
                    "harga turun", "harga naik")
    for sentence in re.split(r"(?<=[.!?])\s+", notes):
        low = sentence.lower()
        if not any(tok in low for tok in shock_tokens):
            continue
        if not any(tok in low for tok in ("ebitda", "operating profit", "laba usaha")):
            continue
        shock_consumed = False
        for raw in re.findall(r"\d+(?:[.,]\d+)?\s?%", sentence):
            printed = parse_house_number(raw)
            if printed is None or printed <= 0:
                continue
            if printed == 10.0 and not shock_consumed:
                # The first 10% in the sentence is the shock itself, not a claim about EBITDA.
                shock_consumed = True
                continue
            if abs(printed - expected) / expected > 0.10:
                out.append(
                    f"G2.3 operating leverage: a sentence prints a {printed:,.1f}% EBITDA move for "
                    f"a 10% price or demand shock, but the model's own margin ({margin:,.1f}%) "
                    f"implies {expected:,.1f}% - a flat pass-through hides the leverage the thesis "
                    f"rests on: {sentence.strip()!r}")
    return out


# =============================================================== G3.4 scenario ladder
def _scenario_ladder(payload: dict) -> dict[str, float]:
    """Pull the downside/base/upside prices out of whichever shape carries them."""
    found: dict[str, float] = {}
    cdcf = payload.get("cDcf") or {}
    scenarios = cdcf.get("scenarios") if isinstance(cdcf, dict) else None
    if isinstance(scenarios, dict):
        for key, row in scenarios.items():
            if not isinstance(row, dict):
                continue
            value = parse_house_number(row.get("fair_value_per_share"))
            if value is None:
                value = parse_house_number(row.get("fair_value"))
            tag = _text(row.get("scenario") or key).upper()
            for name in ("BEAR", "BASE", "BULL"):
                if name in tag and value is not None:
                    found[name] = value
    if len(found) < 3:
        rows = ((payload.get("gate_inputs") or {}).get("scenarios") or {}).get("rows") or []
        for row in rows:
            cells = [_text(c) for c in row] if isinstance(row, (list, tuple)) else []
            joined = " ".join(cells).upper()
            for name in ("BEAR", "BASE", "BULL"):
                if name in joined and name not in found:
                    for cell in cells:
                        value = parse_house_number(cell)
                        if value is not None and value > 100:
                            found[name] = value
                            break
    return found


def check_scenario_ladder(payload: dict) -> list[str]:
    """G3.4 - the downside prices below the base case and the upside above it."""
    out: list[str] = []
    ladder = _scenario_ladder(payload)
    if len(ladder) < 3:
        return out
    bear, base, bull = ladder["BEAR"], ladder["BASE"], ladder["BULL"]
    if not (bear < base):
        out.append(
            f"G3.4 scenario ladder: the downside case prices at Rp {bear:,.0f} against a base case "
            f"of Rp {base:,.0f} - a downside that is not lower than the base case is a labelling "
            "error, not a scenario")
    if not (bull > base):
        out.append(
            f"G3.4 scenario ladder: the upside case prices at Rp {bull:,.0f} against a base case "
            f"of Rp {base:,.0f} - the ladder does not bracket the base case")
    return out


# =============================================================== G4.2 currency discipline
def _wacc_rows(payload: dict) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    page = payload.get("valuation_page") or {}
    for row in page.get("wacc_rows") or []:
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            out.append((_text(row[0]), _text(row[1]), _text(row[2] if len(row) > 2 else "")))
        elif isinstance(row, dict):
            out.append((_text(row.get("label")), _text(row.get("value")), _text(row.get("source"))))
    cdcf = payload.get("cDcf") or {}
    for row in (cdcf.get("wacc_table") or []) if isinstance(cdcf, dict) else []:
        if isinstance(row, dict):
            out.append((_text(row.get("label")), _text(row.get("value")), _text(row.get("source"))))
    return out


def check_currency_discipline(payload: dict) -> list[str]:
    """G4.2 - one currency, and the country risk premium counted once.

    An IDR model discounts at INDOGB, which already carries Indonesia's country risk, so adding a
    country risk premium on top double-counts it; a USD model has to add one. Both directions are
    checked, and so is a label that claims an adjustment the arithmetic does not carry.
    """
    out: list[str] = []
    rows = _wacc_rows(payload)
    if not rows:
        return out
    joined = " ".join(f"{a} {b} {c}" for a, b, c in rows).lower()
    idr = any(tok in joined for tok in ("indogb", "indonesia", "sbn"))
    usd = "ust" in joined or "us treasury" in joined or "treasury" in joined
    crp_rows = [r for r in rows
                if any(tok in r[0].lower() for tok in ("country risk", "crp"))
                or any(tok in r[2].lower() for tok in ("country risk premium",))]
    if idr and crp_rows:
        out.append(
            f"G4.2 currency discipline: the model discounts at INDOGB (a rate that already carries "
            f"country risk) and still adds {crp_rows[0][0]!r} - that count the premium twice")
    if usd and not idr and not crp_rows:
        out.append(
            "G4.2 currency discipline: the model discounts at a US treasury rate and adds no "
            "country risk premium, which underprices the country")
    if idr:
        for label, value, source in rows:
            if "risk premium" not in label.lower():
                continue
            low = source.lower()
            claims_country = ("country risk adj" in low or "country-risk adj" in low
                              or "damodaran indonesia" in low
                              or low.strip().startswith("indonesia"))
            if claims_country:
                out.append(
                    f"G4.2 currency discipline: the {label!r} row is sourced {source!r} while the "
                    "same build discounts at INDOGB - either the premium is the mature-market one "
                    "and the label must say so, or the country premium is counted twice")
    return out


# =============================================================== G5.2 headline caps
def _has_thesis_verb(text: str) -> bool:
    for w in (word.lower().strip(".,;:") for word in _words(text)):
        if w in THESIS_VERBS:
            return True
        if len(w) > 4 and (w.endswith("ed") or w.endswith("ing")):
            return True
    return False


def check_headline_caps(payload: dict) -> list[str]:
    """G5.2 - the title is a thesis inside its budget, the headline paragraph and bullets fit."""
    out: list[str] = []
    s1 = ((payload.get("cover") or {}).get("slide1") or {})
    title = _text(s1.get("theme_title"))
    if title:
        words = _words(title)
        if len(words) > TITLE_MAX_WORDS:
            out.append(
                f"G5.2 headline caps: the cover theme title runs {len(words)} words "
                f"(budget {TITLE_MAX_WORDS}): {title!r}")
        elif not _has_thesis_verb(title):
            out.append(
                f"G5.2 headline caps: the cover theme title carries no verb, so it is a statistic "
                f"rather than a forward thesis: {title!r}")
        if _num_tokens(title) > MAX_NUMBERS_PER_SENTENCE:
            out.append(
                f"G5.2 headline caps: the cover theme title carries {_num_tokens(title)} figures "
                f"(budget {MAX_NUMBERS_PER_SENTENCE}) - a title a reader cannot scan is not a "
                "thesis")
    heading = _text((s1.get("financial_para") or {}).get("heading"))
    if heading and len(_words(heading)) > HEADLINE_MAX_WORDS:
        out.append(
            f"G5.2 headline caps: the cover headline runs {len(_words(heading))} words "
            f"(budget {HEADLINE_MAX_WORDS}): {heading!r}")
    for i, bullet in enumerate(s1.get("highlights") or [], start=1):
        words = _words(_text(bullet))
        if len(words) > BULLET_MAX_WORDS:
            out.append(
                f"G5.2 headline caps: highlight {i} runs {len(words)} words "
                f"(budget {BULLET_MAX_WORDS})")
        for sentence in re.split(r"(?<=[.!?])\s+", _text(bullet)):
            if _num_tokens(sentence) > MAX_NUMBERS_PER_SENTENCE:
                out.append(
                    f"G5.2 headline caps: highlight {i} carries {_num_tokens(sentence)} figures in "
                    f"one sentence (budget {MAX_NUMBERS_PER_SENTENCE}): {sentence!r}")
    return out


# =============================================================== G5.3 catalyst curation
def _parse_iso(text: Any) -> Optional[_date]:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", _text(text))
    if not m:
        return None
    try:
        return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def score_catalyst(item: dict, *, report_date: Optional[_date] = None,
                   shares_out: Optional[float] = None) -> dict:
    """Score one catalyst on the ruleset's four axes, 0-3 each.

    The score is a PROXY computed from the item's own fields, not a model judgement: impact reads
    the driver vocabulary, materiality reads whether a figure exists (and whether the item admits
    it has none), durability reads the structural vocabulary, novelty reads the item's own date.
    The reconciliation documents that it can misjudge, and the gate only enforces the floor, the
    caps and the excluded categories on top of it.
    """
    blob = " ".join(_text(v) for v in (item.get("name"), item.get("effect"),
                                       item.get("source"))).lower()
    quantified = item.get("quantified") if isinstance(item.get("quantified"), dict) else {}
    qblob = " ".join(_text(v) for v in quantified.values()).lower()
    numbers = [v for v in quantified.values() if re.search(r"\d", _text(v))]
    admits_none = any(tok in qblob for tok in ("not yet quantifiable", "not quantifiable",
                                               "cannot be quantified", "tanpa basis"))

    impact = 3 if any(m in blob or m in qblob for m in DRIVER_AXIS_MARKERS) else 1
    if admits_none:
        materiality = 1
    elif len(numbers) >= 2:
        materiality = 3
    elif numbers:
        materiality = 2
    else:
        materiality = 0
    durability = 3 if any(m in blob for m in DURABILITY_MARKERS) else 2
    novelty = 1
    when = _parse_iso(item.get("date")) or _parse_iso(quantified.get("date"))
    if when is None:
        for value in list(quantified.values()) + [item.get("source")]:
            when = parse_report_date(value) or _parse_iso(value) or when
    if when is None:
        novelty = 2                      # undated: neither fresh nor demonstrably old
    elif report_date is None:
        novelty = 2
    else:
        age = abs((report_date - when).days)
        novelty = 3 if age <= 90 else (2 if age <= 180 else 1)
    total = impact + materiality + durability + novelty
    return {"impact": impact, "materiality": materiality, "durability": durability,
            "novelty": novelty, "total": total, "admits_none": admits_none}


def check_catalyst_curation(payload: dict) -> list[str]:
    """G5.3 - the table is curated, capped, and insider flow is a direction, not a trade."""
    out: list[str] = []
    items = [c for c in (payload.get("catalysts") or []) if isinstance(c, dict)]
    if not items:
        return out
    when = parse_report_date((payload.get("meta") or {}).get("date"))
    shares = parse_house_number(((payload.get("cover") or {}).get("shares") or {}).get("outstanding"))
    if shares is not None:
        shares = shares * 1e9            # the cover prints billions of shares
    scored: list[tuple[str, dict]] = []
    for item in items:
        score = score_catalyst(item, report_date=when, shares_out=shares)
        scored.append((_text(item.get("name")), score))
        if score["total"] < CATALYST_SCORE_FLOOR:
            out.append(
                f"G5.3 catalyst curation: {_text(item.get('name'))!r} scores "
                f"{score['total']}/12 (impact {score['impact']}, materiality "
                f"{score['materiality']}, durability {score['durability']}, novelty "
                f"{score['novelty']}) against a floor of {CATALYST_SCORE_FLOOR} - it belongs in "
                "the context, not in the table")
    out += _check_catalyst_categories(items, shares)
    if len(items) > CATALYST_TABLE_MAX:
        out.append(
            f"G5.3 catalyst curation: the table carries {len(items)} items (cap "
            f"{CATALYST_TABLE_MAX})")
    katalis = ((payload.get("cover") or {}).get("slide2") or {}).get("katalis") or {}
    body = _text(katalis.get("body"))
    if body:
        named = sum(1 for name, _ in scored if name and name.lower() in body.lower())
        if named > CATALYST_COVER_MAX:
            out.append(
                f"G5.3 catalyst curation: the cover thesis paragraph names {named} catalysts "
                f"(cap {CATALYST_COVER_MAX}) - the rest belong on the catalyst page")
    return out


def _check_catalyst_categories(items: list[dict], shares: Optional[float]) -> list[str]:
    out: list[str] = []
    for item in items:
        name = _text(item.get("name"))
        blob = f"{name} {_text(item.get('effect'))} {_text(item.get('source'))}"
        for pattern, why in BANNED_CATALYST_PATTERNS:
            if pattern.search(blob.lower()):
                out.append(f"G5.3 catalyst curation: {name!r} is {why}, which the rules exclude")
                break
        quantified = item.get("quantified") if isinstance(item.get("quantified"), dict) else {}
        share_txt = _text(quantified.get("shares"))
        value = parse_house_number(share_txt)
        if value and shares:
            pct = abs(value) / shares * 100.0
            if pct < INSIDER_MATERIALITY_PCT:
                cumulative = any(tok in blob.lower() for tok in
                                ("cumulative", "in total", "net", "now holds", "holding"))
                if not cumulative:
                    out.append(
                        f"G5.3 catalyst curation: {name!r} is an insider block of "
                        f"{pct:.3f}% of the shares outstanding, below the {INSIDER_MATERIALITY_PCT}% "
                        "floor - insider activity is reported as a net direction, not as a single "
                        "trade")
    return out


# =============================================================== aggregate
def audit_friend_v3(payload: Optional[dict]) -> list[str]:
    """All ruleset arms, in clause order. An empty list means the payload satisfies them."""
    payload = payload or {}
    out: list[str] = []
    for check in (check_period_freshness, check_unit_scale, check_forecast_margin,
                  check_operating_leverage, check_flat_forecast_years, check_scenario_ladder,
                  check_currency_discipline, check_headline_caps, check_catalyst_curation):
        try:
            out += check(payload)
        except Exception as exc:  # a broken check must not take the render path down
            out.append(f"friend-v3 {check.__name__} raised {type(exc).__name__}: {exc}")
    return out


def _main(argv: Iterable[str]) -> int:
    """CLI measurement: `.venv/bin/python -m server.report.forecast_gate AMMN`."""
    args = [a for a in argv if not a.startswith("-")]
    ticker = (args[0] if args else "AMMN").upper()
    from server.routers.pdf import _build_live_payload
    payload = _build_live_payload(ticker, None)
    hits = audit_friend_v3(payload)
    print(json.dumps({"ticker": ticker, "hits": len(hits), "violations": hits},
                     indent=2, ensure_ascii=False))
    return 1 if hits else 0


if __name__ == "__main__":  # pragma: no cover - manual measurement entry point
    raise SystemExit(_main(sys.argv[1:]))
