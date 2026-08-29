# Sectors MCP — Setup Guide

> Source: https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide
> Verified: 29 Aug 2026

The Sectors MCP server is **cloud-hosted on Cloudflare Workers** and gives any MCP-compatible client access to **65+ tools** covering IDX (Indonesia), SGX (Singapore), KLSE (Malaysia), and Indonesian mining data — no local install.

| | Value |
|---|---|
| Endpoint | `https://sectors-mcp.supertype.ai/mcp` |
| Transport | Streamable HTTP |
| Auth header | `Authorization: Bearer <YOUR_API_KEY>` |
| Source repo for the skill variant | https://github.com/supertypeai/sectors-agent-skills |

> **Using Claude (web or Desktop)?** Skip the API-key config below — Claude supports a one-click OAuth custom connector. See [claude-integration.md](./claude-integration.md).
> **Using ChatGPT?** See [chatgpt-integration.md](./chatgpt-integration.md).

---

## Prerequisites

1. **A Sectors Financial API key** — requires an Insider plan OR a hackathon onboarding grant (1,000 credits, see [`references/sectors-api-and-mcp.md`](../sectors-api-and-mcp.md)).
   Get your key at https://sectors.app/api.
2. **An MCP-compatible client.** Any of:
   - [Claude Code](https://claude.ai/download) (CLI)
   - [Claude Desktop](https://claude.ai/download) (or use OAuth — see below)
   - [Cursor](https://cursor.com)
   - [VS Code](https://code.visualstudio.com) with GitHub Copilot
   - [Windsurf](https://windsurf.com), JetBrains IDEs, or any client supporting Streamable HTTP transport

---

## Quick Start Setup

### Claude Code

Run this once in your terminal:

```bash
claude mcp add -t http sectors https://sectors-mcp.supertype.ai/mcp \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

The server becomes available in your next Claude Code session. Confirm with:

```bash
claude mcp list
```

### Cursor

Open or create `~/.cursor/mcp.json` and add:

```json
{
  "mcpServers": {
    "sectors": {
      "url": "https://sectors-mcp.supertype.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Replace `YOUR_API_KEY_HERE` with your Sectors Financial API key, **restart Cursor completely**, and Sectors tools will appear in Agent mode.

### VS Code (Copilot)

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "sectors": {
      "type": "http",
      "url": "https://sectors-mcp.supertype.ai/mcp",
      "headers": {
        "Authorization": "Bearer ${input:sectors-api-key}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "sectors-api-key",
      "description": "Your Sectors Financial API key",
      "password": true
    }
  ]
}
```

VS Code will securely prompt for your key the first time the server starts. This config is **workspace-scoped**, so repeat per-project.

### Windsurf / JetBrains / any Streamable HTTP client

| Setting              | Value                                  |
| -------------------- | -------------------------------------- |
| Transport            | `http`                                 |
| URL                  | `https://sectors-mcp.supertype.ai/mcp` |
| Authorization header | `Bearer YOUR_API_KEY_HERE`             |

---

## OAuth variants (no API-key config)

- **Claude** — see [claude-integration.md](./claude-integration.md). One-click OAuth custom connector, no `Bearer` token in your config.
- **ChatGPT** — see [chatgpt-integration.md](./chatgpt-integration.md). Developer-mode custom MCP app, OAuth with Dynamic Client Registration.

Both still require an Insider-plan Sectors account to authorize.

---

## Ticker conventions (the #1 setup mistake)

| Market | Format | Examples | Notes |
|--------|--------|----------|-------|
| IDX    | 4 letters, **omit `.JK`** | `BBCA`, `BMRI`, `TLKM` | MCP tools don't accept `.JK` — strip it. REST tolerates it. |
| SGX    | 3 chars (letters or digits) | `D05`, `U11`, `Z74` | Optional `.si` ignored. |
| KLSE   | 4-digit numeric | `1155`, `4197`, `5225` | Bare digits only. |
| Subsector | kebab-case slug | `banks`, `software-it-services` | **Never guess.** Fetch the canonical list with `get-subsectors`. |
| Mining | company slug | `pt-bukit-asam`, `pt-adairom-energy-indonesia-tbk` | Fetch via `fetch-mining-companies` to confirm. |

Mixing `.JK` on MCP calls will return silent empty arrays. Pick one convention per project and stick to it.

---

## Data freshness (verbatim from the guide)

> "Market prices and daily transaction data are updated at end-of-day. Quarterly financials are updated as companies file their reports. Dividend data is updated when announcements are made."

Practical implication for hackathon projects:
- An 08:00 WIB cron will see **yesterday's EOD data**, not intraday.
- For Automation track: schedule the run after 09:00 WIB and label your product "previous-day close + flow analysis" — don't promise real-time.
- For Market Intelligence track: cache aggressively and display the freshness timestamp prominently (judges notice).

---

## Troubleshooting

### Connection & Setup

**"The server doesn't appear in my MCP client after setup."**
Restart your client completely — most clients only load MCP servers on startup. For Claude Code, `claude mcp list` confirms registration.

**"VS Code keeps prompting for the API key on every session."**
Expected. The `${input:sectors-api-key}` placeholder prompts once per session and stores the key in memory only.

### Authentication

**`401 Unauthorized`**

1. Verify your key is correct and tied to an active Insider plan (or hackathon onboarding grant).
2. Format: `Bearer YOUR_API_KEY_HERE` — the `Bearer ` prefix is required.
3. No extra spaces or line breaks in the key value.

**"My API key works on the Sectors website but not in the MCP server."**
The MCP server uses the same key as the Sectors Financial API. Re-copy from https://sectors.app/api — don't reuse a cached or expired token.

### Data & Coverage

**"A tool returned an empty array or no results."**

- **Wrong subsector slug** — subsectors are kebab-case. Call `get-subsectors` to get the canonical list. Don't guess.
- **Ticker not found** — double-check the symbol; remember no `.JK` on MCP tools.
- **Date range too narrow** — for daily transaction tools, ensure the range includes trading days (no weekends / IDX holidays).

**"Which markets does the Sectors MCP server cover?"**

| Market | Code | Coverage |
|--------|------|----------|
| Indonesia | IDX | **Primary** — 40+ tools (company reports, rankings, financials, brokers, filings, news, mining) |
| Singapore | SGX | Full company reports, rankings, dividends, buybacks, short-sell |
| Malaysia | KLSE | Basic company report and sector data |
| Indonesia Mining | Mining | Full — commodities, companies, sites, production, exports, licenses, auctions |

---

## FAQ

**Q: Do I need a separate key for MCP and REST?**
A: No. Same Sectors API key. MCP uses `Authorization: Bearer <key>`; REST uses `Authorization: <key>` (raw, no `Bearer`). See [`references/sectors-api-and-mcp.md`](../sectors-api-and-mcp.md) for the auth matrix.

**Q: How much credit does each MCP call cost?**
A: No published per-call cost. Hackathon teams get 1,000 credits for the build period. Insider plan gives 5,000/mo — a typical project lifecycle consumes ~20% of a month's allowance. **Cache aggressively and prefer universe feeds (`fetch-close(date)`) over per-symbol loops.** See `references/sectors-api-and-mcp.md` → "Cost / credit budget".

**Q: Can I use Sectors MCP in a hackathon submission?**
A: Yes. Rules §06: any track may use MCP, REST, or both. The product must break if Sectors data is removed.

**Q: Is there a rate limit?**
A: No documented rate-limit headers in the public docs. Be polite, cache, and don't loop.

---

## Next steps

- Tool-by-tool reference: [tools.md](./tools.md)
- OAuth setup (no config file): [claude-integration.md](./claude-integration.md) · [chatgpt-integration.md](./chatgpt-integration.md)
- Build recipes: [`../recipes/01-generative-ai-bg.md`](../recipes/01-generative-ai-bg.md) → [`06-memory-agents.md`](../recipes/06-memory-agents.md)
- REST equivalents: [`../rest/`](../rest/) (Lane 1 — IDX + Mining only)
