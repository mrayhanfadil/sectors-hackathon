"""The valuation ladder - every rung the report computed, with the role of each.

A single headline number hides the argument. On the 15 Sep 2026 AMMN deck the
target (Rp 5,667) was one rung of five the modeler had actually computed:
Rp 3,830 on trailing EBITDA, Rp 4,277 at the own-history -1sigma multiple,
Rp 4,860 at the market-implied multiple, Rp 5,667 on the forward ramp case, and
Rp 5,873 on the own-history mean. Only the highest shipped, unlabelled.

This module assembles the ladder for the reader. It reads the rungs from the
ticker's most recent completed run (real modeler output, none invented) and falls
back to the deterministic sensitivity legs when there is no run. The rung the
published target sits on is marked `primary`; rungs a conceded debate round
attacked are marked `contested`.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger(__name__)


def _parse_rounds_safe(state: dict) -> list:
    """Rounds from run state, or [] - the deck must render without a debate."""
    try:
        from agents.valuation.dissent_audit import parse_rounds

        return parse_rounds(state)
    except Exception:  # noqa: BLE001
        return []


def _typographic(text: str) -> str:
    """House rule: a printed figure writes × - the modeler's labels may carry ASCII x.

    Normalising at the display layer keeps the rule satisfied without rewriting
    the agent's own output (which stays verbatim in the run state for audit).
    """
    import re as _re

    return _re.sub(r"(?<=\d)x\b", "×", text or "")


def _role(label: str, contested: bool, is_primary: bool) -> str:
    if is_primary:
        return "primary"
    if contested:
        return "contested"
    if "cross_check" in label or "sigma" in label or "mean" in label:
        return "cross-check"
    return "sensitivity"


def build_ladder(ticker: str, price: float | None = None, target: float | None = None) -> dict:
    """Return {available, rows, note} for the deck. Never raises, never invents."""
    rows: list[dict] = []
    source = "run"
    try:
        from agents.valuation.dissent_audit import ladder_from_text
        from server.storage import AgentRunStore

        run = AgentRunStore().get_latest_completed(ticker)
        state = (run or {}).get("state") or {}
        rungs = ladder_from_text(state.get("valuation_output")) if state else []
    except Exception as exc:  # noqa: BLE001 - the deck must render without a run
        logger.warning("ladder unavailable for %s: %s", ticker, exc)
        rungs = []
        state = {}

    if not rungs:
        return {
            "available": False,
            "rows": [],
            "note": "Tangga valuasi belum tersedia: belum ada run agen yang menghitungnya.",
        }

    # Which rung did the report price on? Match by value, not by label.
    primary_value = None
    if target:
        closest = min(rungs, key=lambda r: abs(r.fair_value - target))
        if abs(closest.fair_value - target) / max(abs(target), 1.0) <= 0.005:
            primary_value = closest.fair_value

    # Rungs attacked by a conceded debate round.
    contested_vals: set[float] = set()
    try:
        import re

        rounds = [r for r in _parse_rounds_safe(state) if r.conceded and r.rating_relevant]
        tokens: set[str] = set()
        for r in rounds:
            tokens |= {m.group(0).lower().replace(" ", "") for m in re.finditer(r"\b(?:fy\d{2}f?)\b", r.claim, re.I)}
            tokens |= {m.group(0).replace(" ", "").lower() for m in re.finditer(r"\d+(?:[.,]\d+)?\s*(?:×|x)\b", r.claim)}
        for r in rungs:
            if any(t in f"{r.label} {r.basis}".lower() for t in tokens):
                contested_vals.add(r.fair_value)
    except Exception:  # noqa: BLE001
        pass

    for r in sorted(rungs, key=lambda x: x.fair_value, reverse=True):
        is_primary = primary_value is not None and abs(r.fair_value - primary_value) < 0.01
        contested = r.fair_value in contested_vals
        upside = (r.fair_value - price) / price if price else None
        # Pre-format with the house number format: rendering a raw float in the
        # template puts an English decimal in front of the reader, which the
        # deck's own house-rule audit rejects.
        try:
            from server.report import numfmt as _nf

            upside_str = f"{_nf.dec(upside * 100, digits=2, signed=True)}%" if upside is not None else "n/a"
        except Exception:  # noqa: BLE001
            upside_str = "n/a"
        rows.append(
            {
                # "headline" is the parser's name for a bare scalar with no basis
                # label around it - say that plainly rather than implying it is the
                # headline number.
                "label": _typographic(
                    "nilai tunggal (basis tak berlabel)" if r.label == "headline" else r.label.replace("_", " ")
                ),
                # The raw basis is the modeler's JSON snippet ("ev_ebitda": 17.0) -
                # it carries English decimal separators the deck must not print, so
                # the printed table gets the label only. The verbatim basis stays in
                # the run state for anyone auditing it.
                "basis_chars": len(r.basis),
                "fair_value": round(r.fair_value, 2),
                "upside_pct": round(upside * 100, 2) if upside is not None else None,
                "upside_str": upside_str,
                "role": _role(r.label, contested, is_primary),
                "contested": contested,
                "is_primary": is_primary,
            }
        )

    note = (
        f"{len(rows)} rung valuasi dihitung; kolom peran menandai mana yang jadi dasar "
        "target yang terbit (primary), mana yang diserang debat (contested), dan mana "
        "pembanding silang. Angka identik dengan output modeler pada run terakhir."
    )
    if not any(r["is_primary"] for r in rows) and target:
        note += " Target yang terbit tidak sama dengan rung mana pun - perlu ditelusuri."
    return {"available": True, "rows": rows, "source": source, "note": note}
