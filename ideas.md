# Ideas & Track Decision

> **Decision tracker.** We pick exactly one track before writing project code (see [`submission-checklist.md`](submission-checklist.md) Week 1). The brainstorming below is intentionally raw — judges see the final product, not this file.

---

## How to pick

Quick decision rubric (each 0–5):

| Criterion | AI Agents | Automation | Market Intel |
|---|---|---|---|
| How obviously can a real Indonesian use this today? | 4 | 5 | 4 |
| How well does it play to our existing stack (Hermes, NucBox, Cloudflare, Telegram bots)? | 5 | 5 | 4 |
| How *visible* is the Sectors data dependency (judges' "remove Sectors → does it break?" test)? | 5 | 5 | 4 |
| How realistic in 4 weeks for a solo/small team? | 3 | 4 | 4 |
| How exciting will the 3-min judging video be? | 5 | 3 | 4 |

(Totals are personal gut feel — fill in your own.)

**Honest take:** Automation is the most reliable path to a "real person can use it today" product. AI Agents is the most video-exciting but is the highest-risk because the disqualification bar is strict (no off-the-shelf wrappers). Market Intelligence is the middle ground: easier to prove technical depth, easy to demo visually.

---

## Track 01 — AI Agents & Assistants ideas

Each must satisfy "if Sectors data is removed, the product breaks."

1. **"Saham Jujur" — single-ticker due diligence agent.**
   Input: ticker (BBCA, BMRI, TLKM…). Output: structured 5Y revenue trend, profitability vs sector peers, dividend track record, recent disclosures — each answer clickable back to the Sectors endpoint it came from. Citations are mandatory; the user can audit every claim.
   Why it works: clearly an agent (multi-step tool calls, memory of which sub-questions the user already asked), clearly Sectors-core (no ticker → no useful answer), clearly auditable (great judging video).

2. **"Porto Copilot" — held-ticker briefing bot.**
   Input: list of tickers the user owns. Output: daily briefing — peer comp moves, sector rotation, any ticker with material new filings.
   Why it works: memory/state (the user's holdings list), recurring workflow (a daily check), custom tool routing (per-ticker fetch).

3. **"DD for Small Caps" — research agent for thinly-covered IDX names.**
   For IDX small/mid caps with thin coverage, an agent that pulls fundamentals, peer-ranks them, surfaces anomalies vs sector.

---

## Track 02 — Automation & Workflows ideas

Each must satisfy "fires automatically, no human click required."

1. **Pre-market brief Telegram bot.** Cron at 08:00 WIB trading days. Pulls sector signals (top movers, breadth, volume anomalies) from Sectors, assembles a short Telegram message, pushes to subscribers.
   Why it works: trigger = time, output is useful at 08:01 WIB, Sectors-core, easy to demo by showing the morning's message.

2. **Disclosure watcher.** Fires when a watched ticker posts a new event (material disclosure, ownership change, dividend announcement). One-line alert to a Slack channel.

3. **Screener-of-the-day.** A different custom screener runs each day, posts top 10 results to Discord/Telegram channel.

4. **EOD portfolio digest.** 16:30 WIB cron, computes moves vs yesterday's close, posts summary to Telegram/WA.

---

## Track 03 — Market Intelligence ideas

Each must satisfy "adds interpretation on top of raw data, not just re-presentation."

1. **"Dividend Consistency Score"** — cross-sector screener scoring IDX companies on dividend continuity / payout ratio / yield vs history. Output: ranked table.
2. **Sector rotation radar** — weekly comparative view across IDX sectors showing momentum (price + breadth + volume delta).
3. **Material-change detector** — flags tickers where fundamentals moved >N std-dev vs trailing 90 days (revenue surprise, ROE shift, leverage jump).
4. **Liquidity / ownership-concentration screener** — surfaces low-float or high-concentrated-ownership names retail should know about.

---

## What we haven't picked yet (gaps to fill)

- [x] ~~One-sentence problem statement~~ — see template below; drafted for every idea.
- [ ] **Audience validation** — who is the first person we'd show this to, and would they actually use it tomorrow? If we can't name them, the idea isn't ready.
- [x] ~~Sectors API/MCP coverage check~~ — see `references/rest-idx-mining-2026-08-29/` + `references/mcp-idx-mining-2026-08-29/`.
- [x] ~~Risk register~~ — see template below.
- [x] ~~Stack decision matrix~~ — see template below.

---

## Templates

### One-sentence problem statement

Use this format. Two hard rules:

1. **One sentence.** No compound sentences with "and".
2. **Start with the audience, end with the outcome.** "Indonesian X need Y so they can Z."

**Strong examples (from `tracks/idea-scoring.md`):**

> "Asing Radar adalah bot Telegram harian yang menunjukkan 10 saham IDX dengan net foreign flow tertinggi dan 10 terendah, supaya investor ritel Indonesia punya sinyal institusional tanpa harus berlangganan Bloomberg."

**Test your statement against these questions:**
- Can a stranger read it once and understand who the user is?
- Is the value obvious, or do you need to explain industry jargon?
- Would a judge say "ah yes, real problem" within 5 seconds of reading?

### Risk register (per candidate idea)

Fill one row per candidate. Pick the idea with the lowest #1 risk.

| # | Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation |
|---|---|---|---|---|
| 1 | _biggest thing that could make us fail to ship by 30 Sep_ | | | |
| 2 | | | | |
| 3 | | | | |

**Common risk patterns to look for:**
- "We don't know the Sectors API well enough" → H if idea needs ≥3 endpoints, M if ≤2.
- "We need video production skills we don't have" → M (mitigatable with screen-recording only, no fancy editing).
- "Credit budget blown" → M for Track 02 Automation, L for Track 03 with caching.
- "Onboarding incomplete at deadline" → H, mitigatable only by following [`onboarding-blocker.md`](onboarding-blocker.md).

### Stack decision matrix per track

| Track | Top 1 stack option | Top 2 stack option | Decision factor |
|---|---|---|---|
| **01 — AI Agents** | Python + LangGraph + `MultiServerMCPClient` (per `references/mcp/setup.md`) | Node + Vercel AI SDK + `@modelcontextprotocol/sdk` | Pick Python if your team knows it. Pick Node if you want a web frontend in the same codebase. |
| **02 — Automation — Telegram bot** | Cloudflare Worker + Cron Trigger + `node-telegram-bot-api` (free) | Cloudflare Worker + Cron + Webhook (no library) | Worker is free, cron is built-in. Either is fine. |
| **02 — Automation — n8n** | n8n Cloud (free tier) + Sectors MCP node | Self-hosted n8n + Sectors HTTP node | Self-hosted gives more control; cloud is faster to start. |
| **03 — Market Intelligence** | Streamlit (per `references/cookbook/sectorscan-part1.md`) | Next.js + Sectors REST | Streamlit for fastest demo; Next.js if you'll iterate post-hackathon. |

**Other valid stacks (no wrong answer):** Node + Express, Python + FastAPI, Cloudflare Workers (any language via Wrangler), Vercel Edge Functions. The matrix above is the **default-fast** option. Override if you have a strong reason.

---

## Decision (lock this section once chosen)

> **Track:** TBD
> **Idea:** TBD
> **One-sentence problem statement:** TBD
> **Intended audience:** TBD
> **Locked at:** TBD
