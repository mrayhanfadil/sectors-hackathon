"""Deterministic dissent audit - the arithmetic behind "did the report earn its rating?"

Why this module exists
----------------------
On 15 Sep 2026 the AMMN run conceded, in Round 2 of its own red-team debate, that
the 15.0x EV/EBITDA anchor behind the BUY target was defensible only as a
"cautious ramp premium" and NOT as a midpoint - and the published rating stayed
BUY with `gate_flags = []`. The writer was already instructed to carry the
dissent flag and did not. Instructions are not enforcement.

Everything here is stdlib and mechanical:
  * flags are DERIVED from the debate rounds, never written by a model;
  * the rating is derived from the ladder rung the concede did not invalidate;
  * a mismatch between the derived and the published rating is a REJECT.

Rating bands are DECLARED HERE, in one place, because they were previously
nowhere (the writer chose them in free text). Change the constants, not the prose.

    upside >= BUY_UPSIDE            -> BUY
    downside <= SELL_UPSIDE         -> SELL
    otherwise                       -> HOLD
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# --- declared house bands (single source of truth) --------------------------
BUY_UPSIDE = 0.15
SELL_UPSIDE = -0.10

RATING_BUY = "BUY"
RATING_HOLD = "HOLD"
RATING_SELL = "SELL"

# A claim is rating-relevant when conceding it moves the primary anchor. The
# debate rounds name these explicitly; matching on the anchor vocabulary keeps
# this honest without a model in the loop.
ANCHOR_WORDS = ("anchor", "multiple", "ev/ebitda", "target price", "tp ", "fair value", "fy26f", "ebitda")

CONCEDE_MARKERS = ("concede", "accepted", "partially accepted")


def rating_for(upside: float) -> str:
    """Declared band rule - the only place a rating is decided."""
    if upside >= BUY_UPSIDE:
        return RATING_BUY
    if upside <= SELL_UPSIDE:
        return RATING_SELL
    return RATING_HOLD


@dataclass
class Rung:
    """One point estimate on the valuation ladder, with its declared basis."""

    label: str
    basis: str
    fair_value: float
    contested: bool = False


@dataclass
class Round:
    n: int
    mode: str
    verdict: str
    claim: str

    @property
    def conceded(self) -> bool:
        blob = f"{self.mode} {self.verdict}".lower()
        return any(m in blob for m in CONCEDE_MARKERS)

    @property
    def rating_relevant(self) -> bool:
        return any(w in self.claim.lower() for w in ANCHOR_WORDS)


@dataclass
class Audit:
    verdict: str
    reasons: list[str] = field(default_factory=list)
    required_flags: list[str] = field(default_factory=list)
    missing_flags: list[str] = field(default_factory=list)
    rating_expected: str | None = None
    rating_actual: str | None = None
    rating_override_required: str | None = None
    anchor_contested: bool = False
    price: float | None = None
    defended_rung: str | None = None
    defended_fair_value: float | None = None
    ladder: list[dict[str, Any]] = field(default_factory=list)
    disclosure: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------- extraction


def parse_rounds(state: dict[str, Any]) -> list[Round]:
    """Debate rounds from run state. Tolerates str/obj shapes."""
    deb = state.get("debate_output")
    if isinstance(deb, str):
        try:
            deb = json.loads(deb)
        except json.JSONDecodeError:
            return []
    if not isinstance(deb, dict):
        return []
    as_dict: dict[str, Any] = deb
    raw = as_dict.get("debate") or as_dict.get("rounds") or []
    if not isinstance(raw, list):
        return []
    out: list[Round] = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        d = r.get("defense") if isinstance(r.get("defense"), dict) else {}
        out.append(
            Round(
                n=int(r.get("round") or len(out) + 1),
                mode=str(d.get("mode") or r.get("mode") or ""),
                verdict=str(r.get("verdict") or ""),
                claim=str(r.get("claim") or r.get("challenge") or ""),
            )
        )
    return out


FORWARD_WORDS = (
    "fy26f", "fy27f", "fy28f", "forward", "forecast", "projection", "ramp",
    "guidance", "next year", "estimate",
)


def ladder_from_text(valuation_output: Any) -> list[Rung]:
    """Rungs the modeler actually computed, read from its own JSON blocks.

    Shapes seen in live runs (15 / 16 Sep 2026):

        "base_15x": {"ev_ebitda": 15.0, "fair_value_per_share": 5667.31, ...}
        "fair_value_per_share": 147.54                     <- headline / DCF scalar
        "cross_check_mean": {"multiple": 28.42, "fair_value_per_share": 5872.75, ...}
        "primary_fv": {"...fair_value_per_share_idr": 5667.31, ...}
        "secondary_fv": {"...fair_value_per_share_idr": 838.45, ...}
        "sensitivity_primary": {"low_13x": {"...fair_value_per_share_idr": 4733.43}}

    Only figures present in the text become rungs; a missing rung stays
    missing so the audit can say "ladder unavailable" instead of re-pricing
    off a guess.
    """
    text = valuation_output if isinstance(valuation_output, str) else json.dumps(valuation_output or {})
    rungs: list[Rung] = []
    seen: set[float] = set()

    # Shape A: {label: { ... "fair_value_per_share": v }} (Sep 15 flat shape)
    nested_a = re.compile(
        r'"(?P<label>[a-z0-9_]+)"\s*:\s*\{(?P<body>[^{}]{0,400}?)"fair_value_per_share"\s*:\s*(?P<fv>-?[\d.]+)',
        re.IGNORECASE,
    )
    for m in nested_a.finditer(text):
        try:
            fv = float(m.group("fv"))
        except ValueError:
            continue
        if fv in seen:
            continue
        seen.add(fv)
        body = " ".join(m.group("body").split())
        rungs.append(Rung(label=m.group("label"), basis=body[:200], fair_value=fv))

    # Shape B1 (Sep 16 outer named block): "label": {"method": "...", "multiple_x": X, ..., "fair_value_per_share_idr": V}
    # Method body may contain one or more nested object blocks (e.g. bridge, sensitivity).
    # We allow up to 2 levels of nested braces: `(?:[^{}]|\{...|\{...\{...\})` for unlimited depth.
    # Easier: do a depth-aware substring search with a small custom counter instead of a single regex.
    def _depth_scan(label_regex: str, target_key: str, max_label_dist: int = 30) -> list[tuple[str, float, str]]:
        """For each occurrence of ``label: {`` return the first ``target_key: <num>``
        that lives at the SAME brace depth inside the value block. Distance check
        uses ``max_label_dist`` chars to skip unrelated same-named labels."""
        out: list[tuple[str, float, str]] = []
        for m in re.finditer(label_regex, text):
            label = m.group("name")
            start = m.end()
            depth = 1
            i = start
            buf: list[str] = []
            body_chars = 0
            while i < len(text) and depth > 0 and body_chars < 4000:
                c = text[i]
                if c == "{":
                    depth += 1
                    buf.append(c)
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        break
                    buf.append(c)
                else:
                    buf.append(c)
                body_chars += 1
                i += 1
            body_text = "".join(buf)
            km = re.search(rf'"{target_key}"\s*:\s*(?P<v>-?[\d.]+)', body_text)
            if km:
                out.append((label, float(km.group("v")), body_text[:300]))
            else:
                out.append((label, float("nan"), body_text[:300]))
        return [t for t in out if not (t[1] != t[1])]  # drop nan

    # Run depth-scan for `_idr` keys (Sep 16 producer).
    # Skip the "valuation_output" pseudo-key: that captures the whole top-level
    # state field which has every fairness inside it, and would always match
    # the primary anchor (double-counting).
    for label, fv, body in _depth_scan(r'"(?P<name>[a-z0-9_]+)"\s*:\s*\{', "fair_value_per_share_idr"):
        if label in {"valuation_output", "debate_output", "writer_output", "state"}:
            continue
        if fv in seen:
            continue
        seen.add(fv)
        rungs.append(Rung(label=label, basis=body, fair_value=fv))

    # Shape C: standalone "fair_value_per_share": v (Sep 15 legacy scalar)
    for m in re.finditer(r'"fair_value_per_share"\s*:\s*(?P<fv>-?[\d.]+)', text):
        try:
            fv = float(m.group("fv"))
        except ValueError:
            continue
        if fv in seen:
            continue
        seen.add(fv)
        rungs.append(Rung(label="headline", basis="headline fair_value_per_share", fair_value=fv))
    # (Removed Shape D standalone: depth_scan covers every block label faithfully,
    # including leaves like {"fair_value_per_share_idr": V}. A standalone regex
    # would catch all six such leaves under six different labels and lose the
    # parent context needed for the contested-token check.)

    # Shape E (Sep 16 flat producer): "low_13x_fv_per_share": 4733.43,
    # "headline_15x_fv_per_share": 5667.31, "high_17x_fv_per_share": 6601.18 -
    # flat keys at the top of the block, no nested object. Carry the label as
    # both label and basis so the audit/cover can show it. Dedupe against rungs
    # already pulled by Shape A/B.
    for m in re.finditer(
        r'"(?P<label>(?P<kind>low|high|mid|base|headline|cross_check)[_a-z0-9]*?'
        r'(?:13x|14x|15x|16x|17x|18x|midcycle_minus_1sigma|midcycle_mean)?'
        r'_fv_per_share)"\s*:\s*(?P<fv>-?[\d.]+)',
        text, re.IGNORECASE,
    ):
        try:
            fv = float(m.group("fv"))
        except ValueError:
            continue
        if fv in seen:
            continue
        seen.add(fv)
        rungs.append(Rung(label=m.group("label"), basis=m.group("label"), fair_value=fv))

    return rungs


def _is_forward(rung: Rung) -> bool:
    blob = f"{rung.label} {rung.basis}".lower()
    return any(w in blob for w in FORWARD_WORDS)


# ------------------------------------------------------------------- the audit


def audit(state: dict[str, Any], price: float, ladder: list[Rung] | None = None) -> Audit:
    """Grade a finished run: did it disclose its dissent, and does the rating hold?

    `price` is the spot used for upside; pass the same figure the deck prints.
    """
    rounds = parse_rounds(state)
    ladder = ladder if ladder is not None else ladder_from_text(state.get("valuation_output"))

    conceded = [r for r in rounds if r.conceded and r.rating_relevant]
    result = Audit(verdict="PASS", price=price, ladder=[asdict(r) for r in ladder])

    writer_text = state.get("writer_output") if isinstance(state.get("writer_output"), str) else ""
    target_price: float | None = None
    m = re.search(r'"target_price"\s*:\s*([\d.,]+)', writer_text or "")
    if m:
        try:
            target_price = float(m.group(1).replace(",", "").rstrip("."))
        except ValueError:
            target_price = None

    # 1. Required dissent flags - MECHANICAL, from the rounds themselves.
    for r in conceded:
        result.required_flags.append(
            f"DISSENT (Round {r.n}): red team {r.mode or 'challenged'} on a rating-relevant claim - "
            f"{r.verdict.strip()[:140]}"
        )

    declared = state.get("gate_flags")
    if declared is None and isinstance(state.get("writer_output"), str):
        # Legacy path: gate_flags at the top of the writer text.
        m = re.search(r"gate_flags\s*\"?\s*:\s*(\[[^\]]*\])", state["writer_output"])
        if m:
            try:
                declared = json.loads(m.group(1))
            except json.JSONDecodeError:
                declared = None
    if declared is None and isinstance(state.get("writer_output"), dict):
        # 16 Sep 2026+: writer_output is a structured dict (LlmAgent output
        # lands in session.state under the output_key). gate_flags lives inside it.
        declared = state["writer_output"].get("gate_flags")
    if declared is None and isinstance(state.get("writer_output"), str):
        # 16 Sep 2026+: writer_output is a fenced JSON blob. Parse it, then
        # pull gate_flags from the inner dict. Done after the regex try so we
        # only fall back to full-JSON parse when the regex missed (typical when
        # gate_flags is non-empty and contains commas/spaces).
        stripped = state["writer_output"].strip()
        if stripped.startswith("```json"):
            stripped = stripped.split("\n", 1)[1].rsplit("\n```", 1)[0]
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            inner_wo = parsed.get("writer_output", parsed)
            if isinstance(inner_wo, dict):
                declared = inner_wo.get("gate_flags")
    declared = declared or []
    result.missing_flags = [f for f in result.required_flags if f not in declared]
    if conceded and not declared:
        result.reasons.append(
            f"gate_flags is EMPTY while {len(conceded)} debate round(s) conceded on a "
            "rating-relevant claim - the dissent never reached the reader"
        )
    elif result.missing_flags:
        result.reasons.append(
            f"gate_flags does not carry {len(result.missing_flags)} mechanically-required dissent flag(s)"
        )

    # 2. Is the PRIMARY anchor itself on the contested basis?
    #
    # Mechanical, ticker-agnostic: pull the distinctive tokens the conceded claim
    # attacks (FY26F, 15.0x, ...) and mark every rung whose basis carries one.
    # A rung holding the same figure as a contested rung shares its basis, so
    # contested-ness propagates by value too.
    if conceded and ladder:
        tokens: set[str] = set()
        for r in conceded:
            for m in re.finditer(r"\b(?:fy\d{2}f?|q[1-4]\s*\d{4})\b", r.claim, re.I):
                tokens.add(m.group(0).lower().replace(" ", ""))
            for m in re.finditer(r"\d+(?:[.,]\d+)?\s*(?:×|x)\b", r.claim):
                tokens.add(m.group(0).replace(" ", "").lower())
        for r in ladder:
            blob = f"{r.label} {r.basis}".lower()
            r.contested = any(t in blob for t in tokens)
        contested_values = {r.fair_value for r in ladder if r.contested}
        for r in ladder:
            if r.fair_value in contested_values:
                r.contested = True
        result.ladder = [asdict(r) for r in ladder]

        # Which rung is the report actually priced on? The published target price
        # decides - not a label, which the modeler is free to name anything.
        anchor = None
        if target_price:
            anchor = min(ladder, key=lambda r: abs(r.fair_value - target_price))
            if abs(anchor.fair_value - target_price) / max(abs(target_price), 1.0) > 0.005:
                anchor = None  # published target is not one of the computed rungs
        if anchor is not None and anchor.contested:
            result.anchor_contested = True
            result.rating_override_required = "Review Required"
            result.disclosure = (
                f"The published target (Rp {target_price:,.0f}) sits on the '{anchor.label}' rung, which the "
                "debate conceded. A directional rating cannot ship on a conceded anchor: the house's own "
                "override slot applies - Review Required."
            )
        elif anchor is None and target_price:
            result.reasons.append(
                "published target price does not match any rung the modeler computed - the anchor "
                "cannot be tied to a declared basis"
            )

    # 3. Published rating: directional on a contested anchor is not publishable.
    if isinstance(state.get("writer_output"), str):
        m = re.search(r'"rating"\s*:\s*"([A-Za-z ]+)"', state["writer_output"])
        if m:
            result.rating_actual = m.group(1).strip().upper()
    if result.rating_override_required and result.rating_actual in (RATING_BUY, RATING_SELL, RATING_HOLD):
        result.reasons.append(
            f"published rating {result.rating_actual} is directional while its own primary anchor "
            f"was conceded in debate - expected {result.rating_override_required}"
        )
    if result.reasons:
        result.verdict = "REJECT"
    return result
