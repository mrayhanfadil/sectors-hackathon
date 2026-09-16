# Branch inventory - 2026-08-30 cleanup

## Status after cleanup: 8 branches (was 17)

### KEEP - 8 canonical branches

| Branch | Last SHA | Purpose |
|---|---|---|
| `main` | `4aad52e` | Canonical baseline (planning + audit fixes merged) |
| `experiment/ai-agents-assistants` | `7384393` | T01 placeholder; project code lives here once locked |
| `experiment/automation-workflows` | `96ba0f2` | T02 placeholder |
| `experiment/market-intelligence` | `837c2e5` | T03 placeholder |
| `references/rest-idx-mining-2026-08-29` | `cf9d36c` | REST catalog (IDX + Mining only) |
| `references/mcp-idx-mining-2026-08-29` | `bf645ed` | MCP + agent recipes (6 chapters + human-agent) |
| `references/cookbook-idx-mining-2026-08-29` | `8d8ecf7` | Quickstart + 14 cookbook recipes |
| `idea/agy-retail-institutional-2026-08-30` | `ffaa816` | 9 empowerment-angled ideas |
| `idea/agy-niche-2026-08-30` | `cb44658` | 9 niche ideas + friend's "Smart Newsletter" eval |

### ARCHIVED - 9 superseded or consumed branches

| Archived branch | Last SHA | Reason | Where the content lives now |
|---|---|---|---|
| `references/cookbook-2026-08-29` | `36149ec` | v1; superseded by `-idx-mining-` variant (15-file superset) | `references/cookbook-idx-mining-2026-08-29` |
| `references/mcp-and-recipes-2026-08-29` | `f30413e` | v1; missing `human-agent-framework.md` | `references/mcp-idx-mining-2026-08-29` |
| `references/rest-catalog-2026-08-29` | `bcb1221` | Local-only; contained SGX+KLSE which we skipped. Superseded by `-idx-mining` | `references/rest-idx-mining-2026-08-29` |
| `idea/agy-brainstorm-2026-08-30` | `9b92f9d` | Generic track-bucket ideas; absorbed into empowerment + niche batches | covered by `agy-retail-institutional` + `agy-niche` |
| `audit/f1-repo-2026-08-29` | `75a1aaf` | Audit content; fixes already merged to main (`4aad52e`) | `main` |
| `audit/f2-cookbook-2026-08-29` | `952e6bb` | Cookbook-v2 lives in `references/cookbook-idx-mining-` | `references/cookbook-idx-mining-2026-08-29` |
| `audit/f3-ideas-2026-08-29` | `2230ccb` | Asing Radar recommendation superseded by friend's "Macro-to-Micro" Variant 2 (4.50 vs 8.13) | `idea/agy-niche-2026-08-30/ideas/friend-ideas/smart-newsletter-3-variants.md` |
| `fix/f1-audit-2026-08-29` | `4aad52e` | Fixes already merged to main (`4aad52e`) | `main` |
| `fix/mcp-crosslinks-2026-08-29` | `f03f1b7` | Identical content to `references/mcp-idx-mining-2026-08-29` (verified - same blob SHAs for all mcp/recipes files; only `tools.md` differs by the fix commit which is also in mcp-idx-mining branch) | `references/mcp-idx-mining-2026-08-29` |

## Recovery procedure

If any archived branch content is needed later:
```bash
# List archived branches still in local refs (we keep local refs intact)
git for-each-ref --format='%(refname:short) %(objectname:short)' refs/heads/

# Recover specific archived branch
git checkout -b restore/references-cookbook-2026-08-29 <SHA>
git push -u origin restore/references-cookbook-2026-08-29
```

## Why we kept local refs (not just `git branch -D`)

Local refs are cheap (just SHA pointers, no blobs). Keeping them lets us quickly restore any archived branch if a teammate asks "what was in that v1 cookbook?" or "did we ever evaluate the SGX/KLSE ideas?". The blobs are still in the object graph until `git gc --prune=now` (which we don't run).

## Note for the merge plan

When ready to merge the reference branches into `main`, follow `merge-plan.md` (4 steps + cleanup step 3a):
1. Step 1: planning-only updates - DONE (already merged `fix/f1-audit-2026-08-29`)
2. Step 2: merge `references/rest-idx-mining-2026-08-29` (leaf)
3. Step 3: merge `references/mcp-idx-mining-2026-08-29`
4. Step 4: merge `references/cookbook-idx-mining-2026-08-29`
5. Step 5 (optional): cherry-pick audit/fix branches if needed for traceability
