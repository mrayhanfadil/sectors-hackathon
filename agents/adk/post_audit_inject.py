"""Post-audit injection - mechanical, no LLM.

Why this module exists
----------------------
On 16 Sep 2026 the AMMN run (`ammn-313287e2`) shipped BUY with `gate_flags=[]`
even though Round 1 of its red-team debate `defense.mode='concede'`d on the
single binding pillar of the BUY TP (FY26F EBITDA projection). The dissent
audit correctly returned REJECT, but the writer_output that ships to the
PDF/HTML gate never carried the audit's `required_flags`.

The writer runs BEFORE the adversarial_loop, so it cannot know in advance
what the red team will concede. The fix is to inject AFTER the run finishes:
parse the writer_output JSON-fenced blob, append the audit's required_flags
to gate_flags (deduped), and if the anchor itself was contested, surface the
non-anchored FVs and the audit's own disclosure text.

Everything here is stdlib and mechanical. The audit reads rounds; this module
just propagates that read into the deliverable so the deck reflects what the
team itself concluded under cross-examination.

Inputs
------
``state`` is the post-run session.state dict (the same shape that lands in
``data/agent_runs.db.state_json``). ``price`` is the spot printed on the
deck (passed by the runner from ``data/assumptions/{TICKER}.json``).

Output
------
Returns a NEW dict copy of ``state`` with the writer_output re-serialized
(if it parsed) and a synthetic "__audit__" key attached for downstream
callers (PDF gate, /api/agent/runs/{id}). Non-matching / unparseable
writer_output is left alone - we never raise here.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from agents.valuation.dissent_audit import audit as _audit

logger = logging.getLogger(__name__)

#: Marker fences the writer actually used. Only the json fence shows up in
#: real runs; we try both via JSONDecoder.
_FENCE_JSON = re.compile(r"^\s*```json\s*\n(.*?)\n\s*```\s*$", re.DOTALL)


def _parse_writer_output(blob: str) -> dict | None:
    """Parse the writer_output blob (string with markdown json fence).

    Tolerant of three shapes seen in real runs:
      * ``\\n```json\\n{...}\\n```\\n`` (the modeler's preferred form)
      * raw ``{...}`` json
      * key-wrapped ``{"writer_output": {...}}`` (the agent-style form)
    Returns None on any parse failure.
    """
    if not isinstance(blob, str) or not blob.strip():
        return None
    candidates: list[str] = []
    m = _FENCE_JSON.match(blob.strip())
    if m:
        candidates.append(m.group(1))
    if blob.strip().startswith("{"):
        candidates.append(blob.strip())
    # Last resort: split on the first { and the last }
    if "{" in blob and "}" in blob:
        inner = blob[blob.find("{") : blob.rfind("}") + 1]
        candidates.append(inner)
    for raw in candidates:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            if "writer_output" in obj and isinstance(obj["writer_output"], dict):
                return obj["writer_output"]
            # Treat as the inner payload directly.
            return obj
    return None


def _serialize_writer_output(inner: dict) -> str:
    """Re-serialize to match the canonical form: leading blank line + json fence."""
    return "\n```json\n" + json.dumps(inner, indent=2, ensure_ascii=False) + "\n```\n"


_SANITIZE_RULES: list[tuple[re.Pattern[str], str]] = [
    # 1. null followed by (GAP G\d+) / GAP G\d+
    (re.compile(r"\bnull\s*\(\s*GAP\s*G\d+\s*\)\s*(?:-\s*)?", re.I), ""),
    (re.compile(r",\s*GAP\s*G\d+\b", re.I), ""),
    (re.compile(r"\bGAP\s*G\d+\)?\s*(?:-\s*)?", re.I), ""),
    (re.compile(r"\(\s*GAP\s*G\d+\s*\)", re.I), ""),
    # 2. .bvps_path | .fcf_basis | .ev_ebitda_path
    (re.compile(r"\.(?:bvps_path|fcf_basis|ev_ebitda_path)\b", re.I), ""),
    (re.compile(r"\b(?:bvps_path|fcf_basis|ev_ebitda_path)\b", re.I), ""),
    # 3. (LOUD policy[^)]*)
    (re.compile(r"\s*\(\s*LOUD policy[^)]*\)", re.I), ""),
    (re.compile(r"\bLOUD policy\b[^,.;)]*", re.I), ""),
    # 4. payload tidak[^.]*\.
    (re.compile(r":?\s*payload\s+tidak\s+[^.]*\.", re.I), ""),
    # 5. Sectors /[a-z]+ total_count \d+
    (re.compile(r"\s*\(?\s*Sectors\s+/[a-z_]+\s+total_count\s+\d+\s*\)?", re.I), ""),
    # 6. interest_expense | operating_expense
    (re.compile(r"\b(?:interest_expense|operating_expense)\b", re.I), ""),
    # 7. duplicate (Q1-2025...) (Q1-2025...)
    (re.compile(r"(\(Q1-202[0-9][^)]*\))\s*\1", re.I), r"\1"),
]


def sanitize_copy(text: str) -> str:
    """Post-processing function that strips backend leaks from copy (Issue 9)."""
    if not isinstance(text, str) or not text.strip():
        return text
    res = text
    for pat, rep in _SANITIZE_RULES:
        res = pat.sub(rep, res)
    # Dedup any duplicate parenthesized phrases
    res = re.sub(r"(\([^\)]+\))\s*\1", r"\1", res)
    return re.sub(r"\s{2,}", " ", res).strip()


def sanitize_writer_output(data: Any) -> Any:
    """Recursively sanitize strings inside writer_output data."""
    if isinstance(data, str):
        return sanitize_copy(data)
    if isinstance(data, dict):
        return {k: sanitize_writer_output(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_writer_output(v) for v in data]
    return data


def _normalize_flags(declared: Any) -> list[str]:
    """Coerce declared gate_flags into a list[str]. Models emit lists, lists of
    dicts, JSON strings, or null. We only keep strings."""
    out: list[str] = []
    if declared is None:
        return out
    if isinstance(declared, str):
        # Either a JSON array literal or a single flag. Try json first.
        try:
            parsed = json.loads(declared)
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, str)]
        except json.JSONDecodeError:
            # treat as a single-string flag
            return [declared]
    if isinstance(declared, list):
        for x in declared:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                out.append(json.dumps(x, ensure_ascii=False))
    return out


def _flag_for_conceded_rung(rung: dict) -> str:
    """One required_flag per conceded rung - mirrors the audit's own format so a
    human reader sees the same string whether it came from the audit or was
    injected into the deck."""
    label = (rung.get("label") or "rung").strip() or "rung"
    fv = rung.get("fair_value")
    basis = (rung.get("basis") or "").strip()
    fv_str = f"Rp {fv:,.0f}" if isinstance(fv, (int, float)) else "n/a"
    if basis:
        return f"DISSENT (anchor conceded on '{label}' = {fv_str}; basis: {basis[:120]})"
    return f"DISSENT (anchor conceded on '{label}' = {fv_str})"


def _compute_non_anchored_fvs(
    ladder: list[dict],
    target_price: float,
    anchor_value: float | None,
) -> list[dict]:
    """Surface every computed rung that is not the published anchor.

    Returns a list of {label, basis, fair_value, delta_pct, contested} so the
    cover paragraph can show the bear/mid/bull range instead of one number.
    """
    out: list[dict] = []
    if not isinstance(target_price, (int, float)) or target_price <= 0:
        return out
    for r in ladder or []:
        fv = r.get("fair_value")
        if not isinstance(fv, (int, float)):
            continue
        if anchor_value is not None and abs(fv - anchor_value) < 1e-6:
            continue  # that's the anchor itself; skip
        delta = (fv - target_price) / target_price * 100.0
        out.append(
            {
                "label": r.get("label") or "",
                "basis": r.get("basis") or "",
                "fair_value": round(float(fv), 2),
                "delta_from_tp_pct": round(delta, 2),
                "contested": bool(r.get("contested")),
            }
        )
    # Sort ascending so reader sees bear -> bull
    out.sort(key=lambda x: x["fair_value"])
    return out


def apply_audit_to_state(state: dict[str, Any], price: float | None = None) -> dict[str, Any]:
    """Inject the audit's results into the writer_output deliverable.

    Idempotent: re-running on the same state makes no further changes
    (required_flags are appended only if not already present).

    Returns the modified state copy. The original state is not mutated.
    Returns the original state unchanged when writer_output is missing or
    cannot be parsed (a real failure here would break the publish gate).
    """
    if not isinstance(state, dict):
        return state
    wo = state.get("writer_output")
    if not isinstance(wo, str):
        return state

    inner = _parse_writer_output(wo)
    if inner is None:
        logger.warning("post_audit_inject: writer_output did not parse; skipping")
        return state

    # Run the audit - no LLM in the loop.
    price_used = float(price) if price else 0.0
    try:
        result = _audit(state, price=price_used)
    except Exception as exc:  # noqa: BLE001 - injection must never break the run
        logger.warning("post_audit_inject: audit() raised (%s); skipping", exc)
        return state
    audit_dict = result.to_dict()

    declared = _normalize_flags(inner.get("gate_flags"))
    required = list(audit_dict.get("required_flags") or [])
    # Union, dedup, declared first (so original priority order is preserved)
    seen: set[str] = set()
    merged: list[str] = []
    for f in list(declared) + list(required):
        if not f or f in seen:
            continue
        seen.add(f)
        merged.append(f)
    inner["gate_flags"] = merged

    # Anchor sensitivity disclosure (Fix #2): when the anchor itself is
    # contested, the deck must show the bear/mid/bull ladder, not a point.
    anchor_contested = bool(audit_dict.get("anchor_contested"))
    if anchor_contested:
        target_price = inner.get("target_price")
        # Anchor = the rung closest to the published target (same rule as audit)
        ladder = audit_dict.get("ladder") or []
        anchor_value = None
        if isinstance(target_price, (int, float)) and ladder:
            try:
                pick = min(ladder, key=lambda r: abs(float(r.get("fair_value", 0)) - float(target_price)))
                if abs(float(pick.get("fair_value", 0)) - float(target_price)) / max(abs(float(target_price)), 1.0) <= 0.005:
                    anchor_value = float(pick.get("fair_value", 0))
            except Exception:  # noqa: BLE001
                anchor_value = None
        inner["non_anchored_fvs_disclosed"] = _compute_non_anchored_fvs(
            ladder, float(target_price or 0), anchor_value
        )
        # Add a structured anchor justification so the cover paragraph can
        # embed a single number-pair ("Anchor sensitivity: bear/bull Rp X/Y")
        # without picking text.
        flags = audit_dict.get("disclosure") or ""
        inner["anchor_justification"] = flags

        # Build a one-line disclosure the cover paragraph can paste verbatim.
        # Source every number from non_anchored_fvs_disclosed so the helper
        # never hardcodes a ticker-specific figure.
        non_anch = inner["non_anchored_fvs_disclosed"] or []
        if isinstance(target_price, (int, float)) and non_anch and len(non_anch) >= 2:
            low_rung = non_anch[0]
            high_rung = non_anch[-1]
            low_fv = low_rung["fair_value"]
            high_fv = high_rung["fair_value"]
            # Use the audit's own disclosure sentence as the starting point,
            # then append a numeric range from the actual ladder. The reader
            # gets the house signal AND the bear/mid/bull numbers.
            base = (audit_dict.get("disclosure") or "").strip()
            rng = (
                f"{base} Range surfaced from the computed ladder: lowest rung "
                f"Rp {low_fv:,.0f} (basis: {low_rung.get('basis','')[:80]}); highest "
                f"rung Rp {high_fv:,.0f} (basis: {high_rung.get('basis','')[:80]})."
            )
            # Stamp onto cover paragraphs (last paragraph preferred - decks append)
            cps = inner.get("cover_paragraphs") or []
            if isinstance(cps, list):
                # Idempotency: avoid duplicating on re-run
                if not any("Range surfaced from the computed ladder:" in (p or "") for p in cps):
                    cps.append(rng)
            else:
                cps = [rng]
            inner["cover_paragraphs"] = cps
            # Also stamp as a gate flag so any existing renderer that surfaces
            # dissent-aware flags gets the disclosure without code changes.
            rng_flag = (
                f"RANGE_DISCLOSURE: anchor TP Rp {target_price:,.0f} sits on a "
                f"conceded FY26F EBITDA projection; ladder low/high "
                f"Rp {low_fv:,.0f} / Rp {high_fv:,.0f} surfaced in cover_paragraphs[-1]"
            )
            if rng_flag not in inner["gate_flags"]:
                inner["gate_flags"] = [*inner["gate_flags"], rng_flag]

    # Sanitize backend leaks from copy before serialization
    inner = sanitize_writer_output(inner)

    # Re-serialize
    state["writer_output"] = _serialize_writer_output(inner)

    # Attach a synthetic audit summary so /api/report/{TICKER}/pdf and any
    # downstream caller can see the actual injection without re-running it.
    state["__audit__"] = {
        "verdict": audit_dict.get("verdict"),
        "reasons_count": len(audit_dict.get("reasons") or []),
        "required_flags": required,
        "missing_before": len(audit_dict.get("missing_flags") or []),
        "anchor_contested": anchor_contested,
        "injected_flags": len(merged) - len(declared),
    }
    return state


__all__ = [
    "apply_audit_to_state",
    "_parse_writer_output",
    "_serialize_writer_output",
    "sanitize_copy",
    "sanitize_writer_output",
]
