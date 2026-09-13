import { useState, useMemo } from "react"
import {
  Newspaper,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  Clock,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { NewsArticleItem, Sentiment } from "@/lib/api"

export type SentimentNewsListProps = {
  ticker: string
  articles?: NewsArticleItem[]
  socialItems?: Sentiment["items"]
  isLoading?: boolean
}

type SentimentFilter = "all" | "bullish" | "bearish" | "neutral"

function formatTimestamp(ts?: string): string {
  if (!ts) return "BARU SAJA"
  try {
    const d = new Date(ts)
    if (Number.isNaN(d.getTime())) return ts
    return d.toLocaleDateString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).toUpperCase()
  } catch {
    return ts
  }
}

function getHostName(urlStr?: string): string {
  if (!urlStr) return "KANAL PUBLIK"
  try {
    const u = new URL(urlStr)
    return u.hostname.replace(/^www\./, "").toUpperCase()
  } catch {
    return urlStr.length > 25 ? `${urlStr.slice(0, 25).toUpperCase()}...` : urlStr.toUpperCase()
  }
}

export function SentimentNewsList({
  ticker,
  articles = [],
  socialItems = [],
  isLoading,
}: SentimentNewsListProps) {
  const tk = ticker.toUpperCase()
  const [filter, setFilter] = useState<SentimentFilter>("all")
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({})

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  // Combine news articles and social items into unified presentation list
  const combinedEntries = useMemo(() => {
    const list: Array<{
      id: string
      type: "news" | "social"
      title: string
      body: string
      source: string
      platform: string
      sentiment: "bullish" | "bearish" | "neutral" | "unscored"
      timestamp: string
      url?: string
      author?: string
      tags?: string[]
      relevance?: number
    }> = []

    // Map news articles
    articles.forEach((a, idx) => {
      const sentRaw = a.dimension?.sentiment?.toLowerCase() || ""
      const sent: "bullish" | "bearish" | "neutral" | "unscored" =
        sentRaw === "bullish" || sentRaw === "positif"
          ? "bullish"
          : sentRaw === "bearish" || sentRaw === "negatif"
          ? "bearish"
          : sentRaw === "neutral" || sentRaw === "netral"
          ? "neutral"
          : "unscored"

      list.push({
        id: `news-${idx}`,
        type: "news",
        title: a.title,
        body: a.body,
        source: a.source,
        platform: getHostName(a.source),
        sentiment: sent,
        timestamp: a.timestamp,
        url: a.source?.startsWith("http") ? a.source : undefined,
        tags: a.tags,
        relevance: a.dimension?.relevance,
      })
    })

    // Map social items
    socialItems.forEach((s, idx) => {
      const score = typeof s.score === "number" ? s.score : null
      const sent: "bullish" | "bearish" | "neutral" | "unscored" =
        score === null ? "unscored" : score >= 60 ? "bullish" : score <= 40 ? "bearish" : "neutral"

      list.push({
        id: `social-${idx}`,
        type: "social",
        title: s.text?.slice(0, 80) ? `${s.text.slice(0, 80)}...` : `Postingan ${s.platform || "Ritel"}`,
        body: s.text || "",
        source: s.platform || "Forum Komunitas",
        platform: (s.platform || "STOCKBIT / X").toUpperCase(),
        sentiment: sent,
        timestamp: s.timestamp || "",
        url: s.url,
        author: s.author,
      })
    })

    return list
  }, [articles, socialItems])

  const sentimentCounts = useMemo(() => {
    const counts = { all: combinedEntries.length, bullish: 0, bearish: 0, neutral: 0, unscored: 0 }
    combinedEntries.forEach((e) => {
      if (e.sentiment === "bullish") counts.bullish++
      else if (e.sentiment === "bearish") counts.bearish++
      else counts.neutral++
    })
    return counts
  }, [combinedEntries])

  const filteredEntries = useMemo(() => {
    if (filter === "all") return combinedEntries
    return combinedEntries.filter((e) => e.sentiment === filter)
  }, [combinedEntries, filter])

  return (
    <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2.5 dark:border-[#262930] dark:bg-[#181a1f]/70">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Newspaper className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              DISPATCH :: VERIFIED NEWS & DISCUSSION LOG // {tk} &lt;EQUITY&gt;
            </CardTitle>
          </div>

          {/* Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={`rounded-none px-2 py-0.5 font-semibold transition-colors cursor-pointer ${
                filter === "all"
                  ? "bg-neutral-900 text-white dark:bg-amber-400 dark:text-black"
                  : "border border-neutral-300 bg-white text-neutral-600 hover:bg-neutral-100 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400 dark:hover:bg-[#181a1f]"
              }`}
            >
              ALL ({sentimentCounts.all})
            </button>

            <button
              type="button"
              onClick={() => setFilter("bullish")}
              className={`inline-flex items-center gap-1 rounded-none px-2 py-0.5 font-semibold transition-colors cursor-pointer ${
                filter === "bullish"
                  ? "border border-emerald-600 bg-emerald-600 text-white dark:border-emerald-500 dark:bg-emerald-500 dark:text-black"
                  : "border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300 dark:hover:bg-emerald-950/60"
              }`}
            >
              <TrendingUp className="h-2.5 w-2.5" />
              BULL ({sentimentCounts.bullish})
            </button>

            <button
              type="button"
              onClick={() => setFilter("bearish")}
              className={`inline-flex items-center gap-1 rounded-none px-2 py-0.5 font-semibold transition-colors cursor-pointer ${
                filter === "bearish"
                  ? "border border-rose-600 bg-rose-600 text-white dark:border-rose-500 dark:bg-rose-500 dark:text-black"
                  : "border border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-950/60"
              }`}
            >
              <TrendingDown className="h-2.5 w-2.5" />
              BEAR ({sentimentCounts.bearish})
            </button>

            <button
              type="button"
              onClick={() => setFilter("neutral")}
              className={`inline-flex items-center gap-1 rounded-none px-2 py-0.5 font-semibold transition-colors cursor-pointer ${
                filter === "neutral"
                  ? "bg-neutral-800 text-white dark:bg-neutral-200 dark:text-black"
                  : "border border-neutral-300 bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-400 dark:hover:bg-neutral-800"
              }`}
            >
              <MinusCircle className="h-2.5 w-2.5" />
              NEUT ({sentimentCounts.neutral})
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-3 sm:p-4">
        {isLoading ? (
          <div className="flex h-36 items-center justify-center font-mono text-xs text-neutral-400">
            <span>MEMUAT ARUS BERITA & DISKUSI {tk}...</span>
          </div>
        ) : combinedEntries.length === 0 ? (
          <div className="border border-dashed border-neutral-300 bg-neutral-50/50 p-6 text-center font-mono text-xs dark:border-[#262930] dark:bg-[#15171c]">
            <p className="font-semibold text-neutral-700 dark:text-neutral-300">
              [NO DISPATCH ENTRIES FOR {tk}]
            </p>
            <p className="mt-1 text-[11px] text-neutral-500 dark:text-neutral-400">
              Data sentimen ritel (Stockbit, X, media berita) dikumpulkan secara dinamis saat News Harvester dan Social Sentiment agents dijalankan.
            </p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="border border-neutral-300 bg-neutral-50/50 p-4 text-center font-mono text-xs text-neutral-500 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-400">
            Tidak ada entri yang cocok dengan filter ({filter.toUpperCase()}).
          </div>
        ) : (
          <div className="space-y-2">
            {filteredEntries.map((item) => {
              const isExpanded = !!expandedIds[item.id]
              const hasBody = Boolean(item.body && item.body.trim().length > 0)

              return (
                <div
                  key={item.id}
                  className="border border-neutral-300 bg-neutral-50/40 p-3 transition-colors hover:border-neutral-400 dark:border-[#262930] dark:bg-[#15171c] dark:hover:border-neutral-600"
                >
                  <div className="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1 flex-1 pr-2">
                      {/* Top badge row */}
                      <div className="flex flex-wrap items-center gap-1 font-mono text-[10px]">
                        {item.sentiment === "bullish" && (
                          <span className="border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.2 font-semibold text-emerald-700 dark:text-emerald-400">
                            [+ BULLISH]
                          </span>
                        )}
                        {item.sentiment === "bearish" && (
                          <span className="border border-rose-500/40 bg-rose-500/10 px-1.5 py-0.2 font-semibold text-rose-700 dark:text-rose-400">
                            [- BEARISH]
                          </span>
                        )}
                        {item.sentiment === "neutral" && (
                          <span className="border border-neutral-300 bg-neutral-100 px-1.5 py-0.2 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                            [~ NEUTRAL]
                          </span>
                        )}
                        {item.sentiment === "unscored" && (
                          <span className="border border-dashed border-neutral-300 bg-transparent px-1.5 py-0.2 text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
                            [? TANPA SKOR]
                          </span>
                        )}

                        <span className="border border-neutral-300 bg-white px-1.5 py-0.2 text-neutral-600 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400">
                          {item.type === "news" ? "IDX PRESS" : "COMMUNITY"}
                        </span>

                        {item.relevance != null && (
                          <span className="text-neutral-500 tabular-nums dark:text-neutral-400">
                            REL: {(item.relevance * 100).toFixed(0)}%
                          </span>
                        )}

                        {item.author && (
                          <span className="text-neutral-500 dark:text-neutral-400">
                            @{item.author}
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <h4 className="text-xs font-semibold leading-snug text-neutral-900 dark:text-neutral-100">
                        {item.title}
                      </h4>
                    </div>

                    {/* Source & Date info */}
                    <div className="flex shrink-0 items-center gap-2 font-mono text-[10px] text-neutral-500 sm:flex-col sm:items-end sm:gap-1 dark:text-neutral-400">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-neutral-400" />
                        <span>{formatTimestamp(item.timestamp)}</span>
                      </div>

                      {item.url ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-cyan-700 hover:underline dark:text-cyan-400"
                        >
                          <span>[{item.platform}]</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      ) : (
                        <span>[{item.platform}]</span>
                      )}
                    </div>
                  </div>

                  {/* Body text & Expand */}
                  {hasBody && (
                    <div className="mt-2 pt-2 border-t border-neutral-200 dark:border-[#262930]">
                      <p
                        className={`text-xs leading-relaxed text-neutral-700 ${
                          isExpanded ? "whitespace-pre-line" : "line-clamp-2"
                        } dark:text-neutral-300`}
                      >
                        {item.body}
                      </p>

                      {item.body.length > 140 && (
                        <button
                          type="button"
                          onClick={() => toggleExpand(item.id)}
                          className="mt-1.5 inline-flex items-center gap-1 font-mono text-[10px] font-semibold text-cyan-700 hover:underline cursor-pointer dark:text-cyan-400"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3 w-3" />
                              [- COLLAPSE TEXT]
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3" />
                              [+ EXPAND FULL TEXT]
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Tags */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap items-center gap-1 font-mono text-[10px]">
                      {item.tags.map((tag, tIdx) => (
                        <span
                          key={tIdx}
                          className="border border-neutral-300 bg-white px-1 py-0.2 text-neutral-600 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
