import type { ComponentType } from "react"
import {
  Database,
  Newspaper,
  MessageSquare,
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
    title: "Pencari Data IDX & Keuangan",
    shortLabel: "Pencari Data",
    stageId: "intake",
    stageIndex: 1,
    icon: Database,
    badgeBg: "bg-sky-50",
    badgeText: "text-sky-800",
    badgeBorder: "border-sky-200",
    dotColor: "bg-sky-500",
    description: "Mengambil data laporan keuangan, neraca, dan rasio historis dari BEI / IDX.",
  },
  news_harvester: {
    key: "news_harvester",
    title: "Pencari Berita & Keterbukaan",
    shortLabel: "Pencari Berita",
    stageId: "intake",
    stageIndex: 1,
    icon: Newspaper,
    badgeBg: "bg-amber-50",
    badgeText: "text-amber-800",
    badgeBorder: "border-amber-200",
    dotColor: "bg-amber-500",
    description: "Mengumpulkan berita ekonomi, keterbukaan informasi, dan aksi korporasi terkini.",
  },
  social_sentiment: {
    key: "social_sentiment",
    title: "Penganalisis Sentimen Komunitas",
    shortLabel: "Sentimen Pasar",
    stageId: "intake",
    stageIndex: 1,
    icon: MessageSquare,
    badgeBg: "bg-violet-50",
    badgeText: "text-violet-800",
    badgeBorder: "border-violet-200",
    dotColor: "bg-violet-500",
    description: "Menganalisis sentimen investor ritel dan percakapan pasar.",
  },
  news_search_sub: {
    key: "news_search_sub",
    title: "Mesin Pencari Berita Pelengkap",
    shortLabel: "Pencari Berita (Sub)",
    stageId: "intake",
    stageIndex: 1,
    icon: Search,
    badgeBg: "bg-amber-50",
    badgeText: "text-amber-700",
    badgeBorder: "border-amber-200",
    dotColor: "bg-amber-400",
    description: "Menelusuri arsip berita dan rilis pers tambahan.",
  },
  social_search_sub: {
    key: "social_search_sub",
    title: "Mesin Pencari Sentimen Pelengkap",
    shortLabel: "Pencari Sentimen (Sub)",
    stageId: "intake",
    stageIndex: 1,
    icon: Search,
    badgeBg: "bg-violet-50",
    badgeText: "text-violet-700",
    badgeBorder: "border-violet-200",
    dotColor: "bg-violet-400",
    description: "Menelusuri percakapan dan sentimen media sosial tambahan.",
  },
  modeler: {
    key: "modeler",
    title: "Ahli Valuasi Keuangan",
    shortLabel: "Ahli Valuasi",
    stageId: "valuation",
    stageIndex: 2,
    icon: Calculator,
    badgeBg: "bg-emerald-50",
    badgeText: "text-emerald-800",
    badgeBorder: "border-emerald-300",
    dotColor: "bg-emerald-600",
    description: "Menghitung nilai wajar saham dengan model matematis DCF, DDM, GGM, dan PE/PBV.",
  },
  analyst: {
    key: "analyst",
    title: "Analis Fundamental & Kinerja",
    shortLabel: "Analis Fundamental",
    stageId: "research",
    stageIndex: 3,
    icon: TrendingUp,
    badgeBg: "bg-neutral-100",
    badgeText: "text-neutral-800",
    badgeBorder: "border-neutral-300",
    dotColor: "bg-neutral-600",
    description: "Menganalisis tren profitabilitas, margin, dan kesehatan neraca perusahaan.",
  },
  industry: {
    key: "industry",
    title: "Analis Sektor & Industri",
    shortLabel: "Analis Industri",
    stageId: "research",
    stageIndex: 3,
    icon: Building2,
    badgeBg: "bg-teal-50",
    badgeText: "text-teal-800",
    badgeBorder: "border-teal-200",
    dotColor: "bg-teal-600",
    description: "Mengevaluasi tren pasar, posisi kompetitif, dan prospek sektor industri.",
  },
  industry_search_sub: {
    key: "industry_search_sub",
    title: "Mesin Riset Industri Pelengkap",
    shortLabel: "Riset Industri (Sub)",
    stageId: "research",
    stageIndex: 3,
    icon: Search,
    badgeBg: "bg-teal-50",
    badgeText: "text-teal-700",
    badgeBorder: "border-teal-200",
    dotColor: "bg-teal-500",
    description: "Menelusuri data riset industri dan persaingan bisnis tambahan.",
  },
  risk: {
    key: "risk",
    title: "Penganalisis Risiko Investasi",
    shortLabel: "Analis Risiko",
    stageId: "research",
    stageIndex: 3,
    icon: ShieldAlert,
    badgeBg: "bg-rose-50",
    badgeText: "text-rose-800",
    badgeBorder: "border-rose-200",
    dotColor: "bg-rose-600",
    description: "Mengidentifikasi risiko regulasi, operasional, makro, dan keuangan.",
  },
  kpi: {
    key: "kpi",
    title: "Analis Indikator Utama (KPI Operasional)",
    shortLabel: "Analis KPI",
    stageId: "research",
    stageIndex: 3,
    icon: Gauge,
    badgeBg: "bg-cyan-50",
    badgeText: "text-cyan-800",
    badgeBorder: "border-cyan-200",
    dotColor: "bg-cyan-600",
    description: "Mengukur metrik operasional khusus seperti rasio tenansi, volume, dan efisiensi.",
  },
  writer: {
    key: "writer",
    title: "Penulis Laporan Riset",
    shortLabel: "Penulis Laporan",
    stageId: "writing",
    stageIndex: 4,
    icon: FileText,
    badgeBg: "bg-indigo-50",
    badgeText: "text-indigo-800",
    badgeBorder: "border-indigo-200",
    dotColor: "bg-indigo-600",
    description: "Merangkum seluruh temuan menjadi tesis investasi yang terstruktur dan lugas.",
  },
  visualizer: {
    key: "visualizer",
    title: "Pembuat Grafik & Visual",
    shortLabel: "Visualisasi Data",
    stageId: "writing",
    stageIndex: 4,
    icon: BarChart3,
    badgeBg: "bg-pink-50",
    badgeText: "text-pink-800",
    badgeBorder: "border-pink-200",
    dotColor: "bg-pink-600",
    description: "Menyusun grafik visual pergerakan harga, margin laba, dan matriks valuasi.",
  },
  sotp: {
    key: "sotp",
    title: "Agregator Valuasi Konglomerasi (SOTP)",
    shortLabel: "Valuasi SOTP",
    stageId: "writing",
    stageIndex: 4,
    icon: PieChart,
    badgeBg: "bg-orange-50",
    badgeText: "text-orange-800",
    badgeBorder: "border-orange-200",
    dotColor: "bg-orange-600",
    description: "Menghitung valuasi terpisah per pilar anak usaha bila perusahaan bertipe konglomerasi.",
  },
  adversarial: {
    key: "adversarial",
    title: "Tim Penguji Kritis (Red Team)",
    shortLabel: "Penguji Kritis",
    stageId: "qa",
    stageIndex: 5,
    icon: Flame,
    badgeBg: "bg-red-50",
    badgeText: "text-red-800",
    badgeBorder: "border-red-200",
    dotColor: "bg-red-600",
    description: "Menguji kelemahan argumen, mempertanyakan asumsi optimis, dan memvalidasi fakta.",
  },
  critic: {
    key: "critic",
    title: "Reviewer QA & Penjamin Kualitas",
    shortLabel: "Reviewer QA",
    stageId: "qa",
    stageIndex: 5,
    icon: ShieldCheck,
    badgeBg: "bg-neutral-900",
    badgeText: "text-white",
    badgeBorder: "border-neutral-900",
    dotColor: "bg-neutral-900",
    description: "Melakukan verifikasi angka matematika, konsistensi data antar tabel, dan rekomendasi akhir.",
  },
  system: {
    key: "system",
    title: "Sistem Eksekusi",
    shortLabel: "Sistem",
    stageId: "system",
    stageIndex: 0,
    icon: Cpu,
    badgeBg: "bg-neutral-100",
    badgeText: "text-neutral-600",
    badgeBorder: "border-neutral-200",
    dotColor: "bg-neutral-400",
    description: "Koordinasi pipeline multi-agen.",
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
    title: "Pengumpulan Data",
    icon: Search,
    primaryAgents: ["collector", "news_harvester", "social_sentiment"],
    allAgents: ["collector", "news_harvester", "social_sentiment", "news_search_sub", "social_search_sub"],
    agentSubtitle: "Pencari Data, Pencari Berita, Sentimen Pasar",
    description: "Menarik data laporan keuangan resmi IDX, berita terkini, dan sentimen publik.",
  },
  {
    id: "valuation",
    stageNumber: 2,
    title: "Valuasi",
    icon: Calculator,
    primaryAgents: ["modeler"],
    allAgents: ["modeler"],
    agentSubtitle: "Ahli Valuasi Keuangan (DCF, DDM, Multiples)",
    description: "Menghitung nilai wajar secara deterministik dengan model DCF, DDM, GGM, dan rasio PE/PBV.",
  },
  {
    id: "research",
    stageNumber: 3,
    title: "Riset",
    icon: FileSearch,
    primaryAgents: ["analyst", "industry", "risk", "kpi"],
    allAgents: ["analyst", "industry", "industry_search_sub", "risk", "kpi"],
    agentSubtitle: "Analis Fundamental, Industri, Risiko, KPI",
    description: "Mengkaji kesehatan neraca, peta persaingan industri, risiko investasi, dan metrik operasional.",
  },
  {
    id: "writing",
    stageNumber: 4,
    title: "Penulisan",
    icon: PenTool,
    primaryAgents: ["writer", "visualizer", "sotp"],
    allAgents: ["writer", "visualizer", "sotp"],
    agentSubtitle: "Penulis Laporan, Visualisasi Data, Valuasi SOTP",
    description: "Menyusun draft laporan riset yang mudah dipahami disertai grafik dan visualisasi.",
  },
  {
    id: "qa",
    stageNumber: 5,
    title: "Penjaminan Kualitas",
    icon: ShieldCheck,
    primaryAgents: ["adversarial", "critic"],
    allAgents: ["adversarial", "critic"],
    agentSubtitle: "Tim Penguji Kritis (Red Team), Reviewer QA",
    description: "Menguji ketahanan argumen, memverifikasi keselarasan data narasi vs tabel, dan memberi verifikasi akhir.",
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
      title: author ? `Agen ${author}` : "Agen AI",
      shortLabel: author || "Agen",
      stageId: "system",
      stageIndex: 0,
      icon: Cpu,
      badgeBg: "bg-neutral-100",
      badgeText: "text-neutral-700",
      badgeBorder: "border-neutral-200",
      dotColor: "bg-neutral-400",
      description: "Memproses langkah analisis.",
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

export function getEventActionDescription(event: TraceEvent, ticker = "BBCA"): string {
  const t = ticker.toUpperCase()

  if (event.function_calls && event.function_calls.length > 0) {
    const firstCall = event.function_calls[0]
    const translated = translateFunctionName(firstCall.name)
    if (event.author === "modeler") {
      return `Sedang ${translated.toLowerCase()} untuk ${t}`
    }
    return `${translated} (${firstCall.name})`
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
    return `Menyimpan data hasil riset ke memori pipeline [${keysStr}]`
  }

  if (event.text) {
    const firstLine = event.text.trim().split("\n")[0]
    if (firstLine.length > 0 && firstLine.length < 120) {
      return firstLine
    }
    return `${firstLine.slice(0, 110)}...`
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
