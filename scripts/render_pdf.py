#!/usr/bin/env python
"""Backward-compat wrapper: scripts/render_pdf.py now defaults to Typst renderer.
The legacy Jinja2/Chromium path is preserved as scripts/render_pdf_chromium.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_typst import main
if __name__ == "__main__":
    main()
