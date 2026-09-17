"""Audit-disclosure extractor (16 Sep 2026).

Ticker-agnostic. Reads the latest completed run's ``writer_output`` from
``data/agent_runs.db``, pulls out the dissent-aware fields the post-audit
injector (agents/adk/post_audit_inject.py) writes, and stamps them onto
``payload["cover"]["audit_disclosure"]`` so the renderer / templates can
show them in the deck.

Three fields land here:

  * ``gate_flags``                - list[str], every dissent / range flag
                                   the injector emitted. Always populated
                                   when the injector ran; may be empty
                                   if no round conceded.
  * ``non_anchored_fvs_disclosed`` - list[{label, basis, fair_value,
                                   contested, delta_from_tp_pct}]. The
                                   bear/mid/bull ladder. ONLY populated
                                   when the anchor itself was contested;
                                   a defend-mode debate leaves it null.
  * ``anchor_justification``      - str, the audit's own disclosure line.
                                   Same gating as the ladder.

The helper is best-effort: a missing or malformed writer_output yields
``{"present": False, "gate_flags": [], "ladder": [], "disclosure": None}``
and never raises. The PDF gate already runs upstream in
``server/routers/pdf.py:_publish_audit``; this module is purely an
editorial surface so the reader sees the same dissent the gate saw.

Public API:
  * ``extract_audit_disclosure(ticker: str) -> dict`` - read latest run.
  * ``apply_audit_disclosure(payload: dict, ticker: str) -> dict`` -
    stamp onto payload["cover"]["audit_disclosure"]. Mutates payload.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Regex that lifts the fenced JSON out of a writer_output raw text. The
# agent writes ```json\n{...}\n```; we want the inner object. Idempotent
# against multiple fences (picks the last one, which is the canonical
# writer_output the injector mutates).
_JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


def _parse_writer_output(raw: Any) -> dict | None:
    """Best-effort parse of writer_output. Returns inner dict or None.

    Tolerates:
      * writer_output already a dict (in-memory agent path)
      * writer_output a str with one or more ```json fences
      * writer_output a JSON-encoded str (no fences)
      * garbage / None - returns None
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return None
    fences = _JSON_FENCE_RE.findall(raw)
    if fences:
        try:
            inner = json.loads(fences[-1])
        except (ValueError, TypeError):
            return None
        # The fenced inner may itself wrap the writer_output under its
        # own key (the agent emits `{"writer_output": {...}}`); unwrap
        # if so.
        if isinstance(inner, dict) and set(inner.keys()) == {"writer_output"}:
            return inner.get("writer_output") or {}
        return inner if isinstance(inner, dict) else None
    # No fence - try plain JSON
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if isinstance(parsed, dict) and set(parsed.keys()) == {"writer_output"}:
        return parsed.get("writer_output") or {}
    return parsed if isinstance(parsed, dict) else None


def extract_audit_disclosure(ticker: str) -> dict:
    """Pull dissent-aware fields from the latest completed run for ``ticker``.

    Returns:
      {
        "present": bool,             # was a run found at all
        "run_id": str | None,        # the run we read from
        "gate_flags": list[str],     # every DISSENT / RANGE_DISCLOSURE flag
        "ladder": list[dict],        # bear/mid/bull; [] when not contested
        "disclosure": str | None,    # anchor_justification; None when not set
        "verdict": str | None,       # saved __audit__.verdict
        "anchor_contested": bool,    # from saved __audit__
      }

    Never raises. A missing DB / no runs / malformed writer_output yields
    ``{"present": False, "gate_flags": [], "ladder": [], ...}``.
    """
    out = {
        "present": False,
        "run_id": None,
        "gate_flags": [],
        "ladder": [],
        "disclosure": None,
        "verdict": None,
        "anchor_contested": False,
    }
    try:
        # Use attribute access (not `from X import Y`) so tests can
        # monkeypatch server.storage.AgentRunStore to point at a
        # temporary DB without rebinding the imported name in this
        # module's namespace.
        from server import storage as _storage

        run = _storage.AgentRunStore().get_latest_completed(ticker)
    except Exception:
        return out
    if not run:
        return out
    state = run.get("state") or {}
    out["run_id"] = run.get("run_id")
    out["present"] = True
    # __audit__ is what the injector stamps; mirror its verdict + flag.
    audit = state.get("__audit__") or {}
    if isinstance(audit, dict):
        out["verdict"] = audit.get("verdict")
        out["anchor_contested"] = bool(audit.get("anchor_contested"))
    # gate_flags / ladder / disclosure live under writer_output.<key>.
    wo = _parse_writer_output(state.get("writer_output"))
    if isinstance(wo, dict):
        gf = wo.get("gate_flags")
        if isinstance(gf, list):
            out["gate_flags"] = [g for g in gf if isinstance(g, str)]
        lad = wo.get("non_anchored_fvs_disclosed")
        if isinstance(lad, list):
            # Sep 17 2026: the post_audit_inject.py normally populates
            # `delta_from_tp_pct` and `contested` on each row, but a manual
            # mutation (e.g. forcing anchor_contested for verification) may
            # have skipped the injector. Compute the derived fields here so
            # the template can render even when the injector did not run.
            target_price = wo.get("target_price")
            ladder_rows = []
            for r in lad:
                if not (
                    isinstance(r, dict)
                    and {"label", "basis", "fair_value"}.issubset(r.keys())
                ):
                    continue
                fv = r.get("fair_value")
                row = dict(r)
                if (
                    "delta_from_tp_pct" not in row
                    and isinstance(target_price, (int, float))
                    and target_price
                    and isinstance(fv, (int, float))
                ):
                    row["delta_from_tp_pct"] = round(
                        (float(fv) - float(target_price)) / float(target_price) * 100.0,
                        2,
                    )
                if "contested" not in row:
                    row["contested"] = bool(out.get("anchor_contested"))
                ladder_rows.append(row)
            out["ladder"] = ladder_rows
        aj = wo.get("anchor_justification")
        if isinstance(aj, str):
            out["disclosure"] = aj
    return out


def apply_audit_disclosure(payload: dict, ticker: str) -> dict:
    """Stamp the audit disclosure block onto ``payload["cover"]``.

    Idempotent - calling twice does not stack. The shape mirrors what
    ``extract_audit_disclosure`` returns so templates can read it
    directly without re-walking the DB. Never raises.

    Templates should iterate ``payload.cover.audit_disclosure.gate_flags``
    for the bullet list, ``payload.cover.audit_disclosure.ladder`` for
    the bear/mid/bull rows (only present when ``anchor_contested`` is
    True), and ``payload.cover.audit_disclosure.disclosure`` for the
    one-line prose anchor justification.
    """
    import server.report.audit_disclosure as _self

    cover = payload.setdefault("cover", {})
    try:
        block = _self.extract_audit_disclosure(ticker)
    except Exception:
        block = {
            "present": False,
            "run_id": None,
            "gate_flags": [],
            "ladder": [],
            "disclosure": None,
            "verdict": None,
            "anchor_contested": False,
        }
    cover["audit_disclosure"] = block
    return payload
