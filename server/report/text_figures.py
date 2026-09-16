"""Pull the anchor figure out of a line of report prose.

Deck page 3 shows one figure per investment-thesis pillar. The figure is never authored for the layout: a
pillar may declare `stat`, and when it does not, the first money amount or ratio in its own text is used. Both
the figure and the label beside it are therefore things the page already prints, and the rule is the same for
every issuer.
"""
from __future__ import annotations

import re

# A money amount (Rp 43.04 tn) or a ratio/percentage (17,99x, 23,4%). The sign is part of the figure: dropping
# it turns an outflow into an inflow. No \b after the unit class - "x" and "%" are non-word characters, so a
# word boundary can never hold there and ratio figures would silently never match.
_FIGURE = re.compile(r"([−\-–]?\s?(?:Rp\s?\d[\d.,]*\s?(?:tn|bn|md|m)\b|\d[\d.,]*\s?[×x%](?![\w])))")
_LABEL_SKIP = {"rp", "dari", "di", "ke", "pada", "dan", "vs", "atau", "the", "of", "sejak", "sampai"}


_PARENS = re.compile(r"\([^)]*\)")


def figure_in(text: str) -> str:
    """The first anchor figure in `text`, or an empty string when the line carries none.

    A figure inside parentheses is usually a date or a starting stake ("(12 Mei 2026, 6,162% -> 5,27%)"), so the
    text outside the parentheses is searched first. The figure is still lifted from the same sentence; nothing
    is authored for the layout.
    """
    raw = str(text or "")
    m = _FIGURE.search(_PARENS.sub(" ", raw)) or _FIGURE.search(raw)
    return " ".join(m.group(1).split()) if m else ""


def hero_stat(headline, detail="", want_label=False):
    """The anchor figure of a thesis line, plus a label built from the words in front of it."""
    for text in (headline, detail):
        value = figure_in(str(text or ""))
        if not value:
            continue
        if not want_label:
            return value
        raw = str(text)
        m = _FIGURE.search(_PARENS.sub(" ", raw)) or _FIGURE.search(raw)
        before = raw[: m.start()]
        # the label stays inside the figure's own sentence: crossing a full stop pulled the previous
        # sentence's figure into the label
        for sep in (". ", ": ", "; ", " - "):
            if sep in before:
                before = before.rsplit(sep, 1)[1]
        words = [w.strip("(),:;.") for w in before.split()][-3:]
        words = [w for w in words if w and w.lower() not in _LABEL_SKIP and not _FIGURE.search(w)]
        label = " ".join(words).strip(" ,:;.")
        if not label:
            # "100% pendapatan = tembaga+emas": nothing precedes the figure, so the label comes from what
            # follows it. Still the row's own words - the layout never invents a caption.
            after = raw[m.end():].split()
            words = [w.strip("(),:;.=–-→") for w in after][:4]
            words = [w for w in words if w and w.lower() not in _LABEL_SKIP and not _FIGURE.search(w)]
            label = " ".join(words[:2]).strip(" ,:;.")
        if len(label) > 22:
            label = " ".join(label.split()[-2:])
        return value, label.upper()
    return ("", "") if want_label else ""
