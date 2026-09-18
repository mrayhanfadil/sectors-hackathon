import React from "react"
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ReferenceArea,
  ReferenceDot,
  LabelList,
} from "recharts"
import type { ReportPayload } from "@/lib/reportPayload"
import { PendingBlock, formatIdn, formatPct } from "./tokens"
import {
  seriesColor,
  SECTORAL_GRID,
  SECTORAL_ZERO_BASELINE,
  SECTORAL_TICK,
  SECTORAL_TOOLTIP_STYLE,
  SECTORAL_LEGEND_STYLE,
} from "./sectoralSeries"

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
  const pts = Array.isArray(block.series) ? block.series : []

  if (pts.length < 2) {
    return (
      <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
        Data historis {block.label} tidak mencukupi (&lt; 2 titik).
      </div>
    )
  }

  const p10 = typeof block.p10 === "number" ? block.p10 : null
  const p90 = typeof block.p90 === "number" ? block.p90 : null
  const mean = typeof block.mean === "number" ? block.mean : null
  const median = typeof block.median === "number" ? block.median : null
  const cur = pts[pts.length - 1]

  const data = pts.map((p) => ({ name: p.date, value: p.value }))

  return (
    <div className="flex flex-col justify-between rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
      <div>
        <div className="mb-2 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-1.5 dark:border-[#2A2822]">
          <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Rentang historis {block.label} (1 tahun)
          </span>
          <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">n = {block.n ?? pts.length} sesi</span>
        </div>

        <ResponsiveContainer width="100%" height={170}>
          <ComposedChart data={data} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={SECTORAL_GRID} />
            <XAxis dataKey="name" tick={SECTORAL_TICK} axisLine={false} tickLine={false} interval="preserveStartEnd" minTickGap={60} />
            <YAxis tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, 1)} width={44} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={SECTORAL_TOOLTIP_STYLE}
              formatter={(value: unknown) => [typeof value === "number" ? `${formatIdn(value, 1)}×` : "-", block.label]}
              labelFormatter={(label: unknown) => String(label)}
            />
            <Legend iconType="square" wrapperStyle={SECTORAL_LEGEND_STYLE} />
            <ReferenceLine y={0} stroke={SECTORAL_ZERO_BASELINE} />
            {p10 !== null && p90 !== null && (
              <ReferenceArea y1={p10} y2={p90} fill={seriesColor(0)} fillOpacity={0.08} stroke={seriesColor(0)} strokeOpacity={0.25} />
            )}
            {mean !== null && (
              <ReferenceLine y={mean} stroke={seriesColor(4)} strokeDasharray="5 3" label={{ value: `Rata-rata ${formatIdn(mean, 1)}×`, fontSize: 11, fill: seriesColor(4), position: "insideTopRight" }} />
            )}
            {median !== null && (
              <ReferenceLine y={median} stroke={seriesColor(2)} strokeDasharray="2 3" label={{ value: `Median ${formatIdn(median, 1)}×`, fontSize: 11, fill: seriesColor(2), position: "insideTopLeft" }} />
            )}
            <Line type="monotone" dataKey="value" name={block.label} stroke={seriesColor(0)} strokeWidth={2} dot={false} activeDot={{ r: 4 }} connectNulls />
            {cur && typeof cur.value === "number" && (
              <ReferenceDot x={cur.date} y={cur.value} r={4} fill={seriesColor(0)} stroke="#ffffff" />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        <p className="mt-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
          Terkini {typeof cur?.value === "number" ? `${formatIdn(cur.value, 1)}× · p${formatIdn(block.percentile, 0)}` : "-"} · P10-P90 {p10 !== null ? formatIdn(p10, 0) : "-"}×-{p90 !== null ? formatIdn(p90, 0) : "-"}×
        </p>
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
  const n = rows.length
  if (n === 0) return null

  const data = rows.map((r) => ({
    name: r.label + (headline && (r.key === headline || r.label.toLowerCase().includes(headline.toLowerCase())) ? " *" : ""),
    mean: typeof r.to_mean === "number" ? r.to_mean : null,
    median: typeof r.to_median === "number" ? r.to_median : null,
    meanLabel: typeof r.to_mean === "number" ? formatIdn(r.to_mean, 0) : "",
    medianLabel: typeof r.to_median === "number" ? formatIdn(r.to_median, 0) : "",
    delta: typeof r.delta_pct === "number" ? formatPct(r.delta_pct, 0) : "-",
  }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={210}>
        <ComposedChart data={data} margin={{ top: 20, right: 16, left: 0, bottom: 0 }} aria-label="Implied price per multiple">
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={SECTORAL_GRID} />
          <XAxis dataKey="name" tick={SECTORAL_TICK} axisLine={false} tickLine={false} interval={0} angle={0} height={44} />
          <YAxis tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, 0)} width={48} />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            contentStyle={SECTORAL_TOOLTIP_STYLE}
            formatter={(value: unknown, name: unknown) => [
              typeof value === "number" ? formatIdn(value, 0) : "-",
              String(name) === "mean" ? "Kembali ke rata-rata (Rp)" : "Kembali ke median (Rp)",
            ]}
            labelFormatter={(label: unknown) => String(label)}
          />
          <Legend iconType="square" wrapperStyle={SECTORAL_LEGEND_STYLE} />
          <ReferenceLine y={0} stroke={SECTORAL_ZERO_BASELINE} />
          {price !== null && price > 0 && (
            <ReferenceLine y={price} stroke={seriesColor(4)} strokeDasharray="5 3" label={{ value: `Harga pasar ${formatIdn(price, 0)}`, fontSize: 11, fill: seriesColor(4), position: "insideTopLeft" }} />
          )}
          <Bar dataKey="mean" name="Reversion ke rata-rata 1Y" fill={seriesColor(0)} maxBarSize={40} radius={[2, 2, 0, 0]}>
            <LabelList dataKey="meanLabel" position="top" fill={seriesColor(0)} fontSize={11} />
          </Bar>
          <Bar dataKey="median" name="Reversion ke median 1Y" fill={seriesColor(1)} maxBarSize={40} radius={[2, 2, 0, 0]}>
            <LabelList dataKey="medianLabel" position="top" fill="#666" fontSize={11} />
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
        {data.map((d, i) => (
          <span key={i}>
            {d.name}: {d.delta}
          </span>
        ))}
      </div>
    </div>
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
