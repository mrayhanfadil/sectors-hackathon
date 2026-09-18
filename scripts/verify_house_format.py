#!/usr/bin/env python
"""Artifact-level verifier for the house report format (docs/rules/house-report-format.md).

Why this exists next to `tests/test_house_format_adoption.py`: those guards read the
TEMPLATES and the rendered TEXT, which is necessary but not sufficient. A report can pass
every source-level guard and still ship a document where:

  * the house header/footer made it onto only some PHYSICAL pages (per-`<div class="page">`
    furniture does not survive a page overflow in the HTML/Playwright path - a page that
    overflows produces a continuation page with no header, and the footer of the previous
    logical page gets duplicated onto it),
  * an exhibit LABEL is orphaned at the bottom of a page while its chart renders on the
    next one (the label is then not above its object),
  * the footer page numbers are repeated/incomplete even though every page "has" a footer,
  * an em dash survived into the printed page (§12) - it can only come from text written at run
    time, so no source-level guard can see the string that produced it.

None of those are visible in the template source. They are only visible in the PDF.

Usage:
    .venv/bin/python scripts/verify_house_format.py output/<file>.pdf [more.pdf ...] [--json]

Exit code 0 = every PDF passed. Non-zero = at least one FAIL (details on stdout).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover
    print("pymupdf is required: .venv/bin/python -m pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from server.report.house_format import (  # noqa: E402
    FOOTER_LEFT,
    FOOTER_RIGHT,
    HEADER_TITLE,
    SOURCE_LINE,
)

SOURCE_FULL = f"Source: {SOURCE_LINE}"
# The source line can be WRAPPED by a narrow column ("Source:\nCompany,\nTeam\nEstimates"),
# which is a layout wart, not a missing line - match the words with any whitespace between
# them and report the wrapped occurrences separately as a warning.
SOURCE_RE = re.compile(r"Source:\s+" + r"\s+".join(re.escape(w) for w in SOURCE_LINE.split()))
DATE_RE = re.compile(
    r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b"
)
EXHIBIT_RE = re.compile(r"Exhibit\s+(\d+)\s*\.")
PAGENUM_RE = re.compile(re.escape(FOOTER_RIGHT) + r"\s*[\u00b7\u2013-]\s*(\d+)")

# The header lives in the top band of the paper; a header found anywhere else means the
# furniture was placed relative to a content div instead of the page.
HEADER_BAND = 0.22


def check(pdf: Path) -> dict:
    doc = pymupdf.open(str(pdf))
    pages = doc.page_count
    fails: list[str] = []
    warn: list[str] = []
    no_header, no_date, no_ftr_l, no_ftr_r, no_src, no_logo = [], [], [], [], [], []
    page_numbers: list[int | None] = []
    all_exhibits: list[int] = []
    source_lines = 0
    detail = []
    em_total = 0
    em_pages: list[int] = []
    em_samples: list[str] = []

    for i, page in enumerate(doc):
        pno = i + 1
        height = page.rect.height
        blocks = [b for b in page.get_text("blocks") if len(b) >= 5 and b[4].strip()]
        top_band = " ".join(b[4] for b in blocks if b[1] < height * HEADER_BAND)
        text = page.get_text()

        header = HEADER_TITLE in top_band or HEADER_TITLE.replace("\u2013", "-") in top_band
        date = bool(DATE_RE.search(top_band))
        ftr_l = FOOTER_LEFT in text
        ftr_r = FOOTER_RIGHT in text
        m = PAGENUM_RE.search(text.replace("\n", " "))
        page_numbers.append(int(m.group(1)) if m else None)
        n_src = len(re.findall(SOURCE_RE, text))
        n_src_flat = len(re.findall(re.escape(f"Source: {SOURCE_LINE}"), text))
        if n_src > n_src_flat:
            warn.append(
                f"rule 1 page {pno}: {n_src - n_src_flat} source line(s) WRAPPED across lines "
                "(column too narrow for one line) - present, but not the house one-liner"
            )
        source_lines += n_src
        exhibits = sorted(int(n) for n in EXHIBIT_RE.findall(text))
        all_exhibits.extend(exhibits)

        # Rule 12: no em dash on the printed page. Counting per page rather than per document so
        # the report names where it is, and keeping a sample line so the string can be traced
        # back to the writer (a payload string, an assumptions note, an agent paragraph).
        n_em = text.count("\u2014") + text.count("\u2015")
        if n_em:
            em_total += n_em
            em_pages.append(pno)
            if len(em_samples) < 3:
                for line in text.split("\n"):
                    if "\u2014" in line or "\u2015" in line:
                        em_samples.append(f"p{pno} {line.strip()[:70]}")
                        break

        if not header:
            no_header.append(pno)
        if not date:
            no_date.append(pno)
        if not ftr_l:
            no_ftr_l.append(pno)
        if not ftr_r:
            no_ftr_r.append(pno)
        # A source line on a page with NO exhibit label is legitimate when the object
        # spans the page break (the line belongs under its last fragment) - surfacing it
        # as a warning keeps the case visible without failing a correct document.
        if n_src > 0 and not exhibits:
            warn.append(
                f"rule 1 page {pno}: source line with no exhibit label on the page - correct "
                "if the object spans the page break, a separated source line otherwise"
            )
        if n_src == 0 and exhibits:
            no_src.append(pno)

        # Rule 3: the Sectors.app mark, same size and position on every page. Chromium
        # paints an SVG logo as VECTOR PATHS (4 bars, ~32 path items) and a raster logo as
        # an image XObject - so accept either, but require something SMALL in the
        # top-right corner, otherwise the full-width
        # header divider (height 0.8pt) counts as a logo. Detecting with get_images() alone
        # reports a perfectly rendered vector logo as MISSING.
        mark_band = pymupdf.Rect(page.rect.width * 0.6, 0, page.rect.width, height * 0.12)
        has_mark = False
        for im in page.get_images(full=True):
            try:
                r = pymupdf.Rect(page.get_image_bbox(im))
            except Exception:
                continue
            if r.is_valid and r.intersects(mark_band):
                has_mark = True
                break
        if not has_mark:
            try:
                for d in page.get_drawings():
                    r = pymupdf.Rect(d["rect"])
                    if r.intersects(mark_band) and r.width < page.rect.width * 0.4 and r.height > 2:
                        has_mark = True
                        break
            except Exception:
                pass
        if not has_mark:
            no_logo.append(pno)

        detail.append(
            {
                "page": pno,
                "chars": len(text),
                "header": header,
                "date": date,
                "footer_left": ftr_l,
                "footer_right": ftr_r,
                "page_number": page_numbers[-1],
                "source_lines": n_src,
                "exhibits": exhibits,
            }
        )

    if no_header:
        fails.append(f"rule 3 header `{HEADER_TITLE}` missing on physical pages {no_header}")
    if no_date:
        fails.append(f"rule 3 publication date (DD Mon YYYY) missing on pages {no_date}")
    if no_ftr_l:
        fails.append(f"rule 4 footer-left `{FOOTER_LEFT}` missing on pages {no_ftr_l}")
    if no_ftr_r:
        fails.append(f"rule 4 footer-right disclosure missing on pages {no_ftr_r}")
    if no_src:
        fails.append(f"rule 1 pages with an exhibit but no source line under it: {no_src}")
    if no_logo:
        fails.append(
            f"rule 3 Sectors.app mark missing from the top-right corner on pages {no_logo} "
            "- check house_format.header_template() still embeds the logo (an un-resolvable "
            "src renders as nothing, with no error anywhere)"
        )

    found = [n for n in page_numbers if n is not None]
    if len(found) < pages:
        fails.append(
            f"rule 4 footer page number missing on {pages - len(found)} of {pages} pages "
            f"({page_numbers})"
        )
    elif found != list(range(1, pages + 1)):
        fails.append(
            f"rule 4 footer page numbers are not 1..{pages} unique and complete: {page_numbers} "
            "- per-page furniture did not survive pagination"
        )

    unique = sorted(set(all_exhibits))
    if not unique:
        fails.append("rule 1/2 no `Exhibit N.` label found in the document")
    else:
        if unique != list(range(1, len(unique) + 1)):
            gaps = [n for n in range(1, max(unique) + 1) if n not in unique]
            fails.append(
                f"rule 2 exhibit counter is not 1..N (global, no gaps): present={unique} gaps={gaps}"
            )
        if len(all_exhibits) != len(set(all_exhibits)):
            warn.append(
                "rule 2 some exhibit numbers were read twice - check for an object that "
                "labels itself as well as being labelled by the renderer"
            )
    if source_lines < len(all_exhibits):
        fails.append(
            f"rule 1 {len(all_exhibits)} exhibits but only {source_lines} `{SOURCE_FULL}` lines"
        )

    # Rule 12 typography. A FAIL, not a warning: the deck ships to readers, and the one thing
    # that makes this rule hold for text nobody typed is the funnel
    # (server/report/text_sanitize.py) - a hit here means a string bypassed it.
    if em_total:
        fails.append(
            f"rule 12 {em_total} em dash(es) on physical pages {em_pages} "
            f"({'; '.join(em_samples)}) - the deck uses the hyphen separator "
            "('A - B'), so check that the payload passed through "
            "server/report/text_sanitize.py::clean before rendering"
        )

    # Rule 13 Sectoral tokens (friend-supplied, Sep 2026 - docs/design-system-friend.md).
    # The PDF is the only place Roboto-only and the printed primary can be observed:
    # every embedded font must belong to the Roboto family (no Inter / Source Serif /
    # Jakarta leaking from the old house furniture), and the Sectoral primary must be
    # used in drawn vector content (header divider, table header band, charts).
    fonts_seen: set[str] = set()
    for page in doc:
        try:
            for f in page.get_fonts(full=True):
                name = str(f[3]) if len(f) > 3 else ""
                if name:
                    fonts_seen.add(name)
        except Exception:
            pass
    non_roboto = sorted({n for n in fonts_seen if "roboto" not in n.lower()})
    # Warn, not fail: the report surfaces migrate to Roboto in other lanes, and the
    # shipped-PDF gate (tests/test_house_format_adoption.py) must stay green while
    # they land. The hard gate is tests/test_design_system_sectoral.py.
    if fonts_seen and non_roboto:
        warn.append(
            "rule 13 non-Roboto fonts embedded: "
            + ", ".join(non_roboto[:8])
            + " - the Sectoral system uses Roboto only"
        )
    primary_used = False
    try:
        for page in doc:
            for d in page.get_drawings():
                for key in ("color", "fill"):
                    col = (d.get(key) or ())
                    if len(col) == 3 and all(
                        abs(a - b) < 0.02
                        for a, b in zip(col, (0x09 / 255, 0x28 / 255, 0xB1 / 255))
                    ):
                        primary_used = True
                        break
                if primary_used:
                    break
            if primary_used:
                break
    except Exception:
        pass
    if not primary_used:
        warn.append(
            "rule 13 Sectoral primary #0928B1 not found in drawn vector content - "
            "expected in the header divider, table header band or chart series"
        )

    return {
        "pdf": str(pdf),
        "pages": pages,
        "fails": fails,
        "warn": warn,
        "info": {
            "exhibits": len(all_exhibits),
            "exhibit_numbers": unique,
            "source_lines": source_lines,
            "page_numbers": page_numbers,
            "em_dashes": em_total,
        },
        "pages_detail": detail,
    }


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    results = []
    failed = 0
    for arg in args:
        pdf = Path(arg)
        if not pdf.exists():
            print(f"[MISSING] {pdf}")
            failed += 1
            continue
        r = check(pdf)
        results.append(r)
        nums = r["info"]["exhibit_numbers"]
        span = f"{nums[0]}..{nums[-1]}" if nums else "-"
        print(
            f"[{'PASS' if not r['fails'] else 'FAIL'}] {pdf.name}  pages={r['pages']}  "
            f"exhibits={r['info']['exhibits']} ({span})  sources={r['info']['source_lines']}  "
            f"page_numbers={r['info']['page_numbers']}"
        )
        for f in r["fails"]:
            print(f"    FAIL {f}")
        for w in r["warn"]:
            print(f"    warn {w}")
        if r["fails"]:
            failed += 1
    if "--json" in sys.argv:
        out = Path("/tmp/verify_house_format.json")
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"json -> {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
