"""Strings that reach the reader, cleaned once in the funnel both surfaces pass through.

Two jobs live here.

**1. Internal identifiers must not reach the reader.** The payload's source and note strings
were written for the people maintaining the pipeline, so they name repository paths
(`data/drivers/AMMN.json`), module paths (`server/report/engines/dcf_engine`) and API call
shapes (`company_report(AMMN,'peers') - published_pe_ttm // pb_mrq`). Those strings are
rendered, so a reader of the PDF and of the web page sees the machinery instead of the
attribution.

**2. Typography: the deck never prints an em dash** (house-report-format.md §12). An em dash
enters the pipeline from three places a source guard cannot see: prose an agent wrote at run
time, a `note` field in `data/assumptions/` or `data/drivers/`, and a string copied out of a
research PDF. Normalising here - one funnel, both surfaces - is what makes the rule hold for
text nobody typed into the repository.

The repository keeps the exact citations - `data/drivers/*.json` carries `source_internal` - so
rewriting what is *displayed* loses nothing: the record keeps the path, the reader gets the
attribution. Each replacement names the same dataset in the reader's language; none of them
invents a source.
"""
from __future__ import annotations

import re

# --- §12 typography -------------------------------------------------------------------------
# The house separator is a hyphen with a space on each side ("Opsi A - DCF FCFF"). An em dash
# (U+2014) used as punctuation between words becomes that separator; one used INSIDE a token is
# a range ("2024A-2028F") and becomes a plain hyphen.
#
# En dash (U+2013) is deliberately NOT normalised: house-report-format.md §3 mandates the header
# "Equity Research - Company Update" and the range labels ("Rp 5.000 - Rp 7.000") are written
# with it, so removing it would break a rule while enforcing another.
EM_DASH = "\u2014"
HORIZONTAL_BAR = "\u2015"
DASH_SEPARATOR = " - "
_SPACED_DASH = re.compile(r"(?<=\s)[\u2014\u2015](?=\s)")
_ANY_DASH = re.compile(r"[\u2014\u2015]")


def normalize_dashes(text: str) -> str:
    """Replace em dashes / horizontal bars with house punctuation. Pure, idempotent."""
    if EM_DASH not in text and HORIZONTAL_BAR not in text:
        return text
    text = _SPACED_DASH.sub("-", text)
    return _ANY_DASH.sub("-", text)


def dash_hits(value, limit: int = 0) -> list[str]:
    """Paths of printable strings that still carry an em dash / horizontal bar.

    Used by the guards (`tests/test_no_em_dash.py`, the artifact check) so the list of places
    to fix is derived from the payload rather than hand-maintained. `limit` > 0 stops early.
    """
    found: list[str] = []

    def walk(node, path=""):
        if limit and len(found) >= limit:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, (list, tuple)):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and (EM_DASH in node or HORIZONTAL_BAR in node):
            found.append(f"{path}: {node[:80]}")

    walk(value)
    return found


# Ordered: the more specific phrasing first, so a short pattern cannot eat a longer one.
# Ordered most specific first: a generic pattern that runs early eats the head of a longer path and leaves its tail
# stranded ("server/report/engines/dcf_engine" became "model internal DCF internal (FCFF)" on the first attempt).
RULES: list[tuple[re.Pattern[str], str]] = [
    # engine provenance - a required disclosure, restated as the model's name instead of a module path
    (re.compile(r"(?:server/report/engines|engines)/dcf_engine(?:\.dcf)?", re.I), "model DCF internal (FCFF)"),
    (re.compile(r"(?:server/report/engines|engines)/ev_ebitda[a-z_]*", re.I), "model EV/EBITDA internal"),
    (re.compile(r"scripts/dcf_engine(?:\.dcf)?(?:\s*/\s*[a-z_]+)?", re.I), "model DCF internal (FCFF)"),
    (re.compile(r"scripts/dcf\.py", re.I), "model DCF internal (FCFF)"),
    (re.compile(r"scripts/ev_ebitda\.py", re.I), "model EV/EBITDA internal"),
    # assumption and driver files
    (re.compile(r"data/assumptions/[A-Z]{2,6}\.json", re.I), "asumsi terverifikasi tim"),
    (re.compile(r"data/drivers/[A-Z]{2,6}\.json", re.I), "basis asumsi tim"),
    # dataset names as the reader knows them
    (re.compile(r"Sectors company/report financials\.historical_financials\s*\(([^)]*)\)", re.I),
     r"Sectors - laporan keuangan tahunan (\1)"),
    (re.compile(r"company/report financials\.historical_financials\s*\(([^)]*)\)", re.I),
     r"Sectors - laporan keuangan tahunan (\1)"),
    (re.compile(r"Sectors valuation\.historical_valuation", re.I), "Sectors - valuasi historis"),
    (re.compile(r"future\.analyst_rating_breakdown", re.I), "konsensus analis"),
    (re.compile(r"company_report\(([A-Z]{2,6})\s*,\s*'?([a-z_]+)'?\)", re.I), r"data \2 (\1)"),
    (re.compile(r"published_pe_ttm\s*//\s*pb_mrq", re.I), "P/E TTM dan P/BV MRQ"),
    # anything still repo-shaped, and the separator a removal leaves behind
    (re.compile(r"\b(?:server/report|server|src|tests|scripts|data)/[\w./-]+"), ""),
    (re.compile(r"^\s*[-\u2013\u2014\u2015]\s*"), ""),
    (re.compile(r"\s*[-\u2013\u2014\u2015]\s*(?=$|\()"), " "),
    (re.compile(r"\s{2,}"), " "),
]

# A path that survived the rules above still should not be printed.
LEFTOVER_PATH = re.compile(r"\b(?:data|server|src|scripts|tests)/[\w./-]+|\b\w+\.py\b")


# A cell that is only a placeholder is content, not a leftover separator. An earlier version of this module turned
# every "-" in the peer table into a space, which is how a formatting rule quietly deletes a table's meaning.
# The dash forms are all accepted, and all of them render as the plain hyphen: a cell that says "no data" must not
# be the one place an em dash survives (§12).
PLACEHOLDERS = {"-", "\u2013", "\u2014", "\u2015", "n/a", "N/A", "n.a.", "-%"}


def clean_text(text: str) -> str:
    text = normalize_dashes(text)
    if text.strip() in PLACEHOLDERS:
        return text
    # If the cell is purely numeric (with optional leading minus/plus sign), skip the
    # dash-stripping rules below - they were designed for narrative prose ("- EBITDA
    # tumbuh 12%") but ate the minus sign in numeric cells ("-7.635,0" -> "7.635,0").
    # The match accepts: optional sign, then digits / dot / comma / parens / percent / spaces.
    is_numeric_cell = bool(re.match(r"^\s*[+\-−–—]?[\d.,()%\s]+$", text)) and bool(
        re.search(r"\d", text)
    )
    for pattern, replacement in RULES:
        if is_numeric_cell and pattern.pattern in (
            r"^\s*[-\u2013\u2014\u2015]\s*",
            r"\s*[-\u2013\u2014\u2015]\s*(?=$|\()",
        ):
            continue
        text = pattern.sub(replacement, text)
    return text if text.strip() else text


def clean(value, _depth: int = 0):
    """Walk a payload and clean its printable strings. Keys and numbers are left exactly as they are."""
    if _depth > 12:
        return value
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        return {k: clean(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v, _depth + 1) for v in value]
    return value


def leftovers(payload) -> list[str]:
    """Path-shaped strings still present after cleaning - used by the check, so the list cannot rot."""
    found: list[str] = []

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and LEFTOVER_PATH.search(node):
            found.append(f"{path}: {node[:100]}")

    walk(payload)
    return found
