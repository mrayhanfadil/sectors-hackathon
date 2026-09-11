"""House document furniture — single source of truth for the Jinja/HTML report path.

The house rules are specified in `docs/rules/house-report-format.md` and implemented
for the Typst path as constants in `templates/typst/common/theme.typ`. The HTML path
(the one the report API and the FE actually serve) is a second, independent template
tree, so it needs the same values. Duplicating them by hand is how the two trees
drifted apart in the first place, so this module holds them once, next to nothing
else, and `tests/test_house_format_adoption.py` asserts they match the Typst theme
and the rule doc.

Values that must be COMPUTED (the formatted publication date, the inline logo) live
here because Jinja cannot derive them: macros are imported without context, so the
templates reach these through `Environment.globals`.
"""
from __future__ import annotations

import base64
import re
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- Fixed strings (must equal templates/typst/common/theme.typ) -----------------
HEADER_TITLE = "Equity Research \u2013 Company Update"  # en dash, per the rule
FOOTER_LEFT = "sectors.app"
FOOTER_RIGHT = "See important disclosure at the back of this report"
SOURCE_LINE = "Company, Team Estimates"
DIVIDER_COLOR = "#067647"

LOGO_PATH = PROJECT_ROOT / "assets" / "brand" / "sectors-icon.svg"

_MONTHS = {
    "jan": 1, "januari": 1, "january": 1,
    "feb": 2, "februari": 2, "february": 2,
    "mar": 3, "maret": 3, "march": 3,
    "apr": 4, "april": 4,
    "mei": 5, "may": 5,
    "jun": 6, "juni": 6, "june": 6,
    "jul": 7, "juli": 7, "july": 7,
    "agt": 8, "agu": 8, "ags": 8, "agustus": 8, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "okt": 10, "oktober": 10, "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "des": 12, "desember": 12, "dec": 12, "december": 12,
}
_DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def format_house_date(raw: object) -> str:
    """`Day, DD Month YYYY` (e.g. "Monday, 31 August 2026").

    Accepts the mixed date strings the payloads carry ("31 Agt 2026", "20 Jul 2026",
    ISO). Input that cannot be understood is returned unchanged rather than being
    replaced with an invented date.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""

    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if iso:
        y, m, d = (int(x) for x in iso.groups())
        try:
            dt = date(y, m, d)
        except ValueError:
            return s
        return f"{_DAY_NAMES[dt.weekday()]}, {dt.day} {_MONTH_NAMES[dt.month - 1]} {dt.year}"

    toks = [t for t in re.split(r"[\s,.]+", s) if t]
    if len(toks) < 3:
        return s
    day_tok, mon_tok, year_tok = toks[0], toks[1], toks[2]
    if not re.match(r"^\d{1,2}$", day_tok) or not re.match(r"^\d{4}$", year_tok):
        return s
    mon = _MONTHS.get(mon_tok.lower())
    if not mon:
        return s
    try:
        dt = date(int(year_tok), mon, int(day_tok))
    except ValueError:
        return s
    return f"{_DAY_NAMES[dt.weekday()]}, {dt.day} {_MONTH_NAMES[dt.month - 1]} {dt.year}"


def logo_data_uri() -> str:
    """Inline the Sectors mark so no renderer has to resolve a relative path.

    The Playwright path and the weasyprint fallback disagree about base URLs, and an
    un-resolvable image silently renders as nothing — the header would lose the logo
    with no error. Inlining removes that failure mode.
    """
    if not LOGO_PATH.exists():
        return ""
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def install(env, report_data: dict | None = None) -> None:
    """Register the house furniture on a Jinja `Environment`.

    `report_data` supplies the publication date; the templates pass the same value to
    `running()`, but macros imported without context cannot see it, so it is exposed
    as a global instead of being threaded through every call site.
    """
    meta = (report_data or {}).get("meta") or {}
    env.globals["HOUSE"] = {
        "header_title": HEADER_TITLE,
        "footer_left": FOOTER_LEFT,
        "footer_right": FOOTER_RIGHT,
        "source_line": SOURCE_LINE,
        "divider_color": DIVIDER_COLOR,
        "logo": logo_data_uri(),
        "date": format_house_date(meta.get("date")),
    }
