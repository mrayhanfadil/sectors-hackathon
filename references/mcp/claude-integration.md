# Connect Sectors to Claude with OAuth

> Source: https://docs.sectors.app/recipes/sectors-for-ai-agents/02-sectors-in-claude
> Verified: 29 Aug 2026

Sectors is available as a **custom connector** inside Claude — connect once with OAuth and Claude can pull live IDX, SGX, and KLSE data into any conversation. **No API key to paste into a config file**, no JSON to edit, and access is revocable from your Sectors dashboard at any time.

This guide covers the OAuth flow on **claude.ai (web)** and the **Claude Desktop** app. If you're setting up Claude Code, Cursor, VS Code, or any other Streamable HTTP client, see [setup.md](./setup.md) instead.

## Two ways to connect

| Setup style | Best for | Auth | Endpoint |
|-------------|----------|------|----------|
| **OAuth custom connector** (this guide) | claude.ai, Claude Desktop | Browser sign-in | `https://sectors-mcp.supertype.ai/mcp` |
| API key + Streamable HTTP ([setup.md](./setup.md)) | Claude Code, Cursor, VS Code, JetBrains | `Bearer YOUR_API_KEY` header | `https://sectors-mcp.supertype.ai/mcp` |

OAuth is the **path of least resistance** for hackathon teams that don't want every member to manage an API key in a config file. One sign-in per teammate, per workspace.

---

## Prerequisites

1. **A Sectors account on an Insider plan** — required to authorize the connector. Hackathon onboarding also unlocks a 1,000-credit grant, see [`../sectors-api-and-mcp.md`](../sectors-api-and-mcp.md).
2. **Claude on web or desktop** — sign in at https://claude.ai or install the [Claude Desktop app](https://claude.ai/download).

---

## Setup on claude.ai (Web)

The connector UI is the same on web and Desktop. Steps below target web; Desktop follows steps 3–6 after opening Customize.

### Step 1 — Open Customize
In the Claude sidebar, click **Customize**.

### Step 2 — Open Connectors
In the Customize panel, click **Connectors**.

### Step 3 — Add a custom connector
Click the **+** button at the top of the Connectors list and choose **Add custom connector**.

### Step 4 — Enter the Sectors connector details
In the dialog, set:

- **Name:** `Sectors`
- **URL:** `https://sectors-mcp.supertype.ai/mcp`

Leave the advanced settings at their defaults and click **Add**.

### Step 5 — Authorize access
Claude opens the Sectors authorization page in a new window. Review the requested permission (**Read access to Sectors API**) and click **Allow Access**.

Sign in to your Sectors account if you aren't already. Your existing subscription limits and credits apply to all requests made through the connector.

### Step 6 — Confirm the connection
Back in Connectors, **Sectors Mcp** now appears under **Web** with all 65+ tools listed. From here you can toggle tool permissions individually (**Always allow / Ask / Never**) using the icons on the right of each tool row.

---

## Setup on Claude Desktop

Claude Desktop uses the same Connectors UI as the web app.

1. Open the Desktop app.
2. Click your profile → **Customize** → **Connectors**.
3. Follow steps 3–6 from the web setup above.

> The connector you add is synced to your Claude account, so a connector added on the web also appears in Desktop and vice versa.

Make sure you're on a recent version of Claude Desktop. If **Connectors** doesn't appear under **Customize**, update from https://claude.ai/download and restart.

---

## Verify it works

Open a new chat and try:

> Give me an overview of Bank Central Asia (BBCA) using the Sectors connector.

Claude will request permission to call `fetch-company-report` (unless you've already set it to **Always allow**), then return the company's sector, market cap, last close price, and index memberships.

If the tool call succeeds, you're done. For more example prompts see the [main Sectors MCP guide](https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide#usage-examples).

---

## Managing access

- **Tool permissions** — In **Customize → Connectors → Sectors Mcp**, expand the tools list and set each tool to **Always allow**, **Ask**, or **Never**. Per-tool, per-user.
- **Disconnect** — Click **Disconnect** at the top of the connector panel to remove it from Claude.
- **Revoke from Sectors** — Revoke the OAuth grant from your Sectors dashboard. After revoking, Claude tool calls start failing with a 401 until you reconnect.

---

## Troubleshooting

**The connector doesn't show up after I add it.**
Refresh the Connectors page, or close and reopen Claude. Sync between web and Desktop isn't always instant — give it a few seconds.

**Authorization loops back to the login screen.**
Usually means you're signed into the wrong Sectors account, or your session has expired. Open https://sectors.app in the same browser, confirm you're signed in, then retry.

**Tools return `401 Unauthorized` after authorizing.**
The OAuth grant was revoked from your Sectors dashboard, or your Insider subscription has lapsed. Reconnect the connector.

**A tool returns an empty array.**
Same causes as the API-key flow: wrong subsector slug, ticker not found, date range with no trading days. See [setup.md → Data & Coverage](./setup.md#data--coverage).

---

## Hackathon-specific notes

- **Team onboarding:** every team member who wants to use Sectors in their own Claude account needs to do this OAuth flow themselves. There is no shared team connector.
- **Tool toggling:** set frequently-used tools (`fetch-company-report`, `fetch-companies-by-subsector`, `fetch-quarterly-financials`) to **Always allow** during build sessions to avoid permission prompts on every call. Set unfamiliar tools to **Ask** while testing.
- **Cost control:** each tool call hits your Sectors credit balance. Always pass `sections=` to `fetch-company-report` and `fetch-subsector-report`. Prefer universe feeds (`fetch-close(date)`, `fetch-companies-quarterly-financial-dates`) over per-symbol loops. See [`../sectors-api-and-mcp.md` → Cost / credit budget](../sectors-api-and-mcp.md#cost--credit-budget).
- **Build-period freeze (rules §05):** the connector is a runtime thing — it doesn't affect your repo. OAuth tokens auto-refresh; nothing to commit.

---

## Next steps

- [setup.md](./setup.md) — API-key path for Claude Code / Cursor / VS Code / JetBrains
- [tools.md](./tools.md) — full 65+ tool reference
- [`../sectors-api-and-mcp.md`](../sectors-api-and-mcp.md) — REST vs MCP cheat sheet
