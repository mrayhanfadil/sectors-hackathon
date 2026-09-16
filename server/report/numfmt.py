"""One number format for the whole deck: Indonesian convention (dot thousands, comma decimals).

The deck is written in Indonesian, so every figure the reader sees uses `43,04` / `1.234,56` / `+20,84%`,
whether it comes from a table, a narrative sentence, a ratio block or the gate's own message. Two entry points,
because the distinction matters for layout: `idn` keeps thousands grouping (use it where the original had it),
`dec` only swaps the decimal separator (use it inside narrow table columns, where adding separators would
widen the text and push a table out of its column).
"""
from __future__ import annotations

from typing import Any

DASH = "-"


def _swap(text: str) -> str:
    """'1,234.56' -> '1.234,56' without colliding the two separators."""
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def dec(value: Any, digits: int = 2, signed: bool = False, na: str = DASH, width: int = 0) -> str:
    """Decimal comma, no thousands grouping: 43.04 -> 43,04."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return na
    try:
        text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    except (TypeError, ValueError):
        return na
    text = _swap(text)
    return text.rjust(width) if width else text


def idn(value: Any, digits: int = 0, signed: bool = False, na: str = DASH, width: int = 0) -> str:
    """Grouped Indonesian number: 1234.567 -> 1.234,567."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return na
    try:
        text = f"{value:+,.{digits}f}" if signed else f"{value:,.{digits}f}"
    except (TypeError, ValueError):
        return na
    text = _swap(text)
    return text.rjust(width) if width else text


def pcfrac(value: Any, digits: int = 1, na: str = DASH) -> str:
    """A fraction as a percentage: 0.2084 -> 20,8%."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return na
    return dec(float(value) * 100, digits) + "%"


def pct(value: Any, digits: int = 1, signed: bool = True, na: str = DASH) -> str:
    """A number that is already a percentage: 20.84 -> +20,8%."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return na
    return dec(value, digits, signed=signed) + "%"


def auto(value: Any, na: str = "-") -> str:
    """Group and comma-decimal a raw value while keeping its own precision.

    Table cells arrive as raw floats with whatever precision the series has (8.61, 28.3, 14093.6). Formatting
    them at a fixed two decimals would print 28,30 next to 8,61, so trailing zeros are trimmed instead.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value if value is not None else na
    text = _swap(f"{value:,.2f}")
    if "," in text:
        text = text.rstrip("0").rstrip(",")
    return text
