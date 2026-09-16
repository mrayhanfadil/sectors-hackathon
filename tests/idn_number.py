"""Read a number back out of the deck's printed text.

The deck prints Indonesian figures (dot thousands, comma decimals), so a consumer that undoes the separators
must undo them the same way: 4.137 is four thousand one hundred thirty-seven, and 43,04 is forty-three point
zero four. Parsing these strings with English assumptions is how a formatting change turns into a false
regression - or, worse, a wrong number nobody notices.
"""
from __future__ import annotations


def to_float(text) -> float:
    s = str(text).replace("Rp", "").replace("%", "").replace("\u00a0", "").strip()
    s = s.replace("(", "-").replace(")", "")          # the house writes negatives as (28,8)
    s = s.replace(" ", "")
    minus = s.startswith("-")
    s = s.lstrip("-+")
    s = s.replace(".", "").replace(",", ".")
    return -float(s) if minus else float(s)
