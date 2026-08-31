"""Verify rendered PDFs: page count, header/footer/disclaimer/source text presence (T10 QA)."""
from __future__ import annotations

from pathlib import Path

def _extract_text(pdf_path: Path) -> tuple[int, str]:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        pages = len(doc)
        text = "".join(page.get_text() for page in doc)
        return pages, text
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return len(reader.pages), text
    except ImportError:
        pass
    import subprocess
    try:
        res = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True, check=True)
        return 1, res.stdout
    except Exception as e:
        return 0, ""

OUT = Path(__file__).resolve().parent.parent / "output"

CHECKS = [
    ("header RESEARCH", lambda t: t.count("RESEARCH") >= 4),
    ("OJK footer", lambda t: "bukan saran investasi" in t),
    ("source per exhibit (>=5 Sumber)", lambda t: t.count("Sumber") >= 5),
    ("disclaimer block", lambda t: "BUKAN SARAN INVESTASI" in t.upper()),
]

for pdf in sorted(OUT.glob("*.pdf")):
    pages, text = _extract_text(pdf)
    print(f"\n== {pdf.name} ==")
    print(f"   pages={pages} extracted_chars={len(text)}")
    for label, check in CHECKS:
        status = "OK " if check(text) else "FAIL"
        print(f"   [{status}] {label}")


