"""ADK narrative writer - paragraph 2 as flowing plain-Indonesian prose.

One agent, one job: take the verified fact sheet for the News/Sentimen/Katalis section
and write it as prose a lay reader can follow. The agent carries the writer role's
instructions (`agents/adk/agents/instructions.py::writer_instruction` +
`KATALIS_NARRATIVE_RULE`); this module runs that role standalone so refreshing the
narrative costs one model call instead of a full 11-agent report run.

Freeze contract: the result lands in `data/narrative/<TICKER>_katalis.json` together with
the fact-sheet hash, so `server/report/slide2.build_katalis` uses it only while the facts
are unchanged. New facts -> the artifact is stale by definition -> the deck falls back to
the deterministic template and discloses `narrative_source: template_fallback`.

The written prose is checked against the gate BEFORE it is frozen
(`server.report.house_rules.audit_katalis_narrative`): a narrative that invents a figure,
uses method jargon, or overruns the page budget never reaches the deck.

Usage:
    python -m agents.adk.narrative_runner --ticker AMMN
    python -m agents.adk.narrative_runner --ticker AMMN --dry-run    # print the prompt, no model call
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.report.narrative_facts import (  # noqa: E402
    build_katalis_facts,
    fact_numbers,
    facts_hash,
    narrative_path,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "katalis_narrative_writer"


def load_facts(ticker: str) -> tuple[dict, str]:
    """The fact sheet the RENDERER saw, plus the hash it computed for it.

    Read back from the payload rather than re-derived: the render path sanitises a few
    reader-facing strings on the way out (it strips the internal gap code), so a second
    derivation produces a different hash and a frozen narrative could never match the
    render that is supposed to use it. Freezing against the renderer's own sheet makes
    agreement structural instead of hopeful.
    """
    from server.routers.pdf import _build_live_payload

    payload = _build_live_payload(ticker.upper(), None)
    katalis = ((payload.get("cover") or {}).get("slide2") or {}).get("katalis") or {}
    facts, render_hash = katalis.get("facts"), katalis.get("facts_hash")
    if isinstance(facts, dict) and facts and render_hash:
        return facts, str(render_hash)

    # Fallback for a payload built by an older code path: derive it and say so.
    chart = (payload.get("cover", {}).get("slide1") or {}).get("jci_chart")
    facts = build_katalis_facts(payload, chart)
    logger.warning("payload carried no render-side fact sheet - derived one instead")
    return facts, facts_hash(facts)


def build_prompt(ticker: str, facts: dict) -> str:
    """The writer's brief: the fact sheet plus the hard framing."""
    return (
        f"Ticker: {ticker.upper()}\n"
        "Section: paragraph 2 of the cover spread - heading \"News, Sentimen & Katalis\".\n\n"
        "Here is the VERIFIED fact sheet. It is the only thing you may state; every figure\n"
        "you print must appear in it, restated as-is (Indonesian decimals, exact units).\n\n"
        f"```json\n{json.dumps(facts, ensure_ascii=False, indent=2)}\n```\n\n"
        "Write the section now: 2-3 short paragraphs of flowing plain Indonesian prose for a\n"
        "lay reader, following the NARRATIVE RULE in your instructions. Keep the mandated\n"
        "\"Priced-in\" verdict with the EV/EBITDA comparison. Target 1000-1100 characters\n"
        "(hard cap 1200): the cover spread shares one page with the Key Financials exhibit.\n\n"
        "Some facts carry a `*_note` field. Those notes spell out the verified reading of the\n"
        "raw fields next to them - restate the note as written and never recombine raw fields\n"
        "into a new claim of your own (e.g. do not turn a stake gain and a price into \"posisi\n"
        "naik X% menjadi Rp Y\").\n\n"
        "Two things the sheet contains that are NOT copy: the `source` strings (they are our\n"
        "provenance - if you credit a source, name the publisher plainly, e.g. \"keterbukaan\n"
        "IDX\" or \"rilis perusahaan\") and the internal gap code in `impact_gap`. When a figure\n"
        "cannot be quantified, say it in plain words (\"datanya belum ada, jadi angkanya belum\n"
        "bisa dihitung\") - never cite the code, and never the words pipeline, payload, cache\n"
        "or freeze.\n\n"
        'Answer with JSON only: {"paragraphs": ["...", "..."]}'
    )


async def _run_agent(ticker: str, prompt: str) -> str:
    """Run the writer-role LlmAgent once and return its raw text."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    from .agents.instructions import writer_instruction
    from .app import _deepseek_or_gemini

    from google.adk.agents.llm_agent import LlmAgent

    agent = LlmAgent(
        name=AGENT_NAME,
        model=_deepseek_or_gemini(),
        description="Writes paragraph 2 as flowing plain-Indonesian prose from a verified fact sheet.",
        instruction=writer_instruction.replace("{ticker}", ticker.upper()),
        output_key="katalis_narrative",
    )
    runner = Runner(app_name="sectors-narrative", agent=agent,
                    session_service=InMemorySessionService())
    session = await runner.session_service.create_session(
        app_name="sectors-narrative", user_id="narrative_runner")
    message = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])
    text = ""
    async for event in runner.run_async(user_id="narrative_runner",
                                        session_id=session.id, new_message=message):
        content = getattr(event, "content", None)
        for part in (getattr(content, "parts", None) or []):
            if getattr(part, "text", None):
                text += part.text
    return text


_PLAN_LINE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s|^\s*(?:let me|here is|here's|i'll|i will|sure|"
                        r"paragraph \d|final|draft|output|length|total|revisi|revised)\b|"
                        r"\b(?:char|chars|character|karakter)\b|:\s*$", re.I)


def _clean_paragraph(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)      # drop markdown bold
    text = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _json_paragraphs(raw: str) -> list[str]:
    """Every `{"paragraphs": [...]}` object in the answer, first valid one wins."""
    for m in re.finditer(r"\{[^{}]*\"paragraphs\"[^{}]*\}", raw, re.S):
        try:
            doc = json.loads(m.group(0))
        except Exception:
            continue
        paras = [str(p).strip() for p in (doc.get("paragraphs") or []) if str(p).strip()]
        paras = [p for p in paras if 40 <= len(p) <= 1400]
        if paras:
            return paras
    return []


def parse_paragraphs(raw: str) -> list[str]:
    """Pull the paragraphs out of the writer's answer, refusing anything else.

    Accepted shapes, in order: a `{"paragraphs": [...]}` object (the instructed
    format), then prose that is clearly prose. Everything else - a planning dump, a
    character-count bookkeeping block, a refusal - returns [] and the caller retries
    once, then fails. Freezing the model's notes as if they were the paragraph is the
    failure mode this guards: a 28k planning dump once passed a looser parser.
    """
    paras = _json_paragraphs(raw)
    if paras:
        return paras

    lines = [ln for ln in raw.splitlines() if ln.strip() and not _PLAN_LINE.match(ln)]
    prose = " ".join(lines).strip()
    if not prose or len(prose) > 1600:
        return []
    if re.search(r"\b(?:char|chars|character|karakter)\b", prose, re.I):
        return []
    blocks = [b for b in re.split(r"\n\s*\n", prose) if b.strip()]
    out = [_clean_paragraph(b) for b in blocks]
    return [p for p in out if 100 <= len(p) <= 1400]


def tighten_prompt(paragraphs: list[str], target: int) -> str:
    """The bounded tighten ask: same facts, fewer words, a concrete number to hit."""
    draft = "\n\n".join(paragraphs)
    return (
        f"Your draft below is {len(' '.join(paragraphs))} characters; the hard limit is {target}.\n"
        "Rewrite it so the TOTAL is at most "
        f"{target} characters, keeping every figure and the Priced-in verdict, and dropping "
        "the least important detail first (dates, transaction counts, one of the two "
        "performance windows). Do not add anything new.\n\n"
        f"--- draft ---\n{draft}\n--- end draft ---\n\n"
        'Answer with JSON only: {"paragraphs": ["...", "..."]}'
    )


def gate_violations(paragraphs: list[str], facts: dict) -> list[str]:
    """Run the render gate on the candidate BEFORE freezing it."""
    from server.report.house_rules import NARRATIVE_MAX_CHARS, audit_katalis_narrative

    body = " ".join(paragraphs)
    payload = {
        "narrative_source": "writer_frozen",
        "body": body,
        "narrative_provenance": {
            "allowed_numbers": sorted(fact_numbers(facts)),
            "catalyst_names": [c.get("name") for c in (facts.get("catalysts") or [])],
        },
    }
    return audit_katalis_narrative(payload)


def freeze(ticker: str, paragraphs: list[str], facts: dict, model: str,
           render_hash: str | None = None) -> Path:
    """Write the artifact the render path reads, with its provenance."""
    path = narrative_path(ticker, "katalis")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "section": "katalis",
        "ticker": ticker.upper(),
        "paragraphs": paragraphs,
        "facts_hash": render_hash or facts_hash(facts),
        "generated_by": f"{AGENT_NAME} (google-adk LlmAgent, writer role)",
        "instruction_rule": "KATALIS_NARRATIVE_RULE",
        "model": model,
        "run_id": f"{AGENT_NAME}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chars": len(" ".join(paragraphs)),
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write paragraph 2 as plain-Indonesian prose (ADK writer role).")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the prompt, make no model call")
    ap.add_argument("--force", action="store_true", help="freeze even if the gate complains (not recommended)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from server.report.house_rules import NARRATIVE_MAX_CHARS

    ticker = args.ticker.upper()
    facts, render_hash = load_facts(ticker)
    prompt = build_prompt(ticker, facts)
    if args.dry_run:
        print(prompt)
        return 0

    model = os.getenv("ADK_MODEL_LABEL") or os.getenv("ADK_PROVIDER") or "provider-default"
    raw = asyncio.run(_run_agent(ticker, prompt))
    paragraphs = parse_paragraphs(raw)
    if not paragraphs:
        # One bounded retry, and the retry is explicit about the shape: a model that
        # answered with planning notes ("Paragraph 1 ... (1.137 chars)") has not done
        # the job, and freezing its notes is the failure mode this prevents.
        logger.info("no parsable paragraphs - re-asking once for the JSON answer only")
        raw = asyncio.run(_run_agent(
            ticker,
            prompt + "\n\nReminder: answer with the JSON object only - no plan, no bullets, "
                     "no character counts, no commentary before or after it."))
        paragraphs = parse_paragraphs(raw)
    if not paragraphs:
        print("FAIL: the writer returned no parsable paragraphs. Raw answer follows:\n")
        print(raw[:2000])
        return 2

    violations = gate_violations(paragraphs, facts)
    if any("over the" in v for v in violations):
        # A model asked for "1000-1100 characters" routinely returns 1200-1600: counting is
        # not its strength, so the runner does the counting and asks once, with the draft and
        # a concrete number. The gate re-runs on the result, so a tighter draft that invents a
        # figure or drops the mandate is still rejected.
        logger.info("over the page budget (%d chars) - asking for a tighter draft once",
                    len(" ".join(paragraphs)))
        raw2 = asyncio.run(_run_agent(ticker, tighten_prompt(paragraphs, NARRATIVE_MAX_CHARS - 50)))
        tighter = parse_paragraphs(raw2)
        if tighter:
            v2 = gate_violations(tighter, facts)
            if len(v2) < len(violations):
                paragraphs, violations = tighter, v2
    if violations:
        print(f"FAIL: {len(violations)} gate violation(s) - narrative not frozen:")
        for v in violations:
            print("  -", v)
        if not args.force:
            return 3
        print("(--force: freezing anyway)")

    path = freeze(ticker, paragraphs, facts, model, render_hash=render_hash)
    print(f"frozen {path.relative_to(ROOT)}")
    print(f"  paragraphs: {len(paragraphs)} | chars: {len(' '.join(paragraphs))} "
          f"| facts_hash: {render_hash} | model: {model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
