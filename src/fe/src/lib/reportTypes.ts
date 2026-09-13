import type { ReportPayload } from "./reportPayload"

export type RatingBox = {
  action?: string
  tp?: number
  prev_tp?: number | null
  price?: number
  upside_pct?: number
  key_takeaways?: string[]
}

export type VsJci = {
  ytd_abs?: number | null
  ytd_rel?: number | null
  source?: string
  note?: string
  chart?: {
    labels: string[]
    series: number[][]
  }
}

export type ShareholderItem = {
  name: string
  pct: number
  pct_str?: string
}

export type CoverSlide1 = {
  rating?: {
    action?: string
    action_status?: string
    prev_action?: string | null
    prev_tp?: number | null
  }
  price_box?: {
    rows?: string[][]
    anchor?: string
    anchor_basis?: string
  }
  stats?: {
    rows?: string[][]
    major_shareholders?: ShareholderItem[]
    notes?: string[]
    sources?: Record<string, string>
  }
  analyst?: {
    name: string
    title: string
  }
  theme_title?: string
  highlights?: string[]
  financial_para?: {
    heading: string
    body: string
    source?: string
  }
  jci_chart?: {
    ticker?: string
    labels?: string[]
    price?: number[]
    index?: number[]
    rel_pct?: number[]
    window?: string
    months?: number
    abs_chg_pct?: number
    idx_chg_pct?: number
    source?: string
  }
  fx?: {
    rate?: number
    date?: string
    source?: string
  }
  notes?: string[]
}

export type CoverSlide2 = {
  key_financials?: {
    exhibit_title?: string
    headers?: string[]
    rows?: (string | number)[][]
    path_notes?: string[]
    notes?: string[]
    source?: string
    forecast_basis?: string
    forecast_attribution?: string
    forecast_as_of?: string
    forecast_label?: string
    forecast_problems?: string[]
    raw?: Record<string, unknown>
  }
  katalis?: {
    heading?: string
    body?: string
  }
  valuasi?: {
    heading?: string
    body?: string
  }
}

export type CoverSection = {
  rating_box?: RatingBox
  vs_jci?: VsJci
  shares?: {
    outstanding?: number
    unit?: string
    free_float_pct?: number | null
    note?: string
  }
  shareholders?: ShareholderItem[]
  shareholders_src?: string
  shareholders_note?: string
  esg?: {
    found?: boolean
    score?: number
    scores?: { e: number; s: number; g: number }
    source?: string
    date?: string
    note?: string
  }
  summary?: string
  price_chart?: {
    title?: string
    label?: string
    caption?: string
  }
  market?: {
    market_cap?: string
    index_class?: string
    range_52w?: string
  }
  slide1?: CoverSlide1
  slide2?: CoverSlide2
}

export type MetaSection = {
  template?: string
  reason?: string
  ticker?: string
  company_name?: string
  sector?: string
  report_type?: string
  date?: string
  prepared_by?: string
  language?: string
  subsector?: string
}

export type FinancialHighlights = {
  source?: string
  note?: string
  years?: string[]
  rows?: (string | number)[][]
}

export type ThesisItem = {
  headline: string
  detail: string
  stat?: string
  stat_label?: string
  source?: string
}

export type PerformancePage = {
  title?: string
  subtitle?: string
  quadrants?: {
    title?: string
    window?: string
    bars?: number[]
    line?: (number | null)[]
    labels?: string[]
    actual_n?: number
    bar_unit?: string
    line_unit?: string
    bar_fmt?: string[]
    line_fmt?: string[]
    narrative?: string
    tie_out?: Record<string, unknown>
  }[]
  notes?: string[]
  sources?: string[]
}

export type ValuationPage = {
  available?: boolean
  method?: string
  title?: string
  subtitle?: string
  periods?: string[]
  blocks?: {
    build_up?: Record<string, number[]>
    documented_fcff?: number[]
  }
  bridge?: {
    basis?: string
    fcff?: number[]
    growth?: (number | null)[]
    discount?: number[]
    pv_fcff?: number[]
    tv_gordon?: number
    tv_gordon_df?: number
    pv_tv_gordon?: number
    tv_exit?: number
    pv_tv_exit?: number
    pv_explicit?: number
    ev_gordon?: number
    ev_exit?: number
    equity_gordon?: number
    pv_explicit_abs?: number
    equity_exit?: number
    fv_gordon?: number
    fv_exit?: number
    tv_share?: number
    net_debt?: number
    implied_exit_multiple?: number
    flags?: string[]
  }
  wacc_rows?: [string, string, string][]
  sensitivity?: {
    fair_value?: unknown
    wacc_axis?: number[]
    g_axis?: number[]
    base?: [number, number]
    base_fv?: number
    swing?: {
      min?: number
      max?: number
      median?: number
    }
    stats?: {
      min?: number
      max?: number
      median?: number
      n_valid?: number
      n_cells?: number
    }
    columns?: string[]
    rows?: {
      label: string
      cells: {
        value: string | number
        band?: string
        base?: boolean
      }[]
    }[]
    base_wacc?: string
    base_g?: string
  }
  bridge_basis?: string
  drivers?: {
    revenue_fy25?: number
    ebit_margin_fy25?: number
    effective_tax?: number
    da_fy25?: number
    capex_sustaining?: number
    multiple?: number
    price?: number
    revenue_basis?: string
  }
  notes?: string[]
  convention?: string
  block1_headers?: string[] | null
  block2_headers?: string[] | null
  block3_headers?: string[] | null
  block1_rows?: [string, (string | number)[]][]
  block2_rows?: [string, string | number, string | number][]
  block3_rows?: [string, string | number, string | number][]
  crosscheck_rows?: [string, string | number, string][]
  narrative?: string[]
  sources?: string[]
  missing?: string[]
  exhibit8_title?: string
  legs?: {
    dcf?: number
    ev_ebitda?: number
  }
}

export type PeerRow = {
  symbol: string
  name: string
  pe?: number | null
  pe_nm?: boolean
  pbv?: number | null
  ev_ebitda?: number | null
  ev_ebitda_nm?: boolean
  roe?: number | null
  market_cap?: number | null
  is_covered?: boolean
  is_stat?: boolean
}

export type PeerStat = {
  symbol?: string
  pe?: number
  pbv?: number
  ev_ebitda?: number
  roe?: number
  is_stat?: boolean
}

export type PeersPagePartA = {
  exhibit?: number
  title?: string
  columns?: string[]
  rows?: PeerRow[]
  median?: PeerStat
  average?: PeerStat
  counts?: {
    pe_ttm?: number
    pb_mrq?: number
    ev_ebitda_ttm?: number
    roe_ttm?: number
  }
  basis?: string
  as_of?: string
  criteria?: string
  narrative?: string[]
  narrative_text?: string
  sources?: string[]
  credit_log?: string
}

export type PeersPagePartB = {
  exhibits?: number[]
  title?: string
  methodology?: string
  bands?: {
    key: string
    label: string
    narrative: string
    sources?: string[]
    [k: string]: unknown
  }[]
  implied?: {
    label: string
    to_mean: number
    to_median: number
    low?: number
    high?: number
    is_range?: boolean
    delta_pct?: number
  }[]
  driver?: {
    as_of?: string
    earnings_ttm?: number
    ebitda_ttm?: number
    revenue_ttm?: number
    equity?: number
    net_debt?: number
  }
  driver_note?: string
  last_close?: number
  disclaimer?: string
  sources?: string[]
  credit_log?: string
}

export type PeersPage = {
  available?: boolean
  ticker?: string
  as_of?: string
  part_a?: PeersPagePartA
  part_b?: PeersPagePartB
  sections?: {
    a?: string
    b?: string
  }
}

export type StatementRow = {
  label: string
  cells: (number | string | null)[]
  kind?: "section" | "subtotal" | "highlight" | "deduction" | "na" | string
  note?: string
}

export type StatementsPage = {
  available?: boolean
  ticker?: string
  years?: string[]
  variant?: string
  income?: {
    exhibit_key?: string
    title?: string
    headers?: string[]
    rows?: StatementRow[]
  }
  balance?: {
    exhibit_key?: string
    title?: string
    headers?: string[]
    rows?: StatementRow[]
    /** provenance the payload prints under the block (declared because the payload carries it) */
    source?: string
  }
  tie_out?: Record<string, number>
  tied?: boolean
  notes?: string[]
  driver_basis?: {
    interest_expense?: string
    capex?: string
  }
  forecast_source?: string
  forecast_source_display?: string
  sources?: string[]
  bank_variant_note?: string
}

export type CashflowPage = {
  available?: boolean
  ticker?: string
  years?: string[]
  sections?: {
    title: string
    rows: StatementRow[]
  }[]
  closing?: StatementRow[]
  memo?: StatementRow[]
  headers?: string[]
  end_cash?: number[]
  net_change?: number[]
  fcf?: number[]
  fcff_exhibit8?: number
  notes?: string[]
  sources?: string[]
}

export type KeyRatioPage = {
  available?: boolean
  ticker?: string
  years?: string[]
  headers?: string[]
  exhibit_title?: string
  sections?: {
    title: string
    rows: StatementRow[]
  }[]
  notes?: string[]
  sources?: string[]
  growth_basis?: {
    sales?: number
    ebitda?: number
    operating?: number
    net?: number
  }
}

export type RiskItem = {
  bucket: string
  detail: string
  source?: string
  stat?: string
  stat_label?: string
  severity?: string | number
}

export type ExhibitItem = {
  title: string
  chart?: {
    type?: string
    data?: Record<string, unknown>
  }
  source?: string
}

export type SectorData = {
  subsector?: string
  growth_forecast_2026?: {
    revenue_pct?: number
    eps_pct?: number
    base_year?: number
  }
  growth_actual_2025?: {
    revenue_pct?: number
    eps_pct?: number
  }
  top_mcap?: {
    symbol: string
    name: string
    market_cap: number
  }[]
  source?: string
}

export type IndustryPage = {
  title?: string
  subtitle?: string
  paragraphs?: {
    heading: string
    body: string
    basis?: string
  }[]
  sources?: string[]
  notes?: string[]
}

export type FullReportPayload = ReportPayload & {
  meta?: MetaSection
  cover?: CoverSection
  financial_highlights?: FinancialHighlights
  industry_page?: IndustryPage
  thesis?: ThesisItem[]
  performance_page?: PerformancePage
  valuation_page?: ValuationPage
  peers_page?: PeersPage
  statements_page?: StatementsPage
  cashflow_page?: CashflowPage
  key_ratio_page?: KeyRatioPage
  risks?: RiskItem[]
  risks_note?: string
  exhibits?: ExhibitItem[]
  sector_data?: SectorData
  key_financials?: {
    title?: string
    source?: string
    headers?: string[]
    rows?: (string | number)[][]
  }
  financial_statements?: {
    section_title?: string
    section_sub?: string
    income?: {
      title?: string
      headers?: string[]
      rows?: (string | number)[][]
      source?: string
    }
    balance?: {
      title?: string
      headers?: string[]
      rows?: (string | number)[][]
      source?: string
    }
    cashflow?: {
      title?: string
      headers?: string[]
      rows?: (string | number)[][]
      bold_rows?: number[]
      footers?: (string | number)[][]
      source?: string
    }
    ratios?: {
      title?: string
      headers?: string[]
      rows?: (string | number)[][]
      source?: string
    }
  }
  financials?: {
    title?: string
    headers?: string[]
    rows?: (string | number)[][]
    source?: string
  }[]
  kpis?: {
    name: string
    value: number
    prev?: number
    unit?: string
    formula?: string
    source?: string
  }[]
  kpis_src?: string
  kpis_note?: string
}

export type ReportPayloadEnvelope = {
  ticker: string
  payload: FullReportPayload | null
  sections?: string[]
  is422?: boolean
  missing?: string[]
  summary?: string
  offline?: boolean
}
