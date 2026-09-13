#!/usr/bin/env python3
"""Every payload path the FE reads must exist in the payload the PDF renders.

A component that binds to a path the payload does not carry does not throw a helpful error — it renders a pending
state, an empty axis, or crashes on `.toFixed()`. Either way the page looks like "no data" rather than a bug, which
is precisely the failure mode this revamp must not ship.

Reads the served JSON (the same builder the PDF uses) as ground truth, and only counts paths that come from the
report payload: `payload.a.b`, `payload["a"]`, and `field.x` where `field` was assigned from `payload.section`.

    .venv/bin/python scripts/fe_payload_path_check.py                 # AMMN
    .venv/bin/python scripts/fe_payload_path_check.py --ticker RATU
Exit code 1 when a path is missing from the payload.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FE = ROOT / "src/fe/src"

# `payload.a.b`, tolerating optional chaining and index access
RE_DOT = re.compile(r"(?<![\w.$])payload\?\.([A-Za-z_][\w]*(?:\??\.[A-Za-z_]\w*)*)")
RE_INDEX = re.compile(r"(?<![\w.$])payload\??\[\s*[\"']([\w.]+)[\"']\s*\]")
# `const page = payload.valuation_page` — then `page.bridge.ev` belongs under valuation_page
# `const ratingBox = payload.cover?.rating_box` — the optional chaining is part of the path, and stopping at
# `cover` reports correct code as broken (which is exactly what happened the first time this ran).
RE_SECTION_VAR = re.compile(
    r"\b(?:const|let)\s+(\w+)\s*=\s*(?<![\w.])payload\s*\??\.\s*([A-Za-z_][\w]*(?:\s*\??\.\s*[A-Za-z_]\w*)*)"
)
# attribute access on a JS object that is NOT the payload (import.meta.env, props.meta, ...)
METHODS = ("toFixed", "toLocaleString", "toString", "length", "join", "map", "filter", "slice", "split",
           "sort", "reverse", "find", "some", "every", "reduce", "includes", "replace", "trim", "padStart",
           "padEnd", "flat", "keys", "values", "entries", "concat")

RE_NOT_PAYLOAD_PREFIX = ("import.meta", "props.meta", "state.meta", "res.meta", "body.meta")


REPORT_SURFACE = ("routes/report", "components/report/", "lib/api", "lib/report", "routes/index")


PAYLOAD_KEYS: tuple[str, ...] = ()


def source_files() -> list[pathlib.Path]:
    out = []
    for f in sorted(FE.rglob("*.ts*")):
        rel = str(f.relative_to(FE))
        if "node_modules" in rel:
            continue
        if any(part in rel for part in REPORT_SURFACE):
            out.append(f)
    return out


def collect_paths() -> dict[str, set[str]]:
    paths: dict[str, set[str]] = {}

    def add(path: str, where: str) -> None:
        path = path.replace("?.", ".").strip(".")
        if not path:
            return
        # A method call on the value (`.toFixed(1)`, `.map(...)`, `.length`) is not part of the payload path: the
        # data path ends before it. Without this, correct code reads as a dangling path.
        parts = path.split(".")
        keep = []
        for part in parts:
            if part in METHODS:
                break
            keep.append(part)
        path = ".".join(keep)
        if path:
            paths.setdefault(path, set()).add(where)

    for f in source_files():
        text = f.read_text(errors="ignore")
        for m in RE_DOT.finditer(text):
            add(m.group(1), f.name)
        for m in RE_INDEX.finditer(text):
            add(m.group(1), f.name)

    sections: dict[str, str] = {}
    allowed = set(PAYLOAD_KEYS)
    for f in source_files():
        for m in RE_SECTION_VAR.finditer(f.read_text(errors="ignore")):
            section = re.sub(r"\s*\??\.\s*", ".", m.group(2))
            if section.split(".")[0] in allowed:
                sections[m.group(1)] = section
    for var, section in sections.items():
        for f in source_files():
            text = f.read_text(errors="ignore")
            for line in text.splitlines():
                if any(bad in line for bad in RE_NOT_PAYLOAD_PREFIX):
                    continue
                for m in re.finditer(rf"(?<![\w.]){re.escape(var)}\.([A-Za-z_][\w.]*)", line):
                    add(f"{section}.{m.group(1)}", f.name)
    return paths


def resolve(payload, path: str):
    node = payload
    for part in path.split("."):
        if isinstance(node, list):
            if not node:
                return "list-empty"
            node = node[0]
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="AMMN")
    args = ap.parse_args()

    from fastapi.testclient import TestClient
    from server.main import app

    with TestClient(app) as client:
        resp = client.get(f"/api/report/{args.ticker}/payload")
        if resp.status_code != 200:
            print(f"cannot check: {args.ticker} -> HTTP {resp.status_code}")
            return 1
        payload = resp.json()["payload"]
    global PAYLOAD_KEYS
    PAYLOAD_KEYS = tuple(payload.keys())

    paths = collect_paths()
    missing = [(p, w) for p, w in sorted(paths.items()) if resolve(payload, p) is None]
    ok = len(paths) - len(missing)
    print(f"payload paths read by the FE: {len(paths)} · present: {ok} · NOT in the payload: {len(missing)}")
    if missing:
        width = max(len(p) for p, _ in missing)
        for path, where in missing:
            print(f"  MISSING  {path:<{width}}  <- {', '.join(sorted(where))}")
        print("\nA missing path renders as an empty state or a crash, never as an error the user can act on.")
        return 1
    print("every path the FE reads exists in the served payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
