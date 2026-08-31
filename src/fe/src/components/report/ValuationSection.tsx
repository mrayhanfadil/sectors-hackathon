import type { ValuationEngineData, ReportArchetype } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calculator, Percent, Layers, TrendingDown, Scale } from "lucide-react"

interface ValuationSectionProps {
  valuation: ValuationEngineData
  archetype: ReportArchetype
  ticker: string
}

export function ValuationSection({ valuation, ticker }: ValuationSectionProps) {
  return (
    <div className="space-y-4">
      {/* Primary Target Price & Blended Weights Banner */}
      <Card className="border-[#2a313e] bg-[#111317]">
        <CardHeader className="pb-2 border-b border-[#1d222c]">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-300">
              <Calculator className="h-4 w-4 text-amber-400" />
              <span>Adaptive Valuation Engine: {ticker} Target Price Derivation</span>
            </CardTitle>
            <Badge variant="amber" className="font-mono">
              PRIMARY TARGET: IDR {valuation.primaryTargetPrice.toLocaleString("id-ID")}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-3">
          {/* Blended Valuation Breakdown Table (Hero for MTEL / Conglomerate) */}
          {valuation.blendedBreakdown && valuation.blendedBreakdown.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-mono text-slate-300 font-semibold mb-1">
                Weighted Blended Methodologies (MTEL Archetype Standard)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-left">
                      <th className="pb-2 font-medium">Methodology</th>
                      <th className="pb-2 font-medium text-right">Fair Value / Share</th>
                      <th className="pb-2 font-medium text-right">Weight (%)</th>
                      <th className="pb-2 font-medium text-right">Weighted Contribution</th>
                      <th className="pb-2 font-medium pl-4">Model Parameters</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1b2029]">
                    {valuation.blendedBreakdown.map((item, i) => (
                      <tr key={i} className="hover:bg-[#161a22]">
                        <td className="py-2.5 font-medium text-slate-100">{item.methodology}</td>
                        <td className="py-2.5 text-right font-mono font-semibold text-amber-300">
                          IDR {item.fairValuePerShare.toLocaleString("id-ID")}
                        </td>
                        <td className="py-2.5 text-right font-mono text-slate-300">{item.weightPct}%</td>
                        <td className="py-2.5 text-right font-mono font-bold text-emerald-400">
                          IDR {item.weightedValue.toLocaleString("id-ID")}
                        </td>
                        <td className="py-2.5 pl-4 text-slate-400 text-[11px] font-sans">{item.note}</td>
                      </tr>
                    ))}
                    <tr className="bg-[#161920] font-bold border-t border-amber-500/30">
                      <td className="py-2.5 text-amber-300 font-mono">BLENDED CONSENSUS FAIR VALUE</td>
                      <td className="py-2.5 text-right font-mono text-amber-300 text-sm">
                        IDR {valuation.primaryTargetPrice.toLocaleString("id-ID")}
                      </td>
                      <td className="py-2.5 text-right font-mono text-slate-200">100%</td>
                      <td className="py-2.5 text-right font-mono text-emerald-400 text-sm">
                        IDR {valuation.primaryTargetPrice.toLocaleString("id-ID")}
                      </td>
                      <td className="py-2.5 pl-4 text-xs font-mono text-emerald-400">
                        Margin of Safety: {valuation.marginOfSafetyPct}%
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SOTP 4 Pillars Breakdown (if CDIA Conglomerate) */}
      {valuation.sotpPillars && valuation.sotpPillars.length > 0 && (
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <Layers className="h-3.5 w-3.5 text-amber-400" />
              <span>Sum-of-the-Parts (SOTP) Segmental NAV Breakdown</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-1">
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-left">
                    <th className="pb-2 font-medium">Business Pillar</th>
                    <th className="pb-2 font-medium">Key Operating Asset</th>
                    <th className="pb-2 font-medium text-right">EBITDA / Base (Bn)</th>
                    <th className="pb-2 font-medium text-right">Target Multiple</th>
                    <th className="pb-2 font-medium text-right">Implied Equity (Bn)</th>
                    <th className="pb-2 font-medium text-right">Per Share (IDR)</th>
                    <th className="pb-2 font-medium text-right">% of NAV</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b2029]">
                  {valuation.sotpPillars.map((s, i) => (
                    <tr key={i} className="hover:bg-[#161a22]">
                      <td className="py-2.5 font-medium text-slate-100">{s.pillar}</td>
                      <td className="py-2.5 text-slate-300">{s.keyAsset}</td>
                      <td className="py-2.5 text-right font-mono text-slate-300">{s.ebitdaOrMetric}</td>
                      <td className="py-2.5 text-right font-mono text-amber-300">{s.targetMultiple}</td>
                      <td className="py-2.5 text-right font-mono text-slate-200">{s.equityValueBn.toLocaleString("id-ID")}</td>
                      <td className="py-2.5 text-right font-mono font-bold text-amber-300">IDR {s.perShareIdr}</td>
                      <td className="py-2.5 text-right font-mono text-slate-400">{s.shareOfNavPct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gordon Growth Model Math (if BBCA Bank) */}
      {valuation.ggmMath && (
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <Scale className="h-3.5 w-3.5 text-amber-400" />
              <span>Gordon Growth Model (GGM) Implied P/BV Mathematics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2 space-y-3">
            <div className="p-3 rounded bg-[#161920] border border-amber-500/30 font-mono text-xs text-amber-300">
              {valuation.ggmMath.formula}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-slate-400 text-[10px]">SUSTAINABLE ROE</div>
                <div className="text-base font-bold text-white mt-0.5">{valuation.ggmMath.roe}%</div>
              </div>
              <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-slate-400 text-[10px]">COST OF EQUITY (CoE)</div>
                <div className="text-base font-bold text-white mt-0.5">{valuation.ggmMath.costOfEquity}%</div>
              </div>
              <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-slate-400 text-[10px]">TERMINAL GROWTH (g)</div>
                <div className="text-base font-bold text-white mt-0.5">{valuation.ggmMath.terminalGrowth}%</div>
              </div>
              <div className="p-2.5 rounded bg-[#161a22] border border-amber-500/40">
                <div className="text-amber-400 text-[10px]">IMPLIED P/BV MULTIPLE</div>
                <div className="text-base font-bold text-amber-300 mt-0.5">{valuation.ggmMath.impliedPbv}x</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Forecast Revision Block (if CDIA) */}
      {valuation.forecastRevision && valuation.forecastRevision.length > 0 && (
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <TrendingDown className="h-3.5 w-3.5 text-red-400" />
              <span>Forecast Revision Matrix (Earnings De-Risking)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-1">
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-left">
                    <th className="pb-2 font-medium">Metric</th>
                    <th className="pb-2 font-medium text-right">Prior Estimate</th>
                    <th className="pb-2 font-medium text-right">Revised Estimate</th>
                    <th className="pb-2 font-medium text-right">Delta (%)</th>
                    <th className="pb-2 font-medium pl-4">Revision Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b2029]">
                  {valuation.forecastRevision.map((r, i) => (
                    <tr key={i} className="hover:bg-[#161a22]">
                      <td className="py-2.5 font-medium text-slate-100">{r.metric}</td>
                      <td className="py-2.5 text-right font-mono text-slate-400">{r.priorForecast}</td>
                      <td className="py-2.5 text-right font-mono font-semibold text-slate-200">{r.revisedForecast}</td>
                      <td className="py-2.5 text-right font-mono font-bold text-red-400">{r.deltaPct}</td>
                      <td className="py-2.5 pl-4 text-slate-400 text-[11px]">{r.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Historical Valuation Bands (MTEL Hero) */}
      {valuation.historicalBands && valuation.historicalBands.length > 0 && (
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
                <Layers className="h-3.5 w-3.5 text-amber-400" />
                <span>3-Year Historical Multiple Bands (Mean Reversion Analysis)</span>
              </CardTitle>
              <Badge variant="amber" className="font-mono text-[10px]">
                STD ±2 BANDS
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {valuation.historicalBands.map((band, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-[#161920] border border-[#222836] space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="font-bold text-slate-100">{band.metricName}</span>
                    <Badge variant={band.label === "BELOW AVG" || band.label === "DEEP VALUE" ? "success" : "secondary"}>
                      {band.label}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-baseline font-mono text-xs">
                    <span className="text-slate-400 text-[11px]">Current Level:</span>
                    <span className="text-base font-bold text-amber-300">{band.current}x</span>
                  </div>
                  {/* Visual Multiple Range Gauge */}
                  <div className="space-y-1 font-mono text-[10px]">
                    <div className="flex justify-between text-slate-500">
                      <span>-2SD ({band.stdMinus2}x)</span>
                      <span>Mean ({band.average}x)</span>
                      <span>+2SD ({band.stdPlus2}x)</span>
                    </div>
                    <div className="relative h-2 w-full rounded-full bg-[#1e2430] overflow-hidden">
                      <div
                        className="absolute h-full bg-emerald-400 rounded-full"
                        style={{
                          left: "0%",
                          width: `${Math.min(100, ((band.current - band.stdMinus2) / (band.stdPlus2 - band.stdMinus2)) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* DCF Cash Flow Schedule & WACC Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* DCF Free Cash Flow Schedule */}
        <Card className="lg:col-span-2 border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <Calculator className="h-3.5 w-3.5 text-amber-400" />
              <span>DCF Free Cash Flow Schedule (IDR Bn)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-1">
            {valuation.dcfSchedule ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-right">
                      <th className="pb-2 text-left font-medium">Period</th>
                      <th className="pb-2 font-medium">Revenue</th>
                      <th className="pb-2 font-medium">EBIT</th>
                      <th className="pb-2 font-medium">NOPAT</th>
                      <th className="pb-2 font-medium">Capex</th>
                      <th className="pb-2 font-medium">FCFF</th>
                      <th className="pb-2 font-medium">PV (IDR)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1b2029] font-mono text-[11px]">
                    {valuation.dcfSchedule.map((row, i) => (
                      <tr key={i} className="hover:bg-[#161a22]">
                        <td className="py-2 text-left font-semibold text-slate-200">{row.period}</td>
                        <td className="py-2 text-right text-slate-300">{row.revenue.toLocaleString("id-ID")}</td>
                        <td className="py-2 text-right text-slate-300">{row.ebit.toLocaleString("id-ID")}</td>
                        <td className="py-2 text-right text-slate-300">{row.nopat.toLocaleString("id-ID")}</td>
                        <td className="py-2 text-right text-red-400">-{row.capex.toLocaleString("id-ID")}</td>
                        <td className="py-2 text-right font-bold text-amber-300">{row.fcff.toLocaleString("id-ID")}</td>
                        <td className="py-2 text-right font-bold text-emerald-400">{row.presentValue.toLocaleString("id-ID")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-xs text-slate-400 py-4 font-mono">
                Standard DCF discounted at WACC {valuation.waccAssumptions.wacc}%.
              </div>
            )}
          </CardContent>
        </Card>

        {/* WACC Assumptions Schedule */}
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <Percent className="h-3.5 w-3.5 text-amber-400" />
              <span>WACC Schedule Assumptions</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2 space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Weighted Avg Cost of Capital (WACC)</span>
              <span className="font-bold text-amber-300">{valuation.waccAssumptions.wacc}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Beta (Adjusted vs IHSG)</span>
              <span className="font-semibold text-slate-200">{valuation.waccAssumptions.beta}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Risk Free Rate (10Y IndoGov)</span>
              <span className="font-semibold text-slate-200">{valuation.waccAssumptions.riskFreeRate}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Equity Risk Premium (ERP)</span>
              <span className="font-semibold text-slate-200">{valuation.waccAssumptions.equityRiskPremium}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Cost of Equity (CoE)</span>
              <span className="font-semibold text-slate-200">{valuation.waccAssumptions.costOfEquity}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Cost of Debt Post-Tax (CoD)</span>
              <span className="font-semibold text-slate-200">{valuation.waccAssumptions.costOfDebtAfterTax}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#1b2029]">
              <span className="text-slate-400">Terminal Growth Rate (g)</span>
              <span className="font-semibold text-emerald-400">{valuation.waccAssumptions.terminalGrowth}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Weight Equity / Debt</span>
              <span className="font-semibold text-slate-300">
                {valuation.waccAssumptions.weightEquity}% / {valuation.waccAssumptions.weightDebt}%
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
