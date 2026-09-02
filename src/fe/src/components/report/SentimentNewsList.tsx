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
  Inbox,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { NewsArticleItem, Sentiment } from "@/lib/api"

export type SentimentNewsListProps = {
  ticker: string
  articles?: NewsArticleItem[]
  socialItems?: Sentiment["items"]
  isLoading?: boolean
}

type SentimentFilter = "all" | "bullish" | "bearish" | "neutral"

function formatTimestamp(ts?: string): string {
  if (!ts) return "Baru saja"
  try {
    const d = new Date(ts)
    if (Number.isNaN(d.getTime())) return ts
    return d.toLocaleDateString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  } catch {
    return ts
  }
}

function getHostName(urlStr?: string): string {
  if (!urlStr) return "Kanal Publik"
  try {
    const u = new URL(urlStr)
    return u.hostname.replace(/^www\./, "")
  } catch {
    return urlStr.length > 25 ? `${urlStr.slice(0, 25)}...` : urlStr
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
      sentiment: "bullish" | "bearish" | "neutral"
      timestamp: string
      url?: string
      author?: string
      tags?: string[]
      relevance?: number
    }> = []

    // Map news articles
    articles.forEach((a, idx) => {
      const sentRaw = a.dimension?.sentiment?.toLowerCase() || "neutral"
      const sent: "bullish" | "bearish" | "neutral" =
        sentRaw === "bullish" || sentRaw === "positif"
          ? "bullish"
          : sentRaw === "bearish" || sentRaw === "negatif"
          ? "bearish"
          : "neutral"

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
      const score = s.score ?? 50
      const sent: "bullish" | "bearish" | "neutral" =
        score >= 60 ? "bullish" : score <= 40 ? "bearish" : "neutral"

      list.push({
        id: `social-${idx}`,
        type: "social",
        title: s.text?.slice(0, 70) ? `${s.text.slice(0, 70)}...` : `Postingan ${s.platform || "Ritel"}`,
        body: s.text || "",
        source: s.platform || "Forum Komunitas",
        platform: s.platform || "Stockbit / X",
        sentiment: sent,
        timestamp: s.timestamp || "",
        url: s.url,
        author: s.author,
      })
    })

    return list
  }, [articles, socialItems])

  const sentimentCounts = useMemo(() => {
    const counts = { all: combinedEntries.length, bullish: 0, bearish: 0, neutral: 0 }
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
    <Card className="border-slate-200 bg-white shadow-2xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 p-4 pb-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Newspaper className="h-4 w-4 text-slate-700" />
              <CardTitle className="text-sm font-semibold text-slate-900">
                Arus Berita & Diskusi Ritel Terverifikasi
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[11px] text-slate-700">
                {tk}
              </Badge>
            </div>
            <CardDescription className="text-xs text-slate-500">
              Kompilasi artikel media finansial dan diskusi media sosial publik
            </CardDescription>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                filter === "all"
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              Semua ({sentimentCounts.all})
            </button>

            <button
              type="button"
              onClick={() => setFilter("bullish")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                filter === "bullish"
                  ? "bg-emerald-700 text-white"
                  : "bg-white text-emerald-700 border border-emerald-200 hover:bg-emerald-50"
              }`}
            >
              <TrendingUp className="h-3 w-3" />
              Positif ({sentimentCounts.bullish})
            </button>

            <button
              type="button"
              onClick={() => setFilter("bearish")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                filter === "bearish"
                  ? "bg-rose-700 text-white"
                  : "bg-white text-rose-700 border border-rose-200 hover:bg-rose-50"
              }`}
            >
              <TrendingDown className="h-3 w-3" />
              Negatif ({sentimentCounts.bearish})
            </button>

            <button
              type="button"
              onClick={() => setFilter("neutral")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                filter === "neutral"
                  ? "bg-slate-700 text-white"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              <MinusCircle className="h-3 w-3" />
              Netral ({sentimentCounts.neutral})
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {isLoading ? (
          <div className="flex h-44 items-center justify-center space-x-2 text-slate-400">
            <span className="text-xs">Memuat daftar berita dan diskusi {tk}...</span>
          </div>
        ) : combinedEntries.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center">
            <Inbox className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-800">
              Belum ada artikel atau diskusi terindeks untuk {tk}
            </p>
            <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
              Data sentimen ritel (Stockbit, X, media berita) dikumpulkan secara dinamis saat News Harvester dan Social Sentiment agents dijalankan.
            </p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-6 text-center text-xs text-slate-500">
            Tidak ada entri yang cocok dengan filter sentimen ({filter}).
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEntries.map((item) => {
              const isExpanded = !!expandedIds[item.id]
              const hasBody = Boolean(item.body && item.body.trim().length > 0)

              return (
                <div
                  key={item.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 transition-all hover:border-slate-300 hover:shadow-2xs"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1.5 flex-1 pr-2">
                      {/* Top badge row */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {item.sentiment === "bullish" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                            <TrendingUp className="h-3 w-3" />
                            Positif / Bullish
                          </span>
                        )}
                        {item.sentiment === "bearish" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                            <TrendingDown className="h-3 w-3" />
                            Negatif / Bearish
                          </span>
                        )}
                        {item.sentiment === "neutral" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                            <MinusCircle className="h-3 w-3" />
                            Netral
                          </span>
                        )}

                        <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-600">
                          {item.type === "news" ? "Media Finansial" : "Diskusi Komunitas"}
                        </span>

                        {item.relevance != null && (
                          <span className="text-[11px] font-mono text-slate-400">
                            rel: {(item.relevance * 100).toFixed(0)}%
                          </span>
                        )}

                        {item.author && (
                          <span className="text-[11px] text-slate-500">
                            oleh @{item.author}
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <h4 className="text-sm font-semibold leading-snug text-slate-900">
                        {item.title}
                      </h4>
                    </div>

                    {/* Source & Date info */}
                    <div className="flex shrink-0 items-center gap-3 text-xs text-slate-500 sm:flex-col sm:items-end sm:gap-1">
                      <div className="flex items-center gap-1 font-mono text-[11px]">
                        <Clock className="h-3 w-3 text-slate-400" />
                        {formatTimestamp(item.timestamp)}
                      </div>

                      {item.url ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 hover:text-slate-900 underline decoration-slate-300 underline-offset-2"
                        >
                          <span>{item.platform}</span>
                          <ExternalLink className="h-3 w-3 text-slate-400" />
                        </a>
                      ) : (
                        <span className="text-[11px] text-slate-500">
                          {item.platform}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Body text & Expand */}
                  {hasBody && (
                    <div className="mt-2.5 pt-2.5 border-t border-slate-100">
                      <p
                        className={`text-xs leading-relaxed text-slate-700 ${
                          isExpanded ? "whitespace-pre-line" : "line-clamp-2"
                        }`}
                      >
                        {item.body}
                      </p>

                      {item.body.length > 140 && (
                        <button
                          type="button"
                          onClick={() => toggleExpand(item.id)}
                          className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 hover:text-slate-900 cursor-pointer"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3 w-3" />
                              Ringkas teks
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3" />
                              Tampilkan selengkapnya
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Tags */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap items-center gap-1">
                      {item.tags.map((tag, tIdx) => (
                        <span
                          key={tIdx}
                          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-600"
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
