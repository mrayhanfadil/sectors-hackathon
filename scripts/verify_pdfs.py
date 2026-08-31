"""Verify rendered PDFs: page count, header/footer/disclaimer/source text presence (T10 QA)."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

OUT = Path(__file__).resolve().parent.parent / "output"

CHECKS = [
    ("header RESEARCH", lambda t: t.count("RESEARCH") >= 4),
    ("OJK footer", lambda t: "bukan saran investasi" in t),
    ("source per exhibit (>=5 Sumber)", lambda t: t.count("Sumber") >= 5),
    ("disclaimer block", lambda t: "BUKAN SARAN INVESTASI" in t.upper()),
]

for pdf in sorted(OUT.glob("*.pdf")):
    reader = PdfReader(str(pdf))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    print(f"\n== {pdf.name} ==")
    print(f"   pages={len(reader.pages)} extracted_chars={len(text)}")
    for label, check in CHECKS:
        status = "OK " if check(text) else "FAIL"
        print(f"   [{status}] {label}")


