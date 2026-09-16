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

function BandPanel({ block }: { block: BandBlock }) {
  const W = 430
  const H = 170
  const pts = Array.isArray(block.series) ? block.series : []

  if (pts.length < 2) {
    return (
      <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
        Data historis {block.label} tidak mencukupi (&lt; 2 titik).
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

  const y10 = p10 !== null ? y(p10) : null
  const y90 = p90 !== null ? y(p90) : null

  return (
    <div className="flex flex-col justify-between rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
      <div>
        <div className="mb-2 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-1.5 dark:border-[#2A2822]">
          <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Rentang historis {block.label} (1 tahun)
          </span>
          <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">n = {block.n ?? n} sesi</span>
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block select-none" role="img">
          <rect x="0" y="0" width={W} height={H} rx="4" fill="#ffffff" />

          {/* Shaded P10-P90 Distribution Band */}
          {y10 !== null && y90 !== null && (
            <g>
              <rect
                x="4"
                y={y90}
                width={W - 8}
                height={Math.max(y10 - y90, 0.5)}
                fill="rgba(14,110,99,0.08)"
              />
              <line x1="4" y1={y90} x2={W - 4} y2={y90} stroke="#0E6E63" strokeOpacity={0.25} strokeWidth="0.7" />
              <line x1="4" y1={y10} x2={W - 4} y2={y10} stroke="#0E6E63" strokeOpacity={0.25} strokeWidth="0.7" />
            </g>
          )}

          {/* Average Reference Line */}
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
                fontFamily="sans-serif"
              >
                Rata-rata {formatIdn(mean, 1)}×
              </text>
            </g>
          )}

          {/* Median Reference Line */}
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
                fontFamily="sans-serif"
              >
                Median {formatIdn(median, 1)}×
              </text>
            </g>
          )}

          {/* Series Polyline */}
          <polyline
            points={pts.map((p, i) => `${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ")}
            fill="none"
            stroke={TOKENS.teal}
            strokeWidth="1.8"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Current Value Marker */}
          <circle cx={curX} cy={curY} r="3.4" fill={TOKENS.teal} stroke="#ffffff" strokeWidth="1.2" />
          <text
            x={W - 6}
            y={curY - 6}
            fontSize="8.5"
            fontWeight="bold"
            fill={TOKENS.teal}
            textAnchor="end"
            fontFamily="monospace"
            className="tabular-nums"
          >
            {formatIdn(curVal, 1)}× · p{formatIdn(block.percentile, 0)}
          </text>

          {/* Date Axis Base Line */}
          <line x1="4" y1={H - 12} x2={W - 4} y2={H - 12} stroke={TOKENS.rule} strokeWidth="0.7" />
          <text x="6" y={H - 3} fontSize="8" fill={TOKENS.muted}>
            {pts[0].date}
          </text>
          <text x={W - 6} y={H - 3} fontSize="8" fill={TOKENS.muted} textAnchor="end">
            {cur.date} · P10-P90 {p10 !== null ? formatIdn(p10, 0) : "-"}×-{p90 !== null ? formatIdn(p90, 0) : "-"}×
          </text>
        </svg>
      </div>

      {block.narrative && (
        <p className="mt-2 text-xs leading-relaxed text-[#6B6659] border-t border-[#E7E3DA]/60 pt-2 dark:border-[#2A2822] dark:text-[#A8A296]">
          {block.narrative}
        </p>
      )}
    </div>
  )
}

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
      <rect x="0" y="0" width={W} height={H} rx="6" fill="#ffffff" stroke={TOKENS.rule} strokeWidth="0.75" />

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
      <rect x={padL} y="8" width="8" height="8" rx="2" fill={TOKENS.teal} />
      <text x={padL + 12} y="15.5" fontSize="8" fill={TOKENS.muted}>
        Reversion ke rata-rata 1Y
      </text>
      <rect x={padL + 130} y="8" width="8" height="8" rx="2" fill={TOKENS.tealLight} />
      <text x={padL + 142} y="15.5" fontSize="8" fill={TOKENS.muted}>
        Reversion ke median 1Y
      </text>
      {price !== null && price > 0 && (
        <g>
          <line
            x1={padL + 258}
            y1="12"
            x2={padL + 280}
            y2="12"
            stroke={TOKENS.sell}
            strokeWidth="1.4"
            strokeDasharray="4 3"
          />
          <text x={padL + 286} y="15.5" fontSize="8" fill={TOKENS.sell} fontWeight="bold" fontFamily="monospace">
            Harga pasar {formatIdn(price, 0)}
          </text>
        </g>
      )}

      {/* Grouped Bars per multiple */}
      {rows.map((r, i) => {
        const cx = padL + gw * i + gw / 2
        const isAnchor = Boolean(headline && (r.key === headline || r.label.toLowerCase().includes(headline.toLowerCase())))

        return (
          <g key={`grp-${i}`}>
            {/* to_mean bar */}
            {typeof r.to_mean === "number" && (
              <g>
                <rect
                  x={cx - bw - 1}
                  y={padT + chartH - chartH * (r.to_mean / top)}
                  width={bw}
                  height={chartH * (r.to_mean / top)}
                  fill={TOKENS.teal}
                  rx="2"
                />
                <text
                  x={cx - bw / 2 - 1}
                  y={padT + chartH - chartH * (r.to_mean / top) - 3}
                  fontSize="7.5"
                  fontWeight="bold"
                  fill={TOKENS.teal}
                  textAnchor="middle"
                  fontFamily="monospace"
                  className="tabular-nums"
                >
                  {formatIdn(r.to_mean, 0)}
                </text>
              </g>
            )}

            {/* to_median bar */}
            {typeof r.to_median === "number" && (
              <g>
                <rect
                  x={cx + 1}
                  y={padT + chartH - chartH * (r.to_median / top)}
                  width={bw}
                  height={chartH * (r.to_median / top)}
                  fill={TOKENS.tealLight}
                  rx="2"
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

      <line x1={padL} y1={padT + chartH} x2={W - padR} y2={padT + chartH} stroke={TOKENS.rule} strokeWidth="0.9" />
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
        label="Valuasi relatif historis"
        message="data valuasi historis / peers part B belum tersedia di payload."
      />
    )
  }

  const bands: BandBlock[] = Array.isArray(partB.bands) ? partB.bands : []
  const impliedRows: ImpliedRow[] = Array.isArray(partB.implied) ? partB.implied : []

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
      {/* Historical Band Panels */}
      {bands.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {bands.map((blk, idx) => (
            <BandPanel key={blk.key ?? idx} block={blk} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          Panel rentang historis belum tersedia.
        </div>
      )}

      {/* Implied Price Section */}
      {impliedRows.length > 0 && (
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="mb-3 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
            <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Penilaian harga implisit (Implied price)
            </span>
            {price !== null && (
              <span className="text-xs font-medium text-[#B4232A] dark:text-[#F87171]">
                Harga acuan: Rp {formatIdn(price, 0)}
              </span>
            )}
          </div>

          {/* Grouped Bar Chart */}
          <div className="mb-4">
            <ImpliedPriceBars rows={impliedRows} price={price} headline={anchor} />
            <p className="mt-2 text-xs text-[#6B6659] dark:text-[#A8A296]">
              Batang = harga implisit bila kelipatan kembali ke rata-rata (teal) atau median (teal muda) 1 tahun; garis putus-putus merah = harga pasar. Tanda * menandai kelipatan yang menjadi basis anchor target price.
            </p>
          </div>

          {/* Implied Price Table */}
          <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                  <th className="px-3 py-2 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Kelipatan</th>
                  <th className="px-3 py-2 text-right font-semibold">Kembali ke rata-rata (Rp)</th>
                  <th className="px-3 py-2 text-right font-semibold">Kembali ke median (Rp)</th>
                  <th className="px-3 py-2 text-right font-semibold">Rentang</th>
                  <th className="px-3 py-2 text-right font-semibold">Selisih</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                {impliedRows.map((r, rIdx) => {
                  const rangeText = r.is_range && typeof r.low === "number" && typeof r.high === "number"
                    ? `Rp ${formatIdn(r.low, 0)} – ${formatIdn(r.high, 0)}`
                    : "konvergen"

                  return (
                    <tr
                      key={r.key ?? rIdx}
                      className={`${
                        rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                      }`}
                    >
                      <td className="px-3 py-2 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                        {r.label}
                      </td>
                      <td className="px-3 py-2 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                        {typeof r.to_mean === "number" ? formatIdn(r.to_mean, 0) : "-"}
                      </td>
                      <td className="px-3 py-2 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                        {typeof r.to_median === "number" ? formatIdn(r.to_median, 0) : "-"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-[#6B6659] dark:text-[#A8A296]">
                        {rangeText}
                      </td>
                      <td className="px-3 py-2 text-right font-semibold font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                        {typeof r.delta_pct === "number" ? formatPct(r.delta_pct, 0) : "-"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footnotes & Disclaimers */}
          <div className="mt-3.5 space-y-1.5 text-xs">
            {partB.driver_note && (
              <p className="text-[#6B6659] dark:text-[#A8A296]">
                {partB.last_close !== undefined ? `Harga terakhir: ${partB.last_close} · ` : ""}
                {partB.driver_note}
              </p>
            )}
            {partB.disclaimer && (
              <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-xs text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
                <span className="font-semibold">Catatan: </span>
                {partB.disclaimer}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
