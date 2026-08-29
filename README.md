# Sectors Hackathon 2026

Build repo for **Sectors Hackathon / Indonesia / 2026** — an online, Indonesia-wide competition for AI that works with Indonesian financial data using the **Sectors MCP or REST API**.

> **Repo created:** 29 August 2026 (inside build period, which runs 19 Aug – 30 Sep 2026).
> This repo currently holds **planning & research artifacts only** — README, rules, track briefs, submission checklist, ideas. No product code yet.

---

## TL;DR

| | |
|---|---|
| **Organizers** | Supertype × Sectors × Algoritma |
| **Eligibility** | Indonesian citizens / residents; all ages (U18 needs guardian consent) |
| **Team size** | Solo or 2–4 participants (one team per participant) |
| **API credits** | 1,000 Sectors API credits per team, claimed after all members finish onboarding |
| **Registration closes** | **22 Sep 2026, 23:59 WIB** |
| **Build period closes** | **30 Sep 2026, 23:59 WIB** (no commits after) |
| **Winners announced** | **9 Oct 2026** |
| **Prize pool** | **IDR 50,000,000** (IDR 30M cash + IDR 20M Sectors API credits) |
| **Tracks** | AI Agents & Assistants · Automation & Workflows · Market Intelligence |
| **Repo must remain** | Public for ≥90 days after winners announced |
| **Forbidden** | Automated trade execution; pre-event code; multi-account for extra credits; multi-hackathon submission |
| **Allowed** | Templates/boilerplate/AI coding tools (no disclosure needed); MCP + REST both OK on any track |

> Judges weight **real-world usability (40%) > video storytelling (30%) > technical depth (30%)**. A product a real person can use today wins more than a clever prototype.

---

## Repo structure

```
sectors-hackathon/
├── README.md                  ← this file (overview + key dates + nav)
├── rules.md                   ← official rules verbatim (with our annotation)
├── submission-checklist.md    ← what we need ready before 30 Sep 23:59 WIB
├── ideas.md                   ← brainstorming seeds per track (we pick one)
├── tracks/
│   ├── ai-agents-assistants.md
│   ├── automation-workflows.md
│   └── market-intelligence.md
└── .gitignore                 ← typical stack files
```

Project code will live under `experiment/<track-slug>/` once we commit code (see "Branching & commits" below).

---

## Branching & commits

Per-repo convention (private, ready-to-share):

- **`main`** — stable planning artifacts only (rules, track briefs, README, final submission). No project code.
- **`experiment/<track-slug>`** — per-track idea exploration + project code. Created when we lock a track.

> ⚠️ **Build-period freeze rule:** the team's repository freezes on submit or 30 Sep 23:59 WIB, whichever comes first. **No commits, pushes, edits, or changes of any kind after freeze** — even bug fixes — or the team is disqualified. The only exception is a leaked credential: notify organizers on Slack `#support`, rotate, then push a removal-only commit.

We must verify commit history is clean of any pre-19-Aug code if reviewers dig. All commits in this repo so far post-date 19 Aug 2026 (build period open), which is fine.

---

## Next actions (in priority order)

1. **Onboard at sectors.app** — every team member needs a Sectors account + completed onboarding before any project code is written. Onboarding is verified at eligibility check.
2. **Lock the team** — solo or 2–4 people. Each person claims the team on the [hackathon portal](https://hackathon.sectors.app/portal/team). Team rep = API credit holder + prize recipient.
3. **Pick a track** — read [tracks/](tracks/) + [ideas.md](ideas.md), decide what we'll build.
4. **Claim 1,000 API credits** — only after all members onboarded.
5. **Build MVP** — start with smallest core workflow that uses Sectors data so heavily that the product breaks without it (judges check this).
6. **Record videos** — 60s teaser (public, on social) + up-to-3min judging video (public/unlisted YouTube/Vimeo/Google Drive/Loom).
7. **Submit through the portal** by 30 Sep 2026 23:59 WIB — repo link, videos, one-sentence problem statement, track selection, team roster, social post tagging official account.

---

## Links

- Rules (EN): https://hackathon.sectors.app/rules
- Track 01 — AI Agents & Assistants: https://hackathon.sectors.app/tracks/ai-agents-assistants
- Track 02 — Automation & Workflows: https://hackathon.sectors.app/tracks/automation-workflows
- Track 03 — Market Intelligence: https://hackathon.sectors.app/tracks/market-intelligence
- Team portal: https://hackathon.sectors.app/portal/team
- Submission portal: https://hackathon.sectors.app/portal/submit
- Slack: https://join.slack.com/t/sectorshackathon/shared_invite/zt-47a8tdhhz-FgREdKQ46lUETWErcIwNcQ
- Direct email: ask+hackathon@incoming.supertype.ai

---

## Honcho notes (for future sessions)

We have only this repo so far. **No team registered yet**, **no track chosen yet**, **no product code written yet**. Before any product code lands we need: onboarding complete + track chosen + API credits claimed.
