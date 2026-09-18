import React from "react"

export const TOKENS = {
  // Sectoral Design System Tokens
  primary: "#0928B1",
  periwinkle: "#B4C7FF",
  green: "#3ED628",
  teal: "#1DCD9F",
  cobalt: "#0047AB",
  softBlue: "#7596FF",
  ink: "#333333",
  grid: "#D9D9D9",
  caption: "#666666",

  // Legacy compatibility mappings for existing chart components
  navy: "#0928B1",
  tealLight: "#B4C7FF",
  ice: "#D9D9D9",
  icePale: "#FFFFFF",
  rule: "#D9D9D9",
  muted: "#666666",
  buy: "#3ED628",
  sell: "#B4232A",
  hold: "#A16207",
} as const

/**
 * Honest Pending State component rendered when payload section is missing or incomplete.
 * Never invents mock or placeholder figures.
 */
export function PendingBlock({ label, message }: { label: string; message?: string }) {
  return (
    <div className="rounded-xl border border-[#D9D9D9] bg-white px-4 py-8 text-center text-xs text-[#666666] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#f1f5f9]">
      <span className="font-semibold text-[#0928B1] dark:text-[#7596FF]">{label}</span>{" "}
      {message ?? "belum tersedia di payload."}
    </div>
  )
}

/**
 * Format a number using Indonesian separators (dot for thousands, comma for decimals).
 * Returns '-' if value is null or undefined (no substitute zeros).
 */
export function formatIdn(value: number | null | undefined, digits: number = 0): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "-"
  }
  const parts = Math.abs(value).toFixed(digits).split(".")
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".")
  const decPart = parts[1]
  const sign = value < 0 ? "-" : ""
  return decPart !== undefined && digits > 0 ? `${sign}${intPart},${decPart}` : `${sign}${intPart}`
}

/**
 * Format a percentage value (e.g. 15.2 -> "+15,2%" or "-10,0%").
 */
export function formatPct(value: number | null | undefined, digits: number = 1, showSign: boolean = true): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "-"
  }
  const sign = value > 0 && showSign ? "+" : ""
  return `${sign}${formatIdn(value, digits)}%`
}

/**
 * Parse an Indonesian formatted string into a numeric float.
 * Handles "43.036" -> 43036, "141,9" -> 141.9, "(28,8)" -> -28.8, "n/a" -> null.
 * Strictly avoids placeholder defaults.
 */
export function parseIdnNumber(raw: unknown): number | null {
  if (typeof raw === "number") {
    return Number.isFinite(raw) ? raw : null
  }
  if (raw === null || raw === undefined) {
    return null
  }
  const text = String(raw).trim()
  if (text === "" || text === "-" || text === "-" || text.toLowerCase() === "n/a" || text.toLowerCase() === "na") {
    return null
  }
  const isNegative = (text.startsWith("(") && text.endsWith(")")) || text.startsWith("-")
  let clean = text.replace(/[()%]/g, "").replace(/\s+/g, "").replace(/^-/, "")
  if (clean.includes(",")) {
    // Comma as decimal: "141,9" or "43.036,5"
    clean = clean.replace(/\./g, "").replace(",", ".")
  } else if (clean.split(".").length === 2 && clean.split(".")[1].length === 3) {
    // "43.036" is 43036, not 43.036
    clean = clean.replace(/\./g, "")
  }
  const num = parseFloat(clean)
  if (!Number.isFinite(num)) {
    return null
  }
  return isNegative ? -num : num
}
