import React from "react"

export const TOKENS = {
  navy: "#1C1B17",
  teal: "#0E6E63",
  tealLight: "#4FD1B5",
  ice: "#CBD5E1",
  icePale: "#F4F1EA",
  rule: "#E7E3DA",
  muted: "#6B6659",
  buy: "#157F3D",
  sell: "#B4232A",
  hold: "#A16207",
} as const

/**
 * Honest Pending State component rendered when payload section is missing or incomplete.
 * Never invents mock or placeholder figures.
 */
export function PendingBlock({ label, message }: { label: string; message?: string }) {
  return (
    <div className="rounded-xl border border-[#E7E3DA] bg-white px-4 py-8 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
      <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">{label}</span>{" "}
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
