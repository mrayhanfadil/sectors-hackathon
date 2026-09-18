import type { ComponentType } from "react"
import {
  Database,
  Newspaper,
  Search,
  Calculator,
  TrendingUp,
  Building2,
  ShieldAlert,
  Gauge,
  FileText,
  BarChart3,
  PieChart,
  Flame,
  ShieldCheck,
  Cpu,
  PenTool,
  FileSearch,
} from "lucide-react"

export interface TraceEvent {
  seq: number
  ts: number
  author: string
  node: string
  branch?: string | null
  event_type: string
  text: string
  function_calls: { name: string; args: Record<string, unknown>; id: string }[]
  function_responses: { name: string; response: unknown; id: string }[]
  state_delta_keys: string[]
  state_delta?: Record<string, unknown> | null
  transfer_to?: string | null
}

export interface AgentFriendlyMeta {
  key: string
  title: string
  shortLabel: string
  stageId: "intake" | "valuation" | "research" | "writing" | "qa" | "system"
  stageIndex: number
  icon: ComponentType<{ className?: string }>
  badgeBg: string
  badgeText: string
  badgeBorder: string
  dotColor: string
  description: string
}

export const AGENT_FRIENDLY_MAP: Record<string, AgentFriendlyMeta> = {
  collector: {
    key: "collector",
    title: "Pencari data IDX & keuangan",
    shortLabel: "Pencari data",
    stageId: "intake",
    stageIndex: 1,
    icon: Database,
    badgeBg: "bg-sky-50 dark:bg-sky-950/40",
    badgeText: "text-sky-800 dark:text-sky-300",
    badgeBorder: "border-sky-200 dark:border-sky-800/60",
    dotColor: "bg-sky-500",
    description: "Mengambil data laporan keuangan, neraca, dan rasio historis dari BEI / IDX.",
  },
  news_harvester: {
    key: "news_harvester",
    title: "Pencari berita & keterbukaan",
    shortLabel: "Pencari berita",
    stageId: "intake",
    stageIndex: 1,
    icon: Newspaper,
    badgeBg: "bg-amber-50 dark:bg-amber-950/40",
    badgeText: "text-amber-800 dark:text-amber-300",
    badgeBorder: "border-amber-200 dark:border-amber-800/60",
    dotColor: "bg-amber-500",
    description: "Mengumpulkan berita ekonomi, keterbukaan informasi, dan aksi korporasi terkini.",
  },
  news_search_sub: {
    key: "news_search_sub",
    title: "Mesin pencari berita pelengkap",
    shortLabel: "Pencari berita (sub)",
    stageId: "intake",
    stageIndex: 1,
    icon: Search,
    badgeBg: "bg-amber-50 dark:bg-amber-950/40",
    badgeText: "text-amber-700 dark:text-amber-300",
    badgeBorder: "border-amber-200 dark:border-amber-800/60",
    dotColor: "bg-amber-400",
    description: "Menelusuri arsip berita dan rilis pers tambahan.",
  },
  modeler: {
    key: "modeler",
    title: "Ahli valuasi keuangan",
    shortLabel: "Ahli valuasi",
    stageId: "valuation",
    stageIndex: 2,
    icon: Calculator,
    badgeBg: "bg-emerald-50 dark:bg-emerald-950/40",
    badgeText: "text-emerald-800 dark:text-emerald-300",
    badgeBorder: "border-emerald-200 dark:border-emerald-800/60",
    dotColor: "bg-emerald-600",
    description: "Menghitung nilai wajar saham dengan model matematis DCF, DDM, GGM, dan kelipatan PE/PBV.",
  },
  analyst: {
    key: "analyst",
    title: "Analis fundamental & kinerja",
    shortLabel: "Analis fundamental",
    stageId: "research",
    stageIndex: 3,
    icon: TrendingUp,
    badgeBg: "bg-[#B4C7FF] dark:bg-[#1e2229]",
    badgeText: "text-[#333333] dark:text-[#f1f5f9]",
    badgeBorder: "border-[#D9D9D9] dark:border-[#262930]",
    dotColor: "bg-stone-600",
    description: "Menganalisis tren profitabilitas, margin laba, dan kesehatan neraca perusahaan.",
  },
  industry: {
    key: "industry",
    title: "Analis sektor & industri",
    shortLabel: "Analis industri",
    stageId: "research",
    stageIndex: 3,
    icon: Building2,
    badgeBg: "bg-teal-50 dark:bg-teal-950/40",
    badgeText: "text-teal-800 dark:text-teal-300",
    badgeBorder: "border-teal-200 dark:border-teal-800/60",
    dotColor: "bg-teal-600",
    description: "Mengevaluasi tren pasar, posisi kompetitif, dan prospek sektor industri.",
  },
  industry_search_sub: {
    key: "industry_search_sub",
    title: "Mesin riset industri pelengkap",
    shortLabel: "Riset industri (sub)",
    stageId: "research",
    stageIndex: 3,
    icon: Search,
    badgeBg: "bg-teal-50 dark:bg-teal-950/40",
    badgeText: "text-teal-700 dark:text-teal-300",
    badgeBorder: "border-teal-200 dark:border-teal-800/60",
    dotColor: "bg-teal-500",
    description: "Menelusuri data riset industri dan persaingan bisnis tambahan.",
  },
  risk: {
    key: "risk",
    title: "Penganalisis risiko investasi",
    shortLabel: "Analis risiko",
    stageId: "research",
    stageIndex: 3,
    icon: ShieldAlert,
    badgeBg: "bg-rose-50 dark:bg-rose-950/40",
    badgeText: "text-rose-800 dark:text-rose-300",
    badgeBorder: "border-rose-200 dark:border-rose-800/60",
    dotColor: "bg-rose-600",
    description: "Mengidentifikasi risiko regulasi, operasional, makroekonomi, dan keuangan.",
  },
  kpi: {
    key: "kpi",
    title: "Analis indikator utama (KPI operasional)",
    shortLabel: "Analis KPI",
    stageId: "research",
    stageIndex: 3,
    icon: Gauge,
    badgeBg: "bg-cyan-50 dark:bg-cyan-950/40",
    badgeText: "text-cyan-800 dark:text-cyan-300",
    badgeBorder: "border-cyan-200 dark:border-cyan-800/60",
    dotColor: "bg-cyan-600",
    description: "Mengukur metrik operasional khusus seperti rasio tenansi, volume, dan efisiensi aset.",
  },
  writer: {
    key: "writer",
    title: "Penulis laporan riset",
    shortLabel: "Penulis laporan",
    stageId: "writing",
    stageIndex: 4,
    icon: FileText,
    badgeBg: "bg-indigo-50 dark:bg-indigo-950/40",
    badgeText: "text-indigo-800 dark:text-indigo-300",
    badgeBorder: "border-indigo-200 dark:border-indigo-800/60",
    dotColor: "bg-indigo-600",
    description: "Merangkum seluruh temuan menjadi tesis investasi yang terstruktur dan lugas.",
  },
  visualizer: {
    key: "visualizer",
    title: "Pembuat grafik & visual",
    shortLabel: "Visualisasi data",
    stageId: "writing",
    stageIndex: 4,
    icon: BarChart3,
    badgeBg: "bg-pink-50 dark:bg-pink-950/40",
    badgeText: "text-pink-800 dark:text-pink-300",
    badgeBorder: "border-pink-200 dark:border-pink-800/60",
    dotColor: "bg-pink-600",
    description: "Menyusun grafik visual pergerakan harga, margin laba, dan matriks valuasi.",
  },
  sotp: {
    key: "sotp",
    title: "Agregator valuasi konglomerasi (SOTP)",
    shortLabel: "Valuasi SOTP",
    stageId: "writing",
    stageIndex: 4,
    icon: PieChart,
    badgeBg: "bg-orange-50 dark:bg-orange-950/40",
    badgeText: "text-orange-800 dark:text-orange-300",
    badgeBorder: "border-orange-200 dark:border-orange-800/60",
    dotColor: "bg-orange-600",
    description: "Menghitung valuasi terpisah per pilar anak usaha bila perusahaan bertipe konglomerasi.",
  },
  adversarial: {
    key: "adversarial",
    title: "Tim penguji kritis (Red Team)",
    shortLabel: "Penguji kritis",
    stageId: "qa",
    stageIndex: 5,
    icon: Flame,
    badgeBg: "bg-red-50 dark:bg-red-950/40",
    badgeText: "text-red-800 dark:text-red-300",
    badgeBorder: "border-red-200 dark:border-red-800/60",
    dotColor: "bg-red-600",
    description: "Menguji kelemahan argumen, mempertanyakan asumsi optimis, dan memvalidasi fakta riset.",
  },
  critic: {
    key: "critic",
    title: "Peninjau mutu & QA",
    shortLabel: "Peninjau mutu",
    stageId: "qa",
    stageIndex: 5,
    icon: ShieldCheck,
    badgeBg: "bg-[#0928B1]/10 dark:bg-[#7596FF]/15",
    badgeText: "text-[#0928B1] dark:text-[#7596FF]",
    badgeBorder: "border-[#0928B1]/25 dark:border-[#7596FF]/30",
    dotColor: "bg-[#0928B1]",
    description: "Melakukan verifikasi angka matematika, konsistensi data antar tabel, dan rekomendasi akhir.",
  },
  system: {
    key: "system",
    title: "Sistem orkestrator",
    shortLabel: "Sistem",
    stageId: "system",
    stageIndex: 0,
    icon: Cpu,
    badgeBg: "bg-[#B4C7FF] dark:bg-[#1e2229]",
    badgeText: "text-[#666666] dark:text-[#666666]",
    badgeBorder: "border-[#D9D9D9] dark:border-[#262930]",
    dotColor: "bg-[#666666]",
    description: "Koordinasi pipeline alur kerja mesin analisis.",
  },
}

export interface PipelineStageConfig {
  id: "intake" | "valuation" | "research" | "writing" | "qa"
  stageNumber: number
  title: string
  icon: ComponentType<{ className?: string }>
  primaryAgents: string[]
  allAgents: string[]
  agentSubtitle: string
  description: string
}

export const PIPELINE_STAGES: PipelineStageConfig[] = [
  {
    id: "intake",
    stageNumber: 1,
    title: "Pengumpulan data",
    icon: Search,
    primaryAgents: ["collector", "news_harvester"],
    allAgents: ["collector", "news_harvester", "news_search_sub"],
    agentSubtitle: "Pencari data, pencari berita",
    description: "Menarik data laporan keuangan resmi IDX dan keterbukaan informasi terkini.",
  },
  {
    id: "valuation",
    stageNumber: 2,
    title: "Valuasi nilai wajar",
    icon: Calculator,
    primaryAgents: ["modeler"],
    allAgents: ["modeler"],
    agentSubtitle: "Ahli valuasi keuangan (DCF, DDM, kelipatan PE/PBV)",
    description: "Menghitung nilai wajar secara deterministik dengan model DCF, DDM, GGM, dan rasio PE/PBV.",
  },
  {
    id: "research",
    stageNumber: 3,
    title: "Riset fundamental",
    icon: FileSearch,
    primaryAgents: ["analyst", "industry", "risk", "kpi"],
    allAgents: ["analyst", "industry", "industry_search_sub", "risk", "kpi"],
    agentSubtitle: "Analis fundamental, industri, risiko, dan KPI",
    description: "Mengkaji kesehatan neraca, peta persaingan industri, profil risiko, dan indikator operasional.",
  },
  {
    id: "writing",
    stageNumber: 4,
    title: "Penulisan laporan",
    icon: PenTool,
    primaryAgents: ["writer", "visualizer", "sotp"],
    allAgents: ["writer", "visualizer", "sotp"],
    agentSubtitle: "Penulis laporan, visualisasi data, valuasi SOTP",
    description: "Menyusun draf laporan riset yang mudah dipahami disertai grafik dan visualisasi pendukung.",
  },
  {
    id: "qa",
    stageNumber: 5,
    title: "Penjaminan mutu",
    icon: ShieldCheck,
    primaryAgents: ["adversarial", "critic"],
    allAgents: ["adversarial", "critic"],
    agentSubtitle: "Tim penguji kritis (Red Team), peninjau mutu QA",
    description: "Menguji ketahanan argumen, memverifikasi keselarasan narasi vs tabel, dan memberi verifikasi akhir.",
  },
]

const FUNCTION_TRANSLATIONS: Record<string, string> = {
  calc_wacc: "Menghitung biaya modal rata-rata tertimbang (WACC)",
  calc_dcf: "Menghitung nilai wajar arus kas terdiskonto (DCF)",
  calc_ddm: "Menghitung nilai wajar model diskonto dividen (DDM)",
  calc_ggm: "Menghitung nilai wajar model pertumbuhan dividen Gordon (GGM)",
  calc_multiples: "Menghitung valuasi perbandingan rasio PE dan PBV saham sejenis",
  calc_sotp: "Menghitung valuasi gabungan pilar bisnis (Sum-of-the-Parts)",
  calc_blended: "Menggabungkan bobot metode valuasi menjadi satu target harga",
  calc_historical_bands: "Menganalisis deviasi pita valuasi historis 3 tahun",
  calc_ratios: "Menghitung rasio profitabilitas, likuiditas, dan solvabilitas",
  web_search: "Mencari informasi dan berita terbaru dari internet",
  fetch_financials: "Mengambil data laporan keuangan resmi dari IDX",
  fetch_id: "Mengambil data profil dan keuangan resmi dari IDX",
  exit_loop: "Menyelesaikan siklus pengujian kritis",
}

export function getFriendlyAgent(author: string): AgentFriendlyMeta {
  return (
    AGENT_FRIENDLY_MAP[author] || {
      key: author || "unknown",
      title: author ? `Agen ${author}` : "Agen cerdas",
      shortLabel: author || "Agen",
      stageId: "system",
      stageIndex: 0,
      icon: Cpu,
      badgeBg: "bg-[#B4C7FF] dark:bg-[#1e2229]",
      badgeText: "text-[#666666] dark:text-[#666666]",
      badgeBorder: "border-[#D9D9D9] dark:border-[#262930]",
      dotColor: "bg-[#666666]",
      description: "Memproses langkah analisis dalam alur kerja.",
    }
  )
}

export function translateFunctionName(funcName: string): string {
  if (FUNCTION_TRANSLATIONS[funcName]) {
    return FUNCTION_TRANSLATIONS[funcName]
  }
  const clean = funcName.replace(/^calc_/, "Hitung ").replace(/_/g, " ")
  return `Menjalankan kalkulasi: ${clean}`
}

export function getEventActionDescription(event: TraceEvent, ticker = ""): string {
  const t = ticker ? ticker.toUpperCase() : "emiten"

  if (event.function_calls && event.function_calls.length > 0) {
    const firstCall = event.function_calls[0]
    const translated = translateFunctionName(firstCall.name)
    if (event.author === "modeler") {
      return `Sedang ${translated.toLowerCase()} untuk ${t}`
    }
    return `${translated}`
  }

  if (event.function_responses && event.function_responses.length > 0) {
    const firstResp = event.function_responses[0]
    const translated = translateFunctionName(firstResp.name)
    return `Hasil perhitungan selesai: ${translated}`
  }

  if (event.transfer_to) {
    const nextAgent = getFriendlyAgent(event.transfer_to)
    return `Menyerahkan kelanjutan riset ke ${nextAgent.title}`
  }

  if (event.state_delta_keys && event.state_delta_keys.length > 0) {
    const keysStr = event.state_delta_keys.join(", ")
    return `Menyimpan data hasil riset (${keysStr})`
  }

  if (event.text) {
    const firstLine = event.text.trim().split("\n")[0]
    if (firstLine.length > 0 && firstLine.length < 120) {
      return firstLine
    }
    return `${firstLine.slice(0, 110)}…`
  }

  if (event.event_type === "start") {
    return `Memulai rangkaian analisis multi-agen untuk saham ${t}`
  }

  if (event.event_type === "done") {
    return `Seluruh tahap analisis untuk saham ${t} berhasil diselesaikan`
  }

  return `Memproses tahap analisis oleh ${getFriendlyAgent(event.author).shortLabel}`
}

export function formatDurationMs(ms: number | undefined | null): string {
  if (ms === undefined || ms === null || isNaN(ms)) return ""
  if (ms < 1000) {
    return `${ms} ms`
  }
  const sec = (ms / 1000).toFixed(1)
  return `${sec} detik`
}

export function formatTimestamp(ts: number): string {
  if (!ts) return ""
  try {
    const d = new Date(ts * 1000)
    return d.toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
  } catch {
    return ""
  }
}
