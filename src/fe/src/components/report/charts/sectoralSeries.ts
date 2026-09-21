/**
 * Shared Sectoral chart styling for recharts components.
 *
 * Palette order is authoritative: assign series colors in array order
 * (series 1 -> SECTORAL_SERIES[0], series 2 -> SECTORAL_SERIES[1], ...).
 * Styling follows the Sectoral Design System: subtle horizontal grid,
 * no axis/tick lines, 12px #666 ticks, black zero baseline, tooltip shadow.
 */

export const SECTORAL_SERIES: string[] = [
  "#0928B1",
  "#B4C7FF",
  "#3ED628",
  "#1DCD9F",
  "#0047AB",
  "#7596FF",
]

export const SECTORAL_PRIMARY = "#0928B1"
export const SECTORAL_GRID = "#E0E0E0"
export const SECTORAL_ZERO_BASELINE = "#000000"
export const SECTORAL_FONT = "Roboto, sans-serif"

export const SECTORAL_TICK = {
  fontSize: 12,
  fill: "#666",
  fontFamily: SECTORAL_FONT,
}

/** Smaller tick for dense combo charts (6 x-labels in ~300px cards). */
export const SECTORAL_TICK_SM = {
  ...SECTORAL_TICK,
  fontSize: 11,
}

/**
 * Line-series color for bar+line combos. Bars use navy SECTORAL_SERIES[0];
 * the old line color (pale #B4C7FF) was invisible on white, so combos get
 * this dark-green house token instead. Do NOT change SECTORAL_SERIES[1] -
 * PeersCharts uses it for a bar series.
 */
export const SECTORAL_LINE = "#157F3D"

export const SECTORAL_TOOLTIP_STYLE = {
  borderRadius: "4px",
  border: "none",
  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  fontFamily: SECTORAL_FONT,
  fontSize: 12,
}

export const SECTORAL_LEGEND_STYLE = {
  fontSize: "12px",
  fontFamily: SECTORAL_FONT,
}

export function seriesColor(index: number): string {
  return SECTORAL_SERIES[index % SECTORAL_SERIES.length]
}
