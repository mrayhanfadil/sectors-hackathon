"""Ticker-agnostic WACC/terminal-growth defaults (Fadil, 16 Sep 2026).

Fadil locked two valuation constants to be the same across every ticker
so the deck doesn't drift when one issuer uses a different ERP/g than
another:

  - Terminal growth (g) ............. 3.50%  (0.0350)
  - Equity Risk Premium (ERP) ...... 4.00%  (0.0400)

Because WACC = We*CoE + Wd*CoD*(1-tax) and CoE = Rf + beta*ERP, locking
ERP at 4% also pins the WACC for any ticker that ships the same
Rf + beta + we/wd/cod/tax values. So the team constant is the *input*
(ERP) and the WACC becomes a derived value computed from it. We do NOT
hardcode a WACC number - that would be brittle across tickers with
different capital structure.

If you ever want to make g/ERP per-ticker again, the helper functions
below are the only place to touch - the rest of the codebase reads
through `lock_g()` / `lock_erp()` / `apply_locks()`. The constants are
also the authoritative source for any rule that compares the actual
g/erp to the team's expected value (e.g. the g-vs-inflation guard in
the gate system).
"""
from __future__ import annotations

TERMINAL_G: float = 0.035   # 3.50% - team default, locked Sep 2026
ERP_DEFAULT: float = 0.040  # 4.00% - team default, locked Sep 2026


def lock_g(assum: dict) -> float:
    """Return the team-locked terminal growth for any ticker.

    Always returns TERMINAL_G regardless of what the assumptions file
    says. Side-effect: stamps `assum["g"]` so downstream callers that
    read assum.get("g") see the locked value (keeps audit trail intact).
    """
    assum["g"] = TERMINAL_G
    return TERMINAL_G


def lock_erp(assum: dict) -> float:
    """Return the team-locked equity risk premium for any ticker.

    Always returns ERP_DEFAULT regardless of what the assumptions file
    says. Side-effect: stamps `assum["erp"]` so downstream callers that
    read assum.get("erp") see the locked value.
    """
    assum["erp"] = ERP_DEFAULT
    return ERP_DEFAULT


def apply_locks(assum: dict) -> dict:
    """Stamp g and erp on `assum` and return the same dict (mutates).

    Convenience for the one-page builder entry point that loads the
    assumptions dict before any valuation runs. Other code paths that
    only need one of the two should call `lock_g` / `lock_erp` directly
    so the intent is visible.

    Does NOT stamp `assum["wacc"]` - WACC is recomputed fresh from the
    locked ERP at the request boundary (see server.routers.pdf), since
    WACC depends on Rf + beta + we/wd/cod/tax which still vary by ticker.
    """
    if not isinstance(assum, dict):
        raise TypeError(f"apply_locks expected dict, got {type(assum).__name__}")
    lock_g(assum)
    lock_erp(assum)
    return assum
