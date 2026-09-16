// PeersCharts component.
// Own-history valuation band panels and implied price judgement chart from payload.peers_page.part_b.
//
// Price determination rule:
// Uses payload.peers_page.part_b.last_close if it is a number. If it is a formatted string, we do NOT
// parse it silently (to prevent locale parsing anomalies); instead we take the numeric price from
// payload.cover.rating_box.price per the frozen contract. Every series comes directly from the payload.

import React from "react"
import type { ReportPayload } from "@/lib/reportPayload"
import { TOKENS, PendingBlock, formatIdn, formatPct } from "./tokens"

interface BandBlock {
  key: string
  label: string
  n: number
  mean: number
  median: number
  current: number
  percentile: number
  p10: number
  p90: number
  series: { date: string; value: number }[]
  narrative?: string
}

interface ImpliedRow {
  key: string
  label: string
  to_mean: number
  to_median: number
  low?: number
  high?: number
  is_range?: boolean
  delta_pct?: number
}

/**
 * Single multiple own-history valuation band panel.
 * Draws shaded P10-P90 distribution band, historical series polyline,
 * dashed median (buy green, pinned left), dotted mean (sell red, pinned right),
 * and current value marker with percentile.
 */
function BandPanel({ block }: { block: BandBlock }) {
  const W = 430
  const H = 170
  const pts = Array.isArray(block.series) ? block.series : []

  if (pts.length < 2) {
    return (
      <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4 text-center text-xs font-mono text-neutral-400 dark:border-[#262930] dark:bg-[#121418]">
        Series historis {block.label} tidak cukup data (&lt; 2 titik).
      </div>
    )
  }

  const vals = pts.map((p) => p.value).filter((v): v is number => typeof v === "number" && Number.isFinite(v))
  const p10 = typeof block.p10 === "number" ? block.p10 : null
  const p90 = typeof block.p90 === "number" ? block.p90 : null
  const mean = typeof block.mean === "number" ? block.mean : null
  const median = typeof block.median === "number" ? block.median : null

  const refs = [mean, median, p10, p90].filter((v): v is number => typeof v === "number" && Number.isFinite(v))
  const allPoints = [...vals, ...refs]
  const minVal = allPoints.length > 0 ? Math.min(...allPoints) : 0
  const maxVal = allPoints.length > 0 ? Math.max(...allPoints) : 1
  const pad = (maxVal - minVal) * 0.1 || 1.0
  const lo = minVal - pad
  const hi = maxVal + pad
  const span = hi - lo > 0 ? hi - lo : 1

  const n = pts.length
  const x = (i: number) => 4 + ((W - 14) * i) / Math.max(1, n - 1)
  const y = (v: number) => H - 22 - ((H - 40) * (v - lo)) / span

  const cur = pts[pts.length - 1]
  const curVal = cur.value
  const curX = x(n - 1)
  const curY = y(curVal)

  // Distribution band coordinates
  const y10 = p10 !== null ? y(p10) : null
  const y90 = p90 !== null ? y(p90) : null

  return (
    <div className="flex flex-col justify-between rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
      <div>
        <div className="mb-2 flex items-center justify-between border-b border-neutral-100 pb-1 dark:border-[#1f2228]">
          <span className="text-xs font-bold text-neutral-900 dark:text-neutral-100">
            {block.label} Historical Band (1-Year)
          </span>
          <span className="font-mono text-[10px] text-neutral-400">n = {block.n ?? n} sesi</span>
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block select-none" role="img">
          <rect x="0" y="0" width={W} height={H} rx="3" fill="#ffffff" />

          {/* Shaded P10-P90 Distribution Band */}
          {y10 !== null && y90 !== null && (
            <g>
              <rect
                x="4"
                y={y90}
                width={W - 8}
                height={Math.max(y10 - y90, 0.5)}
                fill="rgba(169,201,232,0.30)"
              />
              <line x1="4" y1={y90} x2={W - 4} y2={y90} stroke={TOKENS.ice} strokeWidth="0.7" />
              <line x1="4" y1={y10} x2={W - 4} y2={y10} stroke={TOKENS.ice} strokeWidth="0.7" />
            </g>
          )}

          {/* Average Reference Line (Sell Red, Pinned Right) */}
          {mean !== null && (
            <g>
              <line
                x1="4"
                y1={y(mean)}
                x2={W - 4}
                y2={y(mean)}
                stroke={TOKENS.sell}
                strokeWidth="1"
                strokeDasharray="5 3"
              />
              <text
                x={W - 6}
                y={y(mean) - 4}
                fontSize="8"
                fontWeight="bold"
                fill={TOKENS.sell}
                textAnchor="end"
                fontFamily="monospace"
              >
                rata-rata {formatIdn(mean, 1)}×
              </text>
            </g>
          )}

          {/* Median Reference Line (Buy Green, Pinned Left) */}
          {median !== null && (
            <g>
              <line
                x1="4"
                y1={y(median)}
                x2={W - 4}
                y2={y(median)}
                stroke={TOKENS.buy}
                strokeWidth="1"
                strokeDasharray="2 3"
              />
              <text
                x="6"
                y={y(median) - 4}
                fontSize="8"
                fontWeight="bold"
                fill={TOKENS.buy}
                textAnchor="start"
                fontFamily="monospace"
              >
                median {formatIdn(median, 1)}×
              </text>
            </g>
          )}

          {/* Series Polyline */}
          <polyline
            points={pts.map((p, i) => `${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ")}
            fill="none"
            stroke={TOKENS.navy}
            strokeWidth="1.8"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Current Value Marker & Tag */}
          <circle cx={curX} cy={curY} r="3.4" fill={TOKENS.navy} stroke="#ffffff" strokeWidth="1.2" />
          <text
            x={W - 6}
            y={curY - 6}
            fontSize="8.5"
            fontWeight="bold"
            fill={TOKENS.navy}
            textAnchor="end"
            fontFamily="monospace"
            className="tabular-nums"
          >
            {formatIdn(curVal, 1)}× · p{formatIdn(block.percentile, 0)}
          </text>

          {/* Date Axis Base Line */}
          <line x1="4" y1={H - 12} x2={W - 4} y2={H - 12} stroke={TOKENS.rule} strokeWidth="0.7" />
          <text x="6" y={H - 3} fontSize="8" fill={TOKENS.muted} fontFamily="monospace">
            {pts[0].date}
          </text>
          <text x={W - 6} y={H - 3} fontSize="8" fill={TOKENS.muted} textAnchor="end" fontFamily="monospace">
            {cur.date} · P10-P90 {p10 !== null ? formatIdn(p10, 0) : "-"}×-{p90 !== null ? formatIdn(p90, 0) : "-"}×
          </text>
        </svg>
      </div>

      {block.narrative && (
        <p className="mt-2 text-[11px] leading-relaxed text-neutral-700 dark:text-neutral-300 font-sans border-t border-neutral-100 pt-2 dark:border-[#1f2228]">
          {block.narrative}
        </p>
      )}
    </div>
  )
}

/**
 * Grouped bars SVG chart for Implied Price Judgement per multiple.
 * Draws to_mean in navy, to_median in ice, with a dashed red line at traded market price.
 */
function ImpliedPriceBars({
  rows,
  price,
  headline,
}: {
  rows: ImpliedRow[]
  price: number | null
  headline?: string
}) {
  const W = 660
  const H = 210
  const padL = 54
  const padR = 20
  const padT = 32
  const padB = 46
  const chartW = W - padL - padR
  const chartH = H - padT - padB

  const vals: number[] = []
  rows.forEach((r) => {
    if (typeof r.to_mean === "number") vals.push(r.to_mean)
    if (typeof r.to_median === "number") vals.push(r.to_median)
  })
  if (price !== null && price > 0) vals.push(price)

  const top = vals.length > 0 ? Math.max(...vals) * 1.22 : 1
  const n = rows.length
  if (n === 0) return null

  const gw = chartW / n
  const bw = Math.round(gw * 0.28)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block select-none" role="img" aria-label="Implied price per multiple">
      <rect x="0" y="0" width={W} height={H} rx="4" fill="#ffffff" stroke={TOKENS.rule} strokeWidth="0.75" />

      {/* Gridlines & Left Scale */}
      {[1.0, 0.5, 0.0].map((frac, idx) => {
        const gy = padT + chartH - chartH * frac
        const val = top * frac
        return (
          <g key={`impl-grid-${idx}`}>
            <line x1={padL} y1={gy} x2={W - padR} y2={gy} stroke={TOKENS.rule} strokeWidth="0.7" />
            <text
              x={padL - 6}
              y={gy + 3}
              fontSize="8"
              fill={TOKENS.muted}
              textAnchor="end"
              fontFamily="monospace"
              className="tabular-nums"
            >
              {formatIdn(val, 0)}
            </text>
          </g>
        )
      })}
      <text x={padL - 6} y={padT - 12} fontSize="7.5" fontWeight="bold" fill={TOKENS.muted} textAnchor="end">
        Rp/saham
      </text>

      {/* Dashed Red Market Price Line */}
      {price !== null && price > 0 && (
        <line
          x1={padL}
          y1={padT + chartH - chartH * (price / top)}
          x2={W - padR}
          y2={padT + chartH - chartH * (price / top)}
          stroke={TOKENS.sell}
          strokeWidth="1.5"
          strokeDasharray="5 3"
        />
      )}

      {/* Legend */}
      <rect x={padL} y="8" width="8" height="8" rx="1.5" fill={TOKENS.navy} />
      <text x={padL + 12} y="15.5" fontSize="8" fill={TOKENS.muted}>
        reversion ke 1Y mean
      </text>
      <rect x={padL + 124} y="8" width="8" height="8" rx="1.5" fill={TOKENS.ice} stroke="#2C4A6B" strokeWidth="0.8" />
      <text x={padL + 136} y="15.5" fontSize="8" fill={TOKENS.muted}>
        reversion ke 1Y median
      </text>
      {price !== null && price > 0 && (
        <g>
          <line
            x1={padL + 252}
            y1="12"
            x2={padL + 274}
            y2="12"
            stroke={TOKENS.sell}
            strokeWidth="1.4"
            strokeDasharray="4 3"
          />
          <text x={padL + 280} y="15.5" fontSize="8" fill={TOKENS.sell} fontWeight="bold" fontFamily="monospace">
            harga pasar {formatIdn(price, 0)}
          </text>
        </g>
      )}

      {/* Grouped Bars per multiple */}
      {rows.map((r, i) => {
        const cx = padL + gw * i + gw / 2
        const isAnchor = Boolean(headline && (r.key === headline || r.label.toLowerCase().includes(headline.toLowerCase())))

        return (
          <g key={`grp-${i}`}>
            {/* to_mean bar (Navy) */}
            {typeof r.to_mean === "number" && (
              <g>
                <rect
                  x={cx - bw - 1}
                  y={padT + chartH - chartH * (r.to_mean / top)}
                  width={bw}
                  height={chartH * (r.to_mean / top)}
                  fill={TOKENS.navy}
                  rx="1.5"
                />
                <text
                  x={cx - bw / 2 - 1}
                  y={padT + chartH - chartH * (r.to_mean / top) - 3}
                  fontSize="7.5"
                  fontWeight="bold"
                  fill={TOKENS.navy}
                  textAnchor="middle"
                  fontFamily="monospace"
                  className="tabular-nums"
                >
                  {formatIdn(r.to_mean, 0)}
                </text>
              </g>
            )}

            {/* to_median bar (Ice) */}
            {typeof r.to_median === "number" && (
              <g>
                <rect
                  x={cx + 1}
                  y={padT + chartH - chartH * (r.to_median / top)}
                  width={bw}
                  height={chartH * (r.to_median / top)}
                  fill={TOKENS.ice}
                  stroke="#2C4A6B"
                  strokeWidth="0.8"
                  rx="1.5"
                />
                <text
                  x={cx + bw / 2 + 1}
                  y={padT + chartH - chartH * (r.to_median / top) - 3}
                  fontSize="7.5"
                  fontWeight="bold"
                  fill={TOKENS.muted}
                  textAnchor="middle"
                  fontFamily="monospace"
                  className="tabular-nums"
                >
                  {formatIdn(r.to_median, 0)}
                </text>
              </g>
            )}

            {/* Multiple Label */}
            <text
              x={cx}
              y={H - 30}
              fontSize="8.5"
              fontWeight="bold"
              fill={TOKENS.navy}
              textAnchor="middle"
              fontFamily="monospace"
            >
              {r.label}
              {isAnchor ? " *" : ""}
            </text>

            {/* Delta % */}
            <text
              x={cx}
              y={H - 18}
              fontSize="7.5"
              fill={TOKENS.muted}
              textAnchor="middle"
              fontFamily="monospace"
              className="tabular-nums"
            >
              {typeof r.delta_pct === "number" ? formatPct(r.delta_pct, 0) : "-"}
            </text>
          </g>
        )
      })}

      <line x1={padL} y1={padT + chartH} x2={W - padR} y2={padT + chartH} stroke="#2C4A6B" strokeWidth="0.9" />
    </svg>
  )
}

export function PeersCharts({ payload }: { payload: ReportPayload }) {
  const p = payload as Record<string, any>
  const peersPage = p.peers_page
  const partB = peersPage?.part_b

  if (!peersPage || peersPage.available === false || !partB) {
    return (
      <PendingBlock
        label="Own history & implied price"
        message="data valuasi historis / peers part B belum tersedia di payload."
      />
    )
  }

  const bands: BandBlock[] = Array.isArray(partB.bands) ? partB.bands : []
  const impliedRows: ImpliedRow[] = Array.isArray(partB.implied) ? partB.implied : []

  // Price resolution:
  // Use payload.peers_page.part_b.last_close if it is a number. If it is a formatted string (e.g. "Rp 4.860"),
  // we do not parse it into a number silently - we take the clean numeric price from payload.cover.rating_box.price
  // instead to avoid localization parsing errors and adhere strictly to the frozen data contract.
  let price: number | null = null
  if (typeof partB.last_close === "number" && Number.isFinite(partB.last_close)) {
    price = partB.last_close
  } else if (typeof p.cover?.rating_box?.price === "number" && Number.isFinite(p.cover.rating_box.price)) {
    price = p.cover.rating_box.price
  } else if (typeof p.valuation_page?.drivers?.price === "number") {
    price = p.valuation_page.drivers.price
  }

  const anchor = p.valuation?.anchor ?? p.valuation_page?.drivers?.revenue_basis ?? ""

  return (
    <div className="space-y-5 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            Valuasi Relatif Historis - Own History (Time-Series)
          </h3>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            {partB.methodology ??
              "Evaluasi posisi multiple historis 1 tahun terhadap distribusi (mean, median, persentil) dan harga implisit."}
          </p>
        </div>
        <span className="font-mono text-[10px] text-neutral-400">
          SUMBER: {(partB.sources ?? ["Sectors API v2 time-series"]).join("; ")}
        </span>
      </div>

      {/* Historical Band Panels (P/E, P/BV, EV/EBITDA, EV/Sales) */}
      {bands.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {bands.map((blk, idx) => (
            <BandPanel key={blk.key ?? idx} block={blk} />
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4 text-center text-xs font-mono text-neutral-400 dark:border-[#262930] dark:bg-[#121418]">
          Panel band historis belum tersedia.
        </div>
      )}

      {/* Implied Price Section */}
      {impliedRows.length > 0 && (
        <div className="rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
          <div className="mb-2.5 flex items-center justify-between border-b border-neutral-100 pb-2 dark:border-[#1f2228]">
            <div className="flex items-center gap-2">
              <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
                IMPLIED
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
                Implied Price Judgement
              </span>
            </div>
            {price !== null && (
              <span className="font-mono text-[10px] font-bold text-[#C0392B]">
                Harga Acuan: Rp {formatIdn(price, 0)}
              </span>
            )}
          </div>

          {/* Grouped Bar Chart */}
          <div className="mb-4">
            <ImpliedPriceBars rows={impliedRows} price={price} headline={anchor} />
            <p className="mt-2 font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
              Batang = harga implisit bila kelipatan kembali ke rata-rata (navy) atau median (ice) 1 tahun; garis putus-putus merah = harga pasar. Tanda * menandai kelipatan yang menjadi basis anchor target price.
            </p>
          </div>

          {/* Implied Price Table */}
          <div className="overflow-x-auto rounded border border-neutral-200 dark:border-[#262930]">
            <table className="w-full border-collapse text-xs font-mono">
              <thead>
                <tr className="bg-[#0B1F3A] text-white">
                  <th className="px-3 py-1.5 text-left font-bold">Multiple</th>
                  <th className="px-3 py-1.5 text-right font-bold">Reversion ke Mean (Rp)</th>
                  <th className="px-3 py-1.5 text-right font-bold">Reversion ke Median (Rp)</th>
                  <th className="px-3 py-1.5 text-right font-bold">Rentang</th>
                  <th className="px-3 py-1.5 text-right font-bold">Selisih</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-[#262930]">
                {impliedRows.map((r, rIdx) => {
                  const rangeText = r.is_range && typeof r.low === "number" && typeof r.high === "number"
                    ? `Rp ${formatIdn(r.low, 0)} – ${formatIdn(r.high, 0)}`
                    : "konvergen"

                  return (
                    <tr
                      key={r.key ?? rIdx}
                      className="hover:bg-neutral-50 dark:hover:bg-[#181a1f]/50 even:bg-neutral-50/50 dark:even:bg-[#181a1f]/30"
                    >
                      <td className="px-3 py-1.5 font-bold text-neutral-900 dark:text-neutral-100">
                        {r.label}
                      </td>
                      <td className="px-3 py-1.5 text-right font-semibold text-[#0B1F3A] tabular-nums dark:text-sky-400">
                        {typeof r.to_mean === "number" ? formatIdn(r.to_mean, 0) : "-"}
                      </td>
                      <td className="px-3 py-1.5 text-right font-semibold text-neutral-700 tabular-nums dark:text-neutral-300">
                        {typeof r.to_median === "number" ? formatIdn(r.to_median, 0) : "-"}
                      </td>
                      <td className="px-3 py-1.5 text-right text-neutral-600 tabular-nums dark:text-neutral-400">
                        {rangeText}
                      </td>
                      <td className="px-3 py-1.5 text-right font-bold tabular-nums text-neutral-900 dark:text-neutral-100">
                        {typeof r.delta_pct === "number" ? formatPct(r.delta_pct, 0) : "-"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footnotes & Disclaimers */}
          <div className="mt-3 space-y-1.5 font-sans text-xs">
            {partB.driver_note && (
              <p className="font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
                {partB.last_close !== undefined ? `Harga terakhir: ${partB.last_close} · ` : ""}
                {partB.driver_note}
              </p>
            )}
            {partB.disclaimer && (
              <div className="rounded border-l-2 border-[#0B1F3A] bg-sky-50/50 p-2.5 text-[11px] leading-relaxed text-neutral-800 dark:border-sky-500 dark:bg-sky-950/30 dark:text-neutral-200">
                <span className="font-bold">Catatan: </span>
                {partB.disclaimer}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
