#!/usr/bin/env python
"""Artifact-level verifier for the house report format (docs/rules/house-report-format.md).

Why this exists next to `tests/test_house_format_adoption.py`: those guards read the
TEMPLATES and the rendered TEXT, which is necessary but not sufficient. A report can pass
every source-level guard and still ship a document where:

  * the house header/footer made it onto only some PHYSICAL pages (per-`<div class="page">`
    furniture does not survive a page overflow in the HTML/Playwright path — a page that
    overflows produces a continuation page with no header, and the footer of the previous
    logical page gets duplicated onto it),
  * an exhibit LABEL is orphaned at the bottom of a page while its chart renders on the
    next one (the label is then not above its object),
  * the footer page numbers are repeated/incomplete even though every page "has" a footer.

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
DATE_RE = re.compile(
    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
    r"\d{1,2}\s+(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4}"
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
    no_header, no_date, no_ftr_l, no_ftr_r, no_src = [], [], [], [], []
    page_numbers: list[int | None] = []
    all_exhibits: list[int] = []
    source_lines = 0
    detail = []

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
        n_src = len(re.findall(re.escape(SOURCE_FULL), text))
        source_lines += n_src
        exhibits = sorted(int(n) for n in EXHIBIT_RE.findall(text))
        all_exhibits.extend(exhibits)

        if not header:
            no_header.append(pno)
        if not date:
            no_date.append(pno)
        if not ftr_l:
            no_ftr_l.append(pno)
        if not ftr_r:
            no_ftr_r.append(pno)
        # A page carrying an object but no source line is the "object rendered, source
        # line left behind on the previous page" failure.
        if n_src == 0 and exhibits:
            no_src.append(pno)

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
        fails.append(f"rule 3 publication date (Day, DD Month YYYY) missing on pages {no_date}")
    if no_ftr_l:
        fails.append(f"rule 4 footer-left `{FOOTER_LEFT}` missing on pages {no_ftr_l}")
    if no_ftr_r:
        fails.append(f"rule 4 footer-right disclosure missing on pages {no_ftr_r}")
    if no_src:
        fails.append(f"rule 1 pages with an exhibit but no source line under it: {no_src}")

    found = [n for n in page_numbers if n is not None]
    if len(found) < pages:
        fails.append(
            f"rule 4 footer page number missing on {pages - len(found)} of {pages} pages "
            f"({page_numbers})"
        )
    elif found != list(range(1, pages + 1)):
        fails.append(
            f"rule 4 footer page numbers are not 1..{pages} unique and complete: {page_numbers} "
            "— per-page furniture did not survive pagination"
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
                "rule 2 some exhibit numbers were read twice — check for an object that "
                "labels itself as well as being labelled by the renderer"
            )
    if source_lines < len(all_exhibits):
        fails.append(
            f"rule 1 {len(all_exhibits)} exhibits but only {source_lines} `{SOURCE_FULL}` lines"
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
