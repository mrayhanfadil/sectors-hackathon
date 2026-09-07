# Swarm + Bounded Inter-Agent Comms + Memory Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 11-agent graph berjalan paralel di 2 grup riset, agent bisa minta data ke peer maksimal 3x, dan hasil run tersimpan terstruktur lintas-run — tanpa forever-loop dan tanpa vector DB prematur.

**Architecture:** Root tetap `SequentialAgent` (urutan = correctness). Paralel hanya di 2 grup yang sudah dirancang paralel. Komunikasi peer = deterministic tool `request_peer_data` + counter di state (max 3) + fallback proceed-with-gaps. Memori = SQLite terstruktur yang sudah ada, diperluas skemanya; vector DB ditolak sampai trigger terpenuhi (§Decision Log D3).

**Tech Stack:** ADK Python (`ParallelAgent`, `AgentTool`, `output_key`/state), SQLite (`data/agent_runs.db`), pytest, tanpa dep baru.

---

## Decision Log

### D1: Swarm = 2 grup paralel saja, root tetap sequential — APPROVED (scoped)
- **Why:** Dependensi antar-fase itu real: modeler butuh `collector_output`, writer butuh semua riset, critic harus terakhir. Root paralel = hasil non-deterministik + PDF bisa render dari state setengah jadi.
- **Rejected:** full-swarm semua 11 agent (race di `output_key`, urutan template hancur, debug 3x harder).
- **Risk:** Spark 1.3 concurrency belum pernah diuji (throttle sequential lahir dari era minimax-free 503). Mitigasi: Task 1 = probe konkuren 4-call sebelum flip default.

### D2: Komunikasi peer = tool deterministik + counter, max 3 — APPROVED (pattern)
- **Why:** Request tercatat di state (`peer_requests`), retry terhitung, ke-3 gagal = proceed-with-gaps + provenance jujur. Testable, bounded, kelihatan di /agent trace.
- **Rejected:** LLM-to-LLM free-form negotiation (tidak bounded, tidak bisa di-test, trace jadi bubur, bakar kredit 2 model per putaran).
- **Risk:** Agent malas — selalu request bukannya kerja. Mitigasi: request wajib sertakan `needed_fields` spesifik + alasan; critic flag request tanpa justifikasi.

### D3: Vector DB — REJECTED, SQLite `memory_facts` APPROVED (locked 2026-09-05)
- **Keputusan:** Pakai SQLite yang sudah ada (`data/agent_runs.db`) + tabel `memory_facts` baru. Nol dep baru.
- **Why:** State kita ~13 key kecil per run; pencarian semantik tidak menyelesaikan masalah apapun hari ini. Yang missing adalah memori lintas-run itu sendiri — cukup diselesaikan tabel terstruktur: query exact (ticker, tanggal, verdict) > query semantik untuk audit finansial.
- **Trigger untuk revisit (SEMUA harus benar):** (a) >500 run tersimpan, (b) ada query nyata yang gagal dijawab exact-match ("kapan terakhir kita SELL bank dengan alasan likuiditas?"), (c) benchmark membuktikan FTS/SQLite tidak cukup.
- **Rejected:** chromadb/pgvector sekarang (+1 dep, +1 service, embedding cost per run, zero query yang butuh itu).
- **Risk:** Nanti migrasi. Mitigasi: skema `memory_facts` pakai kolom `embedding BLOB NULL` — siap diisi tanpa migrasi skema.

---

## Phase 0 — Concurrency probe (go/no-go untuk swarm)

### Task 1: Probe 4 parallel Responses-API calls ke Spark 1.3
**Objective:** Buktikan opencode-go tahan konkuren sebelum flip default.
**Files:**
- Create: `agents/adk/tests/test_spark13_concurrency.py`
**Step 1: Write failing test**
```python
import asyncio, time
from agents.adk.providers.opencode_responses import spark13_model
from google.adk.models.llm_request import LlmRequest
from google.genai import types

async def _pong():
    m = spark13_model()
    req = LlmRequest(contents=[types.Content(role="user", parts=[types.Part.from_text(text="Reply with PONG")])])
    out = [x async for x in m.generate_content_async(req)]
    return out[0].content.parts[0].text or ""

def test_4x_parallel_pong_live():
    import os
    if os.getenv("OPENCODE_GO_LIVE") != "1":
        import pytest; pytest.skip("gated")
    t0 = time.time()
    texts = asyncio.run(_gather4())
    assert all("PONG" in t.upper() for t in texts), texts
    print(f"4 parallel took {time.time()-t0:.1f}s")
```
(dengan `async def _gather4(): return await asyncio.gather(*[_pong() for _ in range(4)])`)
**Step 2:** Run: `OPENCODE_GO_LIVE=1 .venv/bin/python -m pytest agents/adk/tests/test_spark13_concurrency.py -q -s`
Expected: PASS semua + wall time paralel < 2x waktu single (10.5s) = aman.
**Step 3 (go/no-go):** Jika ada 500/429/timeout → STOP, catat di plan, swarm tetap off. Jika hijau → lanjut Phase 1.
**Step 4: Commit** `test(adk): concurrency probe spark13 4x parallel`

### Task 2: Flip default ke paralel untuk Spark, sequential tetap untuk minimax
**Objective:** `ADK_PARALLEL` default 1 kecuali provider minimax.
**Files:**
- Modify: `agents/adk/app.py` (~line 243-250, blok `free_tier`)
**Step 1:** Test: extend `agents/adk/tests/test_adk_scaffold.py` — assert `build_graph` dengan `ADK_PROVIDER=opencode-go` menghasilkan `ParallelAgent` bernama `intake_parallel` (cek `type(...).__name__`).
**Step 2:** Run, expect FAIL.
**Step 3:** Implementasi: ubah kondisi `free_tier` jadi true hanya jika provider minimax-ish (bukan sekadar commandcode key di disk):
```python
is_minimax = os.getenv("ADK_PROVIDER", "").lower() in ("minimax", "minimax-m3-free", "minimax/minimax-m3-free")
free_tier = bool(is_minimax and (_adk_parallel_val == "" or _adk_parallel_val == "0"))
```
**Step 4:** Run full `agents/adk/tests/`, expect 53+ PASS.
**Step 5: Commit** `feat(adk): parallel intake/research default on non-minimax`

---

## Phase 1 — Bounded peer comms (max 3x)

### Task 3: Tool `request_peer_data` + state counter
**Objective:** Agent bisa minta field spesifik dari output agent lain, tercatat, max 3x per run.
**Files:**
- Create: `agents/adk/tools/peer_tools.py`
- Test: `agents/adk/tests/test_peer_tools.py`
**Step 1: Write failing test**
```python
from agents.adk.tools.peer_tools import peer_request_allowed, record_peer_request
state = {}
assert peer_request_allowed(state) is True
for _ in range(3):
    state = record_peer_request(state, frm="analyst", to="collector", fields=["segments"])
assert peer_request_allowed(state) is False  # ke-4 diblok
assert state["peer_requests"][0]["fields"] == ["segments"]
```
**Step 2:** Run, expect FAIL (module belum ada).
**Step 3:** Implementasi minimal:
```python
PEER_REQUEST_LIMIT = 3
def peer_request_allowed(state) -> bool:
    return len(state.get("peer_requests", [])) < PEER_REQUEST_LIMIT
def record_peer_request(state, frm, to, fields, reason=""):
    if not fields:
        raise ValueError("request wajib sebut needed_fields spesifik")
    entry = {"from": frm, "to": to, "fields": fields, "reason": reason}
    return {**state, "peer_requests": [*state.get("peer_requests", []), entry]}
```
**Step 4:** Run, expect PASS. **Step 5: Commit** `feat(adk): bounded peer request ledger max 3`

### Task 4: Daftarkan sebagai function tool + instruksi goto
**Objective:** 4 research agent (analyst/industry/risk/kpi) dapat tool-nya + tahu kapan pakai.
**Files:**
- Modify: `agents/adk/app.py` (`_function_tools()` + 4 instruction strings), `agents/adk/agents/instructions.py` jika instruksi di sana
- Test: extend `test_peer_tools.py` — assert tool name `request_peer_data` ada di toolset research agent
**Aturan instruksi (copy-paste ke prompt):** "Kalau field dari agent lain kosong: (1) cek state dulu, (2) panggil request_peer_data SEKALI per field-set dengan alasan, (3) kalau peer_requests sudah 3 → lanjut dengan data seadanya + tulis provenance gap. DILARANG request tanpa needed_fields."
**Step: Commit** `feat(adk): wire request_peer_data into research agents`

### Task 5: Critic flag request malas
**Objective:** Critic menolak laporan yang request >0 tanpa justifikasi di tiap entry.
**Files:** Modify critic instruction + 1 test.
**Step: Commit** `feat(adk): critic audits peer-request justification`

---

## Phase 2 — Memori lintas-run (SQLite, bukan vector)

### Task 6: Tabel `memory_facts` + tulis verdict tiap run
**Objective:** Run kemarin bisa di-query: ticker, tanggal, rating, FV, alasan.
**Files:**
- Modify: `server/routers/agent.py` (after run completes) atau modul storage yang ada (`data/agent_runs.db`)
- Test: `tests/test_memory_facts.py`
Skema:
```sql
CREATE TABLE IF NOT EXISTS memory_facts(
  id INTEGER PRIMARY KEY, run_id TEXT, ticker TEXT, finished_at REAL,
  rating TEXT, fair_value REAL, reasons_json TEXT, embedding BLOB NULL
);
CREATE INDEX IF NOT EXISTS idx_facts_ticker ON memory_facts(ticker);
```
**Step: Commit** `feat(memory): persist run verdicts to memory_facts`

### Task 7: Endpoint baca `GET /api/memory?ticker=&limit=`
**Objective:** FE/agent bisa lihat verdict historis sebelum run baru.
**Files:** Modify `server/routers/endpoints.py` + register router (ikut pola `router_universe`).
**Step: Commit** `feat(memory): GET /api/memory`

---

## Verifikasi akhir
- `agents/adk/tests/` hijau + `tests/test_memory_facts.py` hijau
- 1 run BBCA end-to-end di BE: trace menunjukkan `intake_parallel` event overlap (paralel beneran), `peer_requests` ≤ 3, verdict masuk `memory_facts`
- `GET /api/memory?ticker=BBCA` balas run tadi
- Baru: commit → push → deploy FE (tidak ada perubahan FE fase ini) → restart BE

## Risiko terbuka
- Spark 1.3 rate-limit konkuren tak terlihat di probe 4-call tapi muncul di 11-agent full run → fallback: `ADK_PARALLEL=0` (satu env, tanpa deploy kode).
- Peer request menambah 1-3 LLM call per run → cost naik ~10-20%; pantau via trace.
