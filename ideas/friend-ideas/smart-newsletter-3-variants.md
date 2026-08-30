# Smart Newsletter — 3 variants evaluated + track-placement decision

> Submitted by Fadil's friends as a portfolio-personalized agent idea with 3 concrete variants. Evaluated 2026-08-30 by 1 `agy --model gemini-3.7-flash-high --effort high` invocation. Verdict below.

**TL;DR — pick Variant 2 ("Macro-to-Micro" Translator).**

| Variant | Final Track | F3 Score | Differentiation | Verdict |
|---|---|---|---|---|
| 1 — Portfolio Weather Report | **T02 Automation** | 3.40 / 5.00 | ~60% overlap | ⚠️ Weak differentiation from existing `Porto Copilot` / `EOD digest` / `BookGuard` |
| 2 — Macro-to-Micro Translator | **T01 AI Agents** | **4.50 / 5.00** | ~45% overlap (lowest) | ✅ **WINNER** — bridges macro news → portfolio wallet impact |
| 3 — Alpha Seeker Screener | **T03 Market Intel** | 3.50 / 5.00 | >75% overlap | ❌ Duplicates `DividenSehat` / `DivTrap-Shield` heavily |

---

## Why Variant 2 wins

- **Lowest overlap with existing 33 ideas** (~45%). Existing macro ideas (`BI-Rate Shockwave Simulator`, `Rupiah FX Pass-Through Screener` from batch 3) are **universe-wide screeners** — Variant 2 is **portfolio-personalized** macro impact analysis.
- **Highest F3 score**: R 4.5 + V 4.5 + T 4.5 (perfectly balanced — judges' weighted formula `(0.4·R + 0.3·V + 0.3·T) = 4.5`).
- **Clean Track 01 disqualification survival**: uses LangGraph-style multi-step orchestration + deterministic financial stress-test math (interest coverage, debt-to-equity), not a generic LLM prompt wrapper.
- **Strong video hook**: "BI just raised rates. Here's exactly what that means for your portfolio." — naturally cinematic.
- **Real pain in Indonesia**: ~25M retail investors hear BI Rate news monthly but can't translate it to their specific holdings.

---

## Track-placement details (all 3 variants)

### Variant 1 — Portfolio Weather Report
- **Final track:** Track 02 — Automation & Workflows
- **Pattern:** Recurring cron, autonomous trigger, no human click per run
- **Stack:** CF Worker + Cron Trigger + D1/Supabase (user holdings) + Resend/Telegram Bot API
- **Endpoints:** `/v2/transaction/daily/`, `/v2/ranking/top-changes/`, `/v2/company/report/`
- **F3 score 3.40** — Real-world OK but video wow + tech depth weak (looks like "cron + LLM template")
- **Honest risk:** judges may see it as "a glorified cron job that dumps API JSON into an LLM prompt template"

### Variant 2 — Macro-to-Micro Translator (WINNER)
- **Final track:** Track 01 — AI Agents & Assistants
- **Pattern:** Event-triggered agent loop, multi-step planning, deterministic stress-test math
- **Stack:** FastAPI + LangGraph + Next.js/Streamlit UI + Sectors REST
- **Endpoints:** `/v2/company/report/{symbol}/`, `/v2/company/quarterly-financials/`, `/v2/companies/?where=der<...`
- **F3 score 4.50** — Strong on all 3 dimensions
- **Honest risk:** LLM hallucination on financial math if not deterministic — mitigation: enforce Python-tool math, not LLM-generated formulas

### Variant 3 — Alpha Seeker Goal-Based Screener
- **Final track:** Track 03 — Market Intelligence
- **Pattern:** Continuous background scan, trigger when match
- **Stack:** Next.js/Streamlit + Sectors screener + LLM narrative
- **Endpoints:** `/v2/companies/`, `/v2/company/report/`, `/v2/company/quarterly-financials/`, `/v2/screener/free-float/`
- **F3 score 3.50** — Alert fatigue risk, screener UX is not novel
- **Honest risk:** >75% overlap with existing `DividenSehat` and `DivTrap-Shield` — flagged as **weak differentiation**

---

## Full eval

Below is the unedited AGY output for reference (track placements, disqualification survival, overlap analysis, effort, weaknesses).

---

$(cat /tmp/agy-out/smart-newsletter-eval.md)
