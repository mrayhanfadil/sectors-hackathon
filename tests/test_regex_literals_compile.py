"""Every regex literal in the repo must compile.

A text sweep over a codebase (this is how the em-dash removal was applied) can silently break a
character class: `[\\s,;:\u2013\u2014\\(\\)\\.]` becomes `[\\s,;:\\--\\(\\)\\.]`, which Python reads as the
descending range "\\-".."\\(" and refuses to compile. Nothing else notices until that code path
runs - that is how `server/report/forecast_path.py::display_attribution` broke while every
source-level guard stayed green.

The check is deliberately mechanical: find `re.<fn>(<literal>)`, join the adjacent literal
segments of a multi-line pattern, and compile it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".worktrees", "output", "out",
    ".pytest_cache", ".ruff_cache",
}

_LITERAL = r"""(?P<prefix>[rubfRUBF]*)(?P<q>'''|\"\"\"|'|\")(?P<body>(?:\\.|(?!\2).)*?)\2"""
RE_CALL = re.compile(r"\bre\.(?:compile|sub|subn|search|match|fullmatch|findall|finditer|split)\(\s*" + _LITERAL,
                     re.DOTALL)
RE_CONT = re.compile(r"\s*" + _LITERAL, re.DOTALL)


def _pattern_of(text: str, match: re.Match) -> str | None:
    """The full pattern: the literal plus every whitespace-separated segment after it.

    Adjacent string literals concatenate, so a pattern split across lines ("\\b(naik|tumbuh|" /
    "naik lagi)") is valid Python but no single segment compiles - joining them is what avoids a
    false positive. Three shapes cannot be judged statically and are skipped instead of guessed:
    an f-string, a pattern concatenated with a variable (`re.compile(r"(" + OTHER.pattern)`),
    and anything with an operation other than plain juxtaposition.
    """
    if "f" in match.group("prefix").lower():
        return None
    parts = [match.group("body")]
    pos = match.end()
    while True:
        tail = text[pos:]
        nxt = RE_CONT.match(text, pos)
        if nxt and not tail[: nxt.start() - pos].strip():
            if "f" in nxt.group("prefix").lower():
                return None
            parts.append(nxt.group("body"))
            pos = nxt.end()
            continue
        break
    # the argument ends here (comma / closing paren) or the pattern is built at run time
    if not text[pos:].lstrip().startswith((",", ")")):
        return None
    return "".join(parts)


def py_files() -> Iterator[Path]:
    for path in sorted(REPO_ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        yield path


def bad_regexes() -> list[str]:
    bad: list[str] = []
    for path in py_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in RE_CALL.finditer(text):
            pattern = _pattern_of(text, match)
            if pattern is None:
                continue
            try:
                re.compile(pattern)
            except re.error as exc:
                line = text[: match.start()].count("\n") + 1
                bad.append(f"{path.relative_to(REPO_ROOT)}:{line}: {exc} :: {pattern[:80]!r}")
    return bad


def test_every_regex_literal_compiles() -> None:
    bad = bad_regexes()
    assert not bad, (
        "a regex literal in this repository does not compile, so the code path that owns it can "
        "only fail at run time:\n  " + "\n  ".join(bad)
    )


if __name__ == "__main__":
    found = bad_regexes()
    print(f"scanned {sum(1 for _ in py_files())} python files; {len(found)} regex literal(s) do not compile")
    for item in found:
        print("  ", item)
    sys.exit(1 if found else 0)
