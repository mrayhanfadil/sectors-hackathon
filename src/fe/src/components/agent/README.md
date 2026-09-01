# Agent Visualization Components

Components and hooks for visualizing the 11-agent ADK institutional report pipeline on `/agent`, designed for retail investors (orang awam) with plain Indonesian explanations, visual 5-stage progress, and collapsible raw technical details for developers.

## Architecture & Layout

The `/agent` interface is structured top-to-bottom for clarity:

1. **Hero & Controls**: Run trigger with Indonesian labels (`Jalankan Analisis`, `Mode Cepat`, `Bersihkan`), ticker selection, and backend health status.
2. **Cara Kerja Sistem (Explainer)**: Collapsible guide explaining the 11-agent collaborative process in everyday language.
3. **SummaryCard (`SummaryCard.tsx`)**: Executive summary card appearing on run completion with ticker rating, target price, key findings, elapsed time, and honest disclaimer.
4. **PhaseTimeline (`PhaseTimeline.tsx`)**: Horizontal 5-stage pipeline timeline replacing `AgentRail`:
   - Stage 1: Pengumpulan Data (`collector`, `news_harvester`, `social_sentiment`)
   - Stage 2: Valuasi (`modeler`)
   - Stage 3: Riset (`analyst`, `industry`, `risk`, `kpi`)
   - Stage 4: Penulisan (`writer`, `visualizer`, `sotp`)
   - Stage 5: Penjaminan Kualitas (`adversarial`, `critic`)
5. **PlainEnglishPanel (`PlainEnglishPanel.tsx`)**: Scrollable streaming feed translating raw agent function calls into 1-line plain Indonesian descriptions (e.g. "Sedang menghitung WACC untuk BBCA") with Lucide icons, durations, and an optional collapsible "Lihat detail teknis" toggle for raw JSON inspectability.
6. **Raw Debug Panel**: Collapsible drawer at the bottom of the page for engineers to inspect raw SSE event frames and pipeline state keys.

## Component Overview

### Retail / Awam Components
- **`AGENT_FRIENDLY_META.ts`**: Friendly Indonesian labels, Lucide icon definitions, stage mappings, and natural-language description formatters for all 16 agents and subagents.
- **`PhaseTimeline.tsx`**: 5-stage horizontal timeline with animated active pulses, stage completion badges, and interactive agent filtering.
- **`PlainEnglishPanel.tsx`**: Live event stream rendering friendly agent cards, human-readable actions, duration badges, and collapsible technical JSON details.
- **`SummaryCard.tsx`**: High-level synthesis card summarizing final ratings, target prices, and QA validation.

### Hooks & Shared State
- **`useAgentProgress.ts`**: Tracks agent statuses (`idle`, `running`, `finished`, `error`), rolling ETA, active agent counts, and stream interruptions.
- **`useStatePreview.ts`**: Aggregates state deltas and payload sizes across events.

### Developer / Legacy Components
- **`AgentRail.tsx`**: Original raw agent status rail.
- **`ProgressHeader.tsx`**: Original technical progress header with bridge health metrics.
- **`StatePreview.tsx`**: State keys preview card displaying raw JSON deltas.
- **`FunctionCallCard.tsx`**: Collapsible tool invocation payload card.
- **`FunctionResponseCard.tsx`**: Collapsible tool return payload card.
