#!/usr/bin/env python3
"""Per-page parity between the shipped PDF and the rendered web page.

Matching section headings is not the same as matching content. This takes each PDF page's distinctive figures and asks
the rendered frontend text whether they are there, so a page that exists but is half-empty reports a number instead of
an impression. That is how four short pages were found after the section list already matched.

    .venv/bin/python scripts/fe_pdf_parity.py --pdf output/AMMN.pdf --fe-text /tmp/fe-public/public.txt

The frontend text comes from a headless browser (`page.inner_text("body")`) because what matters is the page that is
painted, not the source. With --min it exits non-zero when a page falls below the threshold, so it can gate a release.

Limits, stated because the number invites over-reading:
- It measures figures, not layout: a well-placed figure that renders in the wrong place still counts as present.
- A figure the page computes (a ratio, an index, a unit conversion) will not be found verbatim; those show up as
  misses and must be read in context before being called a defect.
- A page with almost no figures (a cover, a disclaimer) is not meaningfully measured - the row is reported as n/a.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

NUMBER = re.compile(r"\b\d{1,3}(?:[.,]\d{3})+(?:,\d+)?\b|\b\d{3,}(?:,\d+)?\b|\b\d+,\d+\b")
# years and page numbers are furniture, not content
SKIP = {str(y) for y in range(1990, 2041)} | {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"}


def pdf_pages(pdf: pathlib.Path) -> list[str]:
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    return [p for p in text.split("\f") if p.strip()]


def _fe_side_numbers(fe: str) -> set[str]:
    """Every numeric form the page prints, so a value that is on the page in another notation still counts."""
    out: set[str] = set()
    for tok in NUMBER.findall(fe):
        out.add(tok)
        out.add(tok.replace(".", "").replace(",", "."))
        out.add(tok.replace(".", ""))
    return out


def classify(missing: list[str], payload_url: str) -> tuple[list[str], list[str]]:
    """Split the figures the page lacks into content gaps and chart furniture.

    A figure the payload does not carry cannot be content the page dropped: it is a tick label, an axis value or
    something the document's own renderer computed. Only what the payload carries counts as a gap.
    """
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(payload_url, timeout=120) as r:
            blob = json.dumps(json.loads(r.read()), ensure_ascii=False)
    except Exception as exc:  # the classification is an aid, never a reason to fail the measurement
        print(f"        (could not read the payload for classification: {type(exc).__name__})")
        return [], list(missing)

    leaves: set[str] = set()
    for tok in NUMBER.findall(blob):
        leaves.add(tok)
        leaves.add(tok.replace(".", ""))
    content = [t for t in missing if t in leaves]
    furniture = [t for t in missing if t not in leaves]
    return content, furniture


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=pathlib.Path)
    ap.add_argument("--fe-text", required=True, type=pathlib.Path)
    ap.add_argument("--min", type=float, default=0.0, help="fail below this coverage per page (0 = report only)")
    ap.add_argument("--show-missing", type=int, default=8)
    ap.add_argument("--payload-url", default="", help="served payload; a figure missing from the page is only a "
                                                      "CONTENT gap if the payload carries it")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"pdf not found: {args.pdf}")
        return 1
    if not args.fe_text.exists():
        print(f"frontend text not found: {args.fe_text} - render the page first (headless browser, inner_text)")
        return 1

    fe = re.sub(r"\s+", " ", args.fe_text.read_text())
    pages = pdf_pages(args.pdf)
    print(f"pages: {len(pages)} · frontend text: {len(fe)} chars\n")
    print(f"{'page':>4}  {'figures':>7}  {'present':>7}  coverage")
    below: list[int] = []
    for i, page in enumerate(pages, 1):
        uniq = list(dict.fromkeys(t for t in NUMBER.findall(page) if t not in SKIP))
        if not uniq:
            print(f"{i:>4}  {0:>7}  {0:>7}      n/a")
            continue
        missing = [t for t in uniq if t not in fe]
        found = len(uniq) - len(missing)
        pct = found / len(uniq)
        flag = "" if pct >= (args.min or 0.9) else "  <-- short"
        print(f"{i:>4}  {len(uniq):>7}  {found:>7}  {pct * 100:5.0f}%{flag}")
        if args.min and pct < args.min:
            below.append(i)
        if missing and args.payload_url:
            content, furniture = classify(missing, args.payload_url)
            if content:
                print(f"        CONTENT GAP (the payload carries these): {', '.join(content[: args.show_missing])}")
            if furniture:
                print(f"        not in the payload (chart tick or derived at render): "
                      f"{', '.join(furniture[: args.show_missing])}")
        elif missing and args.show_missing:
            head = ", ".join(missing[: args.show_missing])
            print(f"        missing: {head}")

    if args.min and below:
        print(f"\npages below {args.min:.0%}: {below}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
