import { useState, useMemo } from "react"
import {
  Newspaper,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Clock,
  Tag,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  CircleDot,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { NewsResponse, NewsArticleItem } from "@/lib/api"

interface NewsFeedCardProps {
  ticker: string
  data?: NewsResponse | null
  isLoading?: boolean
}

type SentimentFilter = "all" | "bullish" | "bearish" | "neutral"

function formatTimestamp(ts: string): string {
  if (!ts) return "N/A"
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

function getHostFromUrl(urlStr: string): string {
  if (!urlStr) return "Public Source"
  try {
    const u = new URL(urlStr)
    return u.hostname.replace(/^www\./, "")
  } catch {
    return urlStr.length > 25 ? `${urlStr.slice(0, 25)}...` : urlStr
  }
}

export function NewsFeedCard({ ticker, data, isLoading }: NewsFeedCardProps) {
  const [filter, setFilter] = useState<SentimentFilter>("all")
  const [expandedIds, setExpandedIds] = useState<Record<number, boolean>>({})

  const articles = useMemo(() => {
    if (!data?.data || !Array.isArray(data.data)) return []
    return data.data
  }, [data])

  const toggleExpand = (idx: number) => {
    setExpandedIds((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  // Sentiment counts
  const sentimentCounts = useMemo(() => {
    const counts = { all: articles.length, bullish: 0, bearish: 0, neutral: 0 }
    articles.forEach((a) => {
      const s = a.dimension?.sentiment?.toLowerCase() || "neutral"
      if (s === "bullish") counts.bullish += 1
      else if (s === "bearish") counts.bearish += 1
      else counts.neutral += 1
    })
    return counts
  }, [articles])

  // Filtered articles
  const filteredArticles = useMemo(() => {
    if (filter === "all") return articles
    return articles.filter((a) => {
      const s = a.dimension?.sentiment?.toLowerCase() || "neutral"
      return s === filter
    })
  }, [articles, filter])

  return (
    <Card className="overflow-hidden border-slate-200 shadow-sm">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold text-slate-900">
                Sentiment-Tagged News Feed
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[11px] text-slate-700">
                {ticker}
              </Badge>
            </div>
            <CardDescription className="mt-1 text-xs text-slate-500">
              Curated articles & public releases with automated keyword sentiment tagging
            </CardDescription>
          </div>

          {/* Sentiment Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === "all"
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              All ({sentimentCounts.all})
            </button>
            <button
              type="button"
              onClick={() => setFilter("bullish")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === "bullish"
                  ? "bg-emerald-700 text-white"
                  : "bg-white text-emerald-700 border border-emerald-200 hover:bg-emerald-50"
              }`}
            >
              <TrendingUp className="h-3 w-3" />
              Bullish ({sentimentCounts.bullish})
            </button>
            <button
              type="button"
              onClick={() => setFilter("bearish")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === "bearish"
                  ? "bg-rose-700 text-white"
                  : "bg-white text-rose-700 border border-rose-200 hover:bg-rose-50"
              }`}
            >
              <TrendingDown className="h-3 w-3" />
              Bearish ({sentimentCounts.bearish})
            </button>
            <button
              type="button"
              onClick={() => setFilter("neutral")}
              className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === "neutral"
                  ? "bg-slate-700 text-white"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              <MinusCircle className="h-3 w-3" />
              Neutral ({sentimentCounts.neutral})
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {isLoading ? (
          <div className="flex h-56 items-center justify-center space-x-2 text-slate-400">
            <CircleDot className="h-5 w-5 animate-pulse text-slate-400" />
            <span className="text-sm font-medium">Loading news feed for {ticker}...</span>
          </div>
        ) : articles.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-800">
              No news available for {ticker}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {data?.note || `No news articles indexed for ${ticker} from free public sources.`}
            </p>
          </div>
        ) : filteredArticles.length === 0 ? (
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-6 text-center text-xs text-slate-500">
            No articles match the selected sentiment filter ({filter}).
          </div>
        ) : (
          <div className="space-y-3">
            {filteredArticles.map((item, idx) => {
              const sentiment = item.dimension?.sentiment?.toLowerCase() || "neutral"
              const relevance = item.dimension?.relevance
              const isExpanded = !!expandedIds[idx]
              const hasBody = Boolean(item.body && item.body.trim().length > 0)
              const isExternalUrl = Boolean(
                item.source &&
                (item.source.startsWith("http://") || item.source.startsWith("https://"))
              )

              return (
                <div
                  key={idx}
                  className="group rounded-xl border border-slate-200 bg-white p-4 transition-all hover:border-slate-300 hover:shadow-xs"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1.5 flex-1 pr-2">
                      {/* Sentiment Badge & Metadata line */}
                      <div className="flex flex-wrap items-center gap-2">
                        {sentiment === "bullish" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                            <TrendingUp className="h-3 w-3" />
                            Bullish
                          </span>
                        )}
                        {sentiment === "bearish" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                            <TrendingDown className="h-3 w-3" />
                            Bearish
                          </span>
                        )}
                        {sentiment === "neutral" && (
                          <span className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                            <MinusCircle className="h-3 w-3" />
                            Neutral
                          </span>
                        )}

                        {relevance != null && (
                          <span className="text-[11px] font-mono text-slate-500">
                            rel: {(relevance * 100).toFixed(0)}%
                          </span>
                        )}

                        {item.sector && (
                          <span className="text-[11px] text-slate-500 capitalize">
                            · {item.sector}
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

                      {isExternalUrl ? (
                        <a
                          href={item.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-900 underline decoration-slate-300 underline-offset-2"
                        >
                          <span>{getHostFromUrl(item.source)}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-[11px] text-slate-400">
                          {getHostFromUrl(item.source)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Expandable Snippet / Body */}
                  {hasBody && (
                    <div className="mt-2.5 pt-2.5 border-t border-slate-100">
                      {isExpanded ? (
                        <p className="text-xs leading-relaxed text-slate-700 whitespace-pre-line">
                          {item.body}
                        </p>
                      ) : (
                        <p className="text-xs leading-relaxed text-slate-600 line-clamp-2">
                          {item.body}
                        </p>
                      )}

                      <button
                        type="button"
                        onClick={() => toggleExpand(idx)}
                        className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 hover:text-slate-900 cursor-pointer"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="h-3 w-3" />
                            Show less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3 w-3" />
                            Click to expand full snippet
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* Tags list */}
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
