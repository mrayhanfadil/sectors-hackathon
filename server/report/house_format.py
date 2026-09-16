"""House document furniture - single source of truth for the Jinja/HTML report path.

The house rules are specified in `docs/rules/house-report-format.md` and implemented
by the Jinja/HTML template tree that the report API and the FE serve. Template
constants and Python constants describing the same furniture drifted apart before, so
this module holds the shared values once, next to nothing else, and
`tests/test_house_format_adoption.py` asserts they still match the templates and the
rule doc.

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

# --- Fixed strings (must equal the strings used by templates/macros.html) --------
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


def format_house_date(raw: object, short: bool = True) -> str:
    """`DD Mon YYYY` (e.g. "11 Sep 2026"), the convention rule 3 asks for in the page header.

    `short=False` still renders the long `Day, DD Month YYYY` form for any place that states the date in prose.
    The owner amended the rule on 13 Sep 2026: the header line is read on every page and the weekday was noise in
    it. Both forms read the same input and fall back to the string they were given.

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
        return _render_house_date(dt, short)

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
    return _render_house_date(dt, short)


def _render_house_date(dt, short: bool) -> str:
    mon = _MONTH_NAMES[dt.month - 1]
    return f"{dt.day} {mon[:3]} {dt.year}" if short else f"{_DAY_NAMES[dt.weekday()]}, {dt.day} {mon} {dt.year}"


def logo_data_uri() -> str:
    """Inline the Sectors mark so no renderer has to resolve a relative path.

    The Playwright path and the weasyprint fallback disagree about base URLs, and an
    un-resolvable image silently renders as nothing - the header would lose the logo
    with no error. Inlining removes that failure mode.
    """
    if not LOGO_PATH.exists():
        return ""
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def install(env, report_data: dict | None = None, native_furniture: bool = False) -> None:
    """Register the house furniture on a Jinja `Environment`.

    `report_data` supplies the publication date; the templates pass the same value to
    `running()`, but macros imported without context cannot see it, so it is exposed
    as a global instead of being threaded through every call site.

    `native_furniture` selects WHO draws the per-page header/footer:

    * False (default, any non-Chromium renderer such as weasyprint): the templates emit
      the furniture themselves, once per `<div class="page">`.
    * True (Chromium/Playwright): the furniture is drawn by the PDF engine through
      `header_template()` / `footer_template()` + `PDF_MARGIN`. This is the only variant
      that survives pagination - per-div furniture lives inside the content flow, so a
      page that overflows produces a continuation page with NO header, and the previous
      logical page's footer gets carried onto it (measured: 3 of 8 physical pages without
      a header, footer page numbers `[1,2,-,3,-,4,-,5]`). Per-div furniture is not
      "wrong" - it is simply only correct when one div is exactly one physical page.
    """
    meta = (report_data or {}).get("meta") or {}
    # The investment-thesis anchor is part of the house layout, so it rides with the furniture: every
    # environment that renders a house page gets it, not only the one the PDF router builds.
    from server.report.text_figures import hero_stat as _hero_stat

    env.filters["hero_stat"] = _hero_stat
    # One number format for the deck (dot thousands, comma decimals). `acct` is the house accounting
    # convention: a negative reads (28,8) rather than -28,8.
    from server.report import numfmt as _nf

    def _f_idn(value, digits=0, na="-"):
        return _nf.idn(value, digits, na=na)

    def _f_dec(value, digits=1, na="-"):
        return _nf.dec(value, digits, na=na)

    def _f_auto(value):
        from server.report import numfmt as _n

        return _n.auto(value, na="-")

    def _f_acct(value, digits=0, na="-"):
        text = _nf.idn(abs(value) if isinstance(value, (int, float)) else value, digits, na=na)
        return f"({text})" if isinstance(value, (int, float)) and value < 0 else text

    env.filters["idn"] = _f_idn
    env.filters["dec"] = _f_dec
    env.filters["acct"] = _f_acct
    # the templates call these as functions as well as filters (`acct(v, 0, "n/a")` reads better than a
    # filter chain when it sits inside a conditional), so both names exist
    env.globals["idn"] = _f_idn
    env.globals["dec"] = _f_dec
    env.globals["acct"] = _f_acct
    env.filters["auto"] = _f_auto
    env.globals["auto"] = _f_auto

    date_str = format_house_date(meta.get("date"))
    env.globals["HOUSE"] = {
        "header_title": HEADER_TITLE,
        "footer_left": FOOTER_LEFT,
        "footer_right": FOOTER_RIGHT,
        "source_line": SOURCE_LINE,
        "divider_color": DIVIDER_COLOR,
        "logo": logo_data_uri(),
        "identity": header_identity(report_data or {}),
        "date_short": format_house_date((report_data or {}).get("meta", {}).get("date"), short=True),
        "date": date_str,
        "native_furniture": native_furniture,
    }


# --- Page furniture drawn by Chromium (Playwright print path) --------------------
#
# A Playwright header/footer template renders in its OWN document, on EVERY physical
# page, and cannot see the report payload or the page's CSS. So: everything inline, no
# classes from macros.html, and any derived value (the formatted date, the inlined logo)
# has to be passed in from Python.
#
# The page-number span is Chromium's own substitution - `class="pageNumber"` is replaced
# with the physical page index at render time, which is exactly the "real page counter,
# not a per-page literal" the house rule asks for.
FONT_STACK = "Helvetica Neue, Arial, sans-serif"
PAGE_SIDE_PAD = "40pt"

# Space reserved OUTSIDE the content flow for the furniture. Header content is
# ~40pt tall (title + date + logo + divider), footer ~24pt.
# NOTE: Chromium's printToPDF rejects `pt` margins ("Failed to parse parameter value:
# 58pt") and silently drops the whole call - use px/in/mm/cm. Values in px here.
PDF_MARGIN = {"top": "77px", "bottom": "61px", "left": "0px", "right": "0px"}


def header_identity(data: dict) -> dict:
    """The issuer line and the rating/target line for the running header.

    Both come from the payload that is already on the page: nothing here is authored for the furniture, and a
    missing piece simply drops out of the line rather than being invented.
    """
    from server.report import numfmt as _n

    meta = (data or {}).get("meta") or {}
    cover = (data or {}).get("cover") or {}
    box = cover.get("rating_box") or {}
    ticker = (meta.get("ticker") or "").upper().strip()
    company = (meta.get("company_name") or "").strip()
    issuer = " · ".join([x for x in (f"{ticker} IJ" if ticker else "", company) if x])

    rating = str(box.get("action") or cover.get("rating") or "").strip()
    target = box.get("tp")
    bits = []
    if rating:
        bits.append(rating if rating.isupper() else rating.upper())
    if isinstance(target, (int, float)):
        bits.append(f"TP Rp {_n.idn(target, 0)}")
    return {"issuer": issuer, "status": " · ".join(bits)}


def header_template(date_str: str | None = None, identity: dict | None = None) -> str:
    """Top of every page: house title + publication date left, Sectors mark right, divider."""
    date_html = ""
    if date_str:
        date_html = (
            f'<div style="font:7pt {FONT_STACK};color:#475467;margin-top:1pt;">{date_str}</div>'
        )
    logo = logo_data_uri()
    logo_html = (
        f'<img src="{logo}" style="height:12pt;display:block;margin:0 0 2.5pt;" alt="Sectors.app">' if logo else ""
    )
    identity = identity or {}
    issuer = identity.get("issuer") or ""
    issuer_html = (
        f'<div style="font:700 8.6pt {FONT_STACK};color:#101828;letter-spacing:-0.1pt;">{issuer}</div>'
        if issuer else f'<div style="font:700 8.6pt {FONT_STACK};color:#101828;">{HEADER_TITLE}</div>'
    )
    house_line = " · ".join([x for x in (HEADER_TITLE if issuer else "", date_str or "") if x])
    status = identity.get("status") or ""
    status_html = (
        f'<div style="font:700 7.6pt {FONT_STACK};color:#101828;margin-bottom:1pt;">{status}</div>'
        if status else ""
    )
    return (
        f'<div style="width:100%;padding:0 {PAGE_SIDE_PAD};box-sizing:border-box;'
        f'-webkit-print-color-adjust:exact;print-color-adjust:exact;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f"<div>{issuer_html}"
        f'<div style="font:6.9pt {FONT_STACK};color:#475467;margin-top:0.5pt;">{house_line}</div></div>'
        f'<div style="flex:0 0 auto;text-align:right;">{logo_html}{status_html}</div>'
        f"</div>"
        f'<div style="border-bottom:1.2pt solid {DIVIDER_COLOR};margin-top:3pt;"></div>'
        f"</div>"
    )


def footer_template() -> str:
    """Bottom of every page: `sectors.app` left, disclosure + page number right."""
    return (
        f'<div style="width:100%;padding:0 {PAGE_SIDE_PAD};box-sizing:border-box;'
        f'font:6.5pt {FONT_STACK};color:#475467;-webkit-print-color-adjust:exact;">'
        f'<div style="border-top:.5pt solid #e4e7ec;padding-top:4pt;display:flex;'
        f'justify-content:space-between;">'
        f"<span>{FOOTER_LEFT}</span>"
        f'<span>{FOOTER_RIGHT} \u00b7 <span class="pageNumber"></span></span>'
        f"</div></div>"
    )
