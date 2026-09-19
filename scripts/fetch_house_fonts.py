#!/usr/bin/env python3
"""Fetch the house fonts that are not committed to the repository.

`assets/fonts/*.ttf` is gitignored on purpose (binary blobs, fetched once - see the comment in
.gitignore), so a fresh clone has no fonts and the PDF renderer silently falls back to whatever
the base image ships. That is exactly how the deck shipped in Liberation Sans for weeks while the
CSS asked for Roboto. Run this after cloning, before `make build`.

Roboto is pulled from the same Google Fonts v51 files the front end loads
(`src/fe/index.html` -> fonts.googleapis.com/css2?family=Roboto), so the web deck and the printed
deck are set in the same generation of the face, and the file names match the @font-face block in
`templates/macros.html`.

Usage:
    python scripts/fetch_house_fonts.py            # fetch what is missing
    python scripts/fetch_house_fonts.py --force    # refetch everything
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FONTS_DIR = REPO_ROOT / "assets" / "fonts"

# Google Fonts CSS API -> TTF. A modern UA gets one @font-face per requested weight.
CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Roboto:ital,wght@0,300;0,400;0,500;0,700;1,400;1,700&display=swap"
)
# (style, weight) -> shipped file name (must match templates/macros.html @font-face block)
ROBOTO_FACES = {
    ("normal", "300"): "Roboto-Light.ttf",
    ("normal", "400"): "Roboto-Regular.ttf",
    ("italic", "400"): "Roboto-Italic.ttf",
    ("normal", "500"): "Roboto-Medium.ttf",
    ("normal", "700"): "Roboto-Bold.ttf",
    ("italic", "700"): "Roboto-BoldItalic.ttf",
}

# Fonts the deck also declares but that came from their own upstream repositories. They are listed
# so the checker reports them as expected-and-absent rather than unknown, and so a future host can
# see what a complete assets/fonts/ looks like.
UPSTREAM_FONTS = {
    "IBMPlexSans-Regular.ttf": "IBM Plex Sans (github.com/IBM/plex)",
    "IBMPlexSans-Bold.ttf": "IBM Plex Sans (github.com/IBM/plex)",
    "IBMPlexMono-Regular.ttf": "IBM Plex Mono (github.com/IBM/plex)",
    "IBMPlexMono-Bold.ttf": "IBM Plex Mono (github.com/IBM/plex)",
    "Inter-VF.ttf": "Inter (github.com/rsms/inter)",
    "Inter-Italic-VF.ttf": "Inter (github.com/rsms/inter)",
    "SourceSerif4-VF.ttf": "Source Serif 4 (github.com/adobe/fonts-source-serif)",
    "SourceSerif4-Italic-VF.ttf": "Source Serif 4 (github.com/adobe/fonts-source-serif)",
    "JetBrainsMono-VF.ttf": "JetBrains Mono (github.com/JetBrains/JetBrainsMono)",
    "JetBrainsMono-Regular.ttf": "JetBrains Mono (github.com/JetBrains/JetBrainsMono)",
    "JetBrainsMono-Bold.ttf": "JetBrains Mono (github.com/JetBrains/JetBrainsMono)",
}

SFNT_MAGIC = (b"\x00\x01\x00\x00", b"true", b"OTTO", b"ttcf")


def curl(url: str, dest: Path | None = None) -> bytes:
    cmd = ["curl", "-sSL", "--max-time", "120"]
    if dest:
        cmd += ["-o", str(dest)]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, check=True)
    return r.stdout


def fetch_roboto(force: bool) -> int:
    wanted = [n for n in ROBOTO_FACES.values() if force or not (FONTS_DIR / n).exists()]
    missing = [n for n in ROBOTO_FACES.values() if not (FONTS_DIR / n).exists()]
    if not wanted:
        print(f"roboto: all {len(ROBOTO_FACES)} faces present")
        return 0
    css = curl(CSS_URL).decode("utf-8", "replace")
    urls = {}
    for block in re.findall(r"@font-face\s*\{(.*?)\}", css, re.S):
        style = str((re.search(r"font-style:\s*(\w+)", block) or [None, ""])[1] or "")
        weight = str((re.search(r"font-weight:\s*(\d+)", block) or [None, ""])[1] or "")
        url = (re.search(r"url\((https://[^)]+)\)", block) or [None, ""])[1]
        name = ROBOTO_FACES.get((style, weight))
        if name and url:
            urls[name] = url
    written = 0
    for name in missing:
        url = urls.get(name)
        if not url:
            print(f"roboto: {name} not offered by the CSS API (style/weight pair missing)", file=sys.stderr)
            return 1
        dest = FONTS_DIR / name
        curl(url, dest)
        head = dest.read_bytes()[:4]
        if head not in SFNT_MAGIC:
            print(f"roboto: {name} downloaded but is not a font ({head!r})", file=sys.stderr)
            return 1
        print(f"roboto: wrote {name} ({dest.stat().st_size:,} bytes)")
        written += 1
    print(f"roboto: {written} of {len(ROBOTO_FACES)} faces fetched")
    return 0


def check_upstream() -> list[str]:
    absent = [name for name in UPSTREAM_FONTS if not (FONTS_DIR / name).exists()]
    if absent:
        print(f"note: {len(absent)} non-Roboto house font(s) absent (the deck renders without them):")
        for name in absent[:6]:
            print(f"  - {name} [{UPSTREAM_FONTS[name]}]")
    return absent


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch the house fonts that are not committed (Roboto from Google Fonts; "
                    "the other four families come from their upstream repositories)."
    )
    ap.add_argument("--force", action="store_true", help="refetch even if the file exists")
    args = ap.parse_args()
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    rc = fetch_roboto(args.force)
    check_upstream()
    if rc == 0:
        print(f"\nassets/fonts/ now holds {len(list(FONTS_DIR.iterdir()))} files")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
