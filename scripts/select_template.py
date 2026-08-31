"""Template switch logic — decides which of the 4 report templates to render (T10 task item 2).

Pure function, no I/O. Mirrors plan.md §5:
    if segments>1 -> sotp, elif subsector infra/telco -> infra, else single
    strategy is NEVER auto-selected: it is an explicit overlay passed by the orchestrator.
"""
from __future__ import annotations

INFRA_KEYWORDS = ("infra", "telco", "tower", "fiber", "toll", "telekomunikasi", "telecommunication")


def select_template(report_data: dict) -> tuple[str, str]:
    """Return (template_name, reason).

    Precedence (revised 31 Aug 2026 after empirical check — see DATA_CONTRACT.md):
      1. meta.template explicit override (orchestrator's call wins)
      2. subsector infra/telco -> infra   (BEFORE segments: every real telco reports
         segments, so segments-first dead-codes the infra template for MTEL/TOWR-type
         names, which need the KPI hero + blended + bands sections)
      3. segments > 1 -> sotp              (conglomerate: CDIA/ADRO)
      4. else -> single                    (pure-play: RATU)
    'strategy' is never auto-selected: explicit overlay passed by the orchestrator.
    """
    meta = report_data.get("meta") or {}
    if meta.get("report_kind") == "strategy" or (report_data.get("strategy") and not meta.get("ticker")):
        return "strategy", "explicit overlay (market-level report) — never auto-selected"

    override = meta.get("template")
    if override in ("single", "sotp", "infra", "strategy"):
        return override, f"meta.template override -> {override}"

    subsector = (meta.get("subsector") or meta.get("sector") or "").lower()
    if any(k in subsector for k in INFRA_KEYWORDS):
        return "infra", f"subsector '{subsector}' matches infra/telco keywords (precedence over segments)"

    segments = report_data.get("segments") or []
    if len(segments) > 1:
        return "sotp", f"segments={len(segments)} > 1 -> sotp"

    return "single", "segments<=1 and no infra/telco match -> single"


def main() -> None:
    import json
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("usage: select_template.py <report_data.json>")
        raise SystemExit(2)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    template, reason = select_template(data)
    print(json.dumps({"template": template, "reason": reason}, ensure_ascii=False))


if __name__ == "__main__":
    main()
