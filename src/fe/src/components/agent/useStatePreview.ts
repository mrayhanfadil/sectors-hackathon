import { useMemo } from "react"

export interface TraceEvent {
  seq: number
  ts: number
  author: string
  node: string
  branch?: string | null
  event_type: string
  text: string
  function_calls: { name: string; args: Record<string, unknown>; id: string }[]
  function_responses: { name: string; response: unknown; id: string }[]
  state_delta_keys: string[]
  state_delta?: Record<string, unknown> | null
  transfer_to?: string | null
}

export interface StateItem {
  key: string
  value: unknown | undefined
  hasValue: boolean
  lastUpdatedSeq: number
  lastUpdatedTs: number
  author: string
  previewSnippet: string
  fullFormatted: string
  byteSize: number
  typeTag: string
  isTruncated: boolean
}

export interface StatePreviewData {
  items: StateItem[]
  totalBytes: number
  totalKb: string
  totalKeys: number
  summaryText: string
}

function processStateValue(
  key: string,
  raw: { value: unknown; hasValue: boolean; lastUpdatedSeq: number; lastUpdatedTs: number; author: string }
): StateItem {
  if (!raw.hasValue || raw.value === undefined) {
    return {
      key,
      value: undefined,
      hasValue: false,
      lastUpdatedSeq: raw.lastUpdatedSeq,
      lastUpdatedTs: raw.lastUpdatedTs,
      author: raw.author,
      previewSnippet: "—",
      fullFormatted: "— (not in event)",
      byteSize: 0,
      typeTag: "not in event",
      isTruncated: false,
    }
  }

  const v = raw.value

  if (typeof v === "string") {
    const encoder = new TextEncoder()
    const byteSize = encoder.encode(v).length
    const kbStr = (byteSize / 1024).toFixed(1)
    const typeTag = byteSize >= 1024 ? `[string:${kbStr}kb]` : `[string:${byteSize}B]`
    const preview = v.length > 200 ? `${v.slice(0, 200)}…` : v
    const isTruncated = v.length > 4000
    const full = isTruncated ? `${v.slice(0, 4000)}…` : v

    return {
      key,
      value: v,
      hasValue: true,
      lastUpdatedSeq: raw.lastUpdatedSeq,
      lastUpdatedTs: raw.lastUpdatedTs,
      author: raw.author,
      previewSnippet: preview,
      fullFormatted: full,
      byteSize,
      typeTag,
      isTruncated,
    }
  }

  if (typeof v === "object" && v !== null) {
    let jsonFormatted = ""
    let jsonCompact = ""
    try {
      jsonFormatted = JSON.stringify(v, null, 2)
      jsonCompact = JSON.stringify(v)
    } catch {
      jsonFormatted = "[Unserializable object]"
      jsonCompact = "[Unserializable object]"
    }

    const encoder = new TextEncoder()
    const byteSize = encoder.encode(jsonCompact).length
    const kbStr = (byteSize / 1024).toFixed(1)
    const kind = Array.isArray(v) ? "array" : "object"
    const typeTag = `[${kind}:${kbStr}kb]`
    const previewRaw = jsonCompact.length > 200 ? `${jsonCompact.slice(0, 200)}…` : jsonCompact
    const previewSnippet = `${typeTag} ${previewRaw}`
    const isTruncated = jsonFormatted.length > 4000
    const fullFormatted = isTruncated ? `${jsonFormatted.slice(0, 4000)}…` : jsonFormatted

    return {
      key,
      value: v,
      hasValue: true,
      lastUpdatedSeq: raw.lastUpdatedSeq,
      lastUpdatedTs: raw.lastUpdatedTs,
      author: raw.author,
      previewSnippet,
      fullFormatted,
      byteSize,
      typeTag,
      isTruncated,
    }
  }

  const str = String(v)
  const byteSize = str.length
  return {
    key,
    value: v,
    hasValue: true,
    lastUpdatedSeq: raw.lastUpdatedSeq,
    lastUpdatedTs: raw.lastUpdatedTs,
    author: raw.author,
    previewSnippet: str,
    fullFormatted: str,
    byteSize,
    typeTag: typeof v,
    isTruncated: false,
  }
}

export function useStatePreview(events: TraceEvent[]): StatePreviewData {
  return useMemo(() => {
    const map = new Map<
      string,
      { value: unknown; hasValue: boolean; lastUpdatedSeq: number; lastUpdatedTs: number; author: string }
    >()

    for (const ev of events) {
      if (ev.state_delta && typeof ev.state_delta === "object") {
        for (const [k, v] of Object.entries(ev.state_delta)) {
          map.set(k, {
            value: v,
            hasValue: v !== undefined && v !== null,
            lastUpdatedSeq: ev.seq,
            lastUpdatedTs: ev.ts,
            author: ev.author,
          })
        }
      }

      if (Array.isArray(ev.state_delta_keys)) {
        for (const k of ev.state_delta_keys) {
          if (!map.has(k)) {
            map.set(k, {
              value: undefined,
              hasValue: false,
              lastUpdatedSeq: ev.seq,
              lastUpdatedTs: ev.ts,
              author: ev.author,
            })
          } else {
            const existing = map.get(k)!
            if (ev.seq > existing.lastUpdatedSeq) {
              map.set(k, {
                ...existing,
                lastUpdatedSeq: ev.seq,
                lastUpdatedTs: ev.ts,
                author: ev.author,
              })
            }
          }
        }
      }
    }

    const items: StateItem[] = []
    let totalBytes = 0

    for (const [key, raw] of map.entries()) {
      const item = processStateValue(key, raw)
      items.push(item)
      totalBytes += item.byteSize
    }

    items.sort((a, b) => {
      if (b.lastUpdatedSeq !== a.lastUpdatedSeq) {
        return b.lastUpdatedSeq - a.lastUpdatedSeq
      }
      return b.lastUpdatedTs - a.lastUpdatedTs
    })

    const totalKb = (totalBytes / 1024).toFixed(1)
    const summaryText = `${items.length} keys · ${totalKb} kb total`

    return {
      items,
      totalBytes,
      totalKb,
      totalKeys: items.length,
      summaryText,
    }
  }, [events])
}
