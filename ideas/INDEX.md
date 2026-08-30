# Ideas INDEX — Sectors Hackathon 2026

> Single ranked matrix for all brainstormed ideas across the repo. Source-of-truth detail lives in the original branch docs (linked below). This file is the **decision surface** — when you pick an idea, lock it in §7.

**Generated:** 2026-08-30
**Total ideas:** 31 across 4 source files (excluding 5 NEW ideas from F3 audit branch which is now deleted; can be recovered from local refs if needed)
**Tracks:** T01 (AI Agents), T02 (Automation), T03 (Market Intelligence)

---

## 1. Source files

| Source | File | Branch | # ideas |
|---|---|---|---|
| Original brainstorm | [`ideas.md`](../ideas.md) | `main` | 13 |
| AGY batch 2 (retail = institutional) | [`agy-9-retail-institutional.md`](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-retail-institutional-2026-08-30/ideas/agy-9-retail-institutional.md) | `idea/agy-retail-institutional-2026-08-30` | 9 |
| AGY batch 3 (niche / IDX-specific) | [`agy-9-niche.md`](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-niche-2026-08-30/ideas/agy-9-niche.md) | `idea/agy-niche-2026-08-30` | 6 |
| Friend's "Smart Newsletter" | [`smart-newsletter-3-variants.md`](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-niche-2026-08-30/ideas/friend-ideas/smart-newsletter-3-variants.md) | `idea/agy-niche-2026-08-30/ideas/friend-ideas/` | 3 variants |

---

## 2. Top 5 ranked (highest score / strongest differentiation / lowest overlap)

> Ranked by F3-style composite (Real-world usability 40% + Video wow 30% + Technical depth 30%) + differentiation penalty (lower overlap = higher rank).

| Rank | Idea | Track | Score | Source | Why it's strong |
|---|---|---|---|---|---|
| 🥇 1 | **Macro-to-Micro Translator** (Friend's Variant 2) | T01 AI Agents | **4.50** | `friend-ideas/smart-newsletter-3-variants.md` | Event-triggered agent that translates BI Rate / FX / inflation news into portfolio-specific wallet impact via deterministic debt/interest-coverage math. Lowest overlap (45%), cinematic video hook, clean Track 01 disqualification survival. |
| 🥈 2 | **Smart Money Divergence Radar** (Asing Radar variant) | T02 Automation | **8.13/10** | F3 audit (`tracks/idea-scoring.md`) | Daily 08:00 WIB pre-market Telegram bot showing top 10 net foreign inflow + top 10 outflow. Sectors-distinguishing dataset, perfect stack fit, one-message demo. F3 recommendation before friend's Variant 2 arrived. |
| 🥉 3 | **InsiderCompounder** | T03 Market Intel | ~7.5/10 (est.) | `agy-9-retail-institutional.md` | Custom thesis-as-code screener combining insider buying + ROE + free-float. Differentiated by personalization (user-defined thresholds) vs. generic screeners. |
| 4 | **DES-Guard** (OJK Sharia forced-divestment radar) | T03 Market Intel | ~7.0/10 (est.) | `agy-9-niche.md` | Cites actual OJK Regulation 35/POJK.04/2017 + Reksa Dana Syariah 10-30 day forced divestiture. Genuinely IDX-specific — Bloomberg can't replicate. High-judge-wow potential. |
| 5 | **BandarDivergence** (Smart Money Conviction Index) | T01 / T03 | ~6.5/10 (est.) | `agy-9-retail-institutional.md` | Composite signal correlating foreign broker flow percentiles + insider activity + valuation z-scores. Requires backtesting validation — eats Week 2 if pursued standalone. |

**Honest note on ranking:** scores are mixed (F3 audit uses /10 scale; AGY scores use /5). The ranked order is my judgment after reading all 31 ideas; treat as directional, not absolute.

---

## 3. Full ranked matrix (all 31 ideas)

> Per F3 rubric: R = Real-world usability (40%), V = Video wow (30%), T = Technical depth (30%). "Diff" = differentiator vs existing solutions. "Eff" = effort L/M/H.

### Track 01 — AI Agents & Assistants

| # | Idea | Source | R | V | T | Diff | Eff |
|---|---|---|---|---|---|---|---|
| 1 | Macro-to-Micro Translator | friend-variant-2 | 4.5 | 4.5 | 4.5 | Low overlap (45%) | M |
| 2 | Saham Jujur | `ideas.md` | 5 | 4 | 5 | Auditable citations | M |
| 3 | Bandar Radar | `agy-9-ideas.md` | 4 | 4 | 4 | Multi-source triangulation | M |
| 4 | Tambang Intel | `agy-9-ideas.md` | 3 | 3 | 4 | Ticker-to-concession mapping | M |
| 5 | ThesisBreak | `agy-9-retail-institutional.md` | 4 | 4 | 4 | Fundamental stop-loss (not price) | M |
| 6 | Conviction-Rebalancer | `agy-9-retail-institutional.md` | 3 | 3 | 4 | Insider-aligned sizing | M |
| 7 | ForeignFlow Divergence / Concentration | `agy-9-retail-institutional.md` | 3 | 3 | 4 | Portfolio flow risk | M |
| 8 | DD for Small Caps | `ideas.md` | 3 | 3 | 4 | Thin coverage angle | M |

### Track 02 — Automation & Workflows

| # | Idea | Source | R | V | T | Diff | Eff |
|---|---|---|---|---|---|---|---|
| 1 | Smart Money Divergence Radar (Asing Radar) | F3 audit + AGY | 5 | 4 | 4 | Foreign flow as Sectors-distinguishing data | L-M |
| 2 | Pre-market Foreign Flow & Commodity Radar | `agy-9-ideas.md` | 5 | 4 | 4 | Multi-signal morning brief | L |
| 3 | Pantau Orang Dalam | `agy-9-ideas.md` | 4 | 3 | 4 | Event-driven insider filings | L |
| 4 | Siaga Lapkeu IDX | `agy-9-ideas.md` | 4 | 3 | 3 | Earnings calendar | L |
| 5 | Portfolio Weather Report | friend-variant-1 | 4 | 3 | 3 | Multi-asset portfolio health | L |
| 6 | KursImpact | `agy-9-niche.md` | 4 | 4 | 4 | USD/IDR + sector sensitivity | M |
| 7 | KomoditasLokal | `agy-9-niche.md` | 3 | 3 | 3 | Commodity → IDX mapping | M |
| 8 | BI-Rate-Pulse | `agy-9-niche.md` | 4 | 3 | 3 | BI Rate calendar | L |
| 9 | Screener-of-the-day | `ideas.md` | 4 | 3 | 3 | Daily rotating screener | L |
| 10 | Disclosure watcher | `ideas.md` | 4 | 3 | 3 | Event-driven alerts | L |
| 11 | EOD portfolio digest | `ideas.md` | 3 | 2 | 3 | Daily PnL recap | L |

### Track 03 — Market Intelligence

| # | Idea | Source | R | V | T | Diff | Eff |
|---|---|---|---|---|---|---|---|
| 1 | InsiderCompounder | `agy-9-retail-institutional.md` | 4 | 4 | 5 | User-defined thresholds | L |
| 2 | DES-Guard | `agy-9-niche.md` | 4 | 5 | 5 | OJK POJK 35/2017 expertise | M |
| 3 | BandarDivergence | `agy-9-retail-institutional.md` | 4 | 4 | 5 | Multi-domain composite | M |
| 4 | YieldDurability | `agy-9-retail-institutional.md` | 4 | 3 | 4 | Yield-trap detector | L |
| 5 | ThematicExposureMap | `agy-9-retail-institutional.md` | 4 | 4 | 5 | Theme → ticker mapping | M |
| 6 | DividenSehat | `agy-9-ideas.md` | 4 | 3 | 5 | Composite dividend health score | L |
| 7 | Alpha Seeker Goal-Based Screener | friend-variant-3 | 3.5 | 3.5 | 3.5 | Goal-based filtering | L-M |
| 8 | DividenHunter | `agy-9-niche.md` | 4 | 4 | 4 | Yield-trap + dividend card | L |
| 9 | MoversRadar | `agy-9-niche.md` | 3 | 4 | 3 | Weekly recap card | L |
| 10 | Billionaire Watch IDX | `agy-9-niche.md` | 3 | 3 | 3 | Insider concentration card | M |
| 11 | TambangIntel | `agy-9-ideas.md` | 3 | 4 | 4 | Mining margin sensitivity | M |
| 12 | Smart Money Conviction Index | friend-variant-3 area | 3 | 3 | 4 | Conviction rating | M |

---

## 4. Disqualification risk per track (rules)

- **Track 01 — AI Agents:** judges disqualify "off-the-shelf AI client (Claude, OpenClaw, Hermes, etc.) + Sectors MCP with custom prompts alone." **Mitigation:** every Track 01 idea above uses ≥3 Sectors endpoints + custom math/state (citations, multi-agent, fundamental analysis). None is a pure wrapper.
- **Track 02 — Automation:** disqualification if "requires human click per run." **Mitigation:** every Track 02 idea above is cron-triggered or event-triggered.
- **Track 03 — Market Intelligence:** disqualification if "only displays raw Sectors data in a different visual form." **Mitigation:** every Track 03 idea adds a custom score/filter/composite signal.

---

## 5. Resource budget summary

Per [`credit-calculator.md`](../credit-calculator.md):

| Track / Idea type | Credits/day | 30-day | Headroom |
|---|---|---|---|
| Track 02 (cron, single signal) | 4-10 | 120-300 | ✅ comfortable |
| Track 02 (cron, multi-signal) | 50-80 | 1500-2400 | 🟡 tight without caching |
| Track 01 (per-query agent) | 5-6/query | ~150 queries | ✅ comfortable |
| Track 03 (weekly batch screener) | 5-10/week | 20-40 | ✅ very comfortable |

**Watch out:** Track 02 with full broker-summary per ticker runs out fast. Use universe-feed endpoints + 24h caching.

---

## 6. Final recommendation (TL;DR)

**Two finalists — pick one based on risk appetite:**

### Conservative pick: **Asing Radar** (Track 02 Automation, F3 audit recommendation)
- Daily 08:00 WIB Telegram bot, top 10 net foreign inflow + top 10 net outflow
- Sectors-CORE (removing Sectors breaks it)
- Existing F3 score: 8.13 / 10
- 4-week ship plan: bot skeleton → per-ticker loop → drill-down → videos + submit
- Lower ceiling but higher floor; everything except onboarding is reproducible
- **Best if:** you prioritize shipping, not differentiating from judges' expectations

### Moonshot pick: **Macro-to-Micro Translator** (Track 01 AI Agents, friend's Variant 2 winner)
- Event-triggered agent, translates macro news → portfolio wallet impact
- Cleanest disqualification survival (deterministic financial math, multi-step agent loop)
- F3 score: 4.50 / 5.00
- 4-week ship plan: build deterministic stress-test math + LangGraph agent + onboarding form
- Higher ceiling but requires disciplined engineering (no LLM hallucination on financial math)
- **Best if:** you want to win, not just submit

**My honest pick:** Macro-to-Micro Translator. The "BI Rate → your portfolio" framing is something Indonesian retail understands instantly, the video is naturally cinematic, and the Sectors-core test passes cleanly.

---

## 7. Lock-in (fill once decided)

> **Track:** TBD
> **Idea:** TBD
> **One-sentence problem statement:** TBD
> **Intended audience:** TBD
> **Locked at:** TBD
> **Locked by:** Fadiil (mrayhanfadil)
>
> After locking, run: `gh repo create` / portal registration, then `experiment/<track-slug>/` branch setup.

---

## 8. Cleanup checklist before onboarding

- [ ] Track locked + idea locked (§7)
- [ ] `team-roster.md` updated (solo entry OK)
- [ ] `onboarding-blocker.md` checklist opened — register at https://sectors.app
- [ ] Each team member completes onboarding → claims 1,000 credits
- [ ] Onboarding verified in portal → `experiment/<track-slug>/` branch created
- [ ] `.env.example` committed to the new branch with Sectors API key placeholder
- [ ] First curl test confirms "remove Sectors → no signal" empirically
- [ ] `submission-checklist.md` updated with chosen track + Week 1 plan

See [`merge-plan.md`](../merge-plan.md) for the merge order of reference branches once onboarding is complete.
