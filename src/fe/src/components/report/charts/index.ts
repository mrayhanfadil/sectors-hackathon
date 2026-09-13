// The chart surface of the report page. Lane B owns this file: the signatures below are frozen because the page
// shell imports them, and the bodies are replaced with charts wired to the payload.
//
// No component may invent a value. When the section it binds to is absent from the payload it renders the pending
// state, and it never substitutes a zero, a fixture, or a mock series.

import type { ReportPayload } from "@/lib/reportPayload"
import { PerformanceQuadrants } from "./PerformanceQuadrants"
import { DcfSpreadCharts } from "./DcfSpreadCharts"
import { PeersCharts } from "./PeersCharts"

export type ChartProps = { payload: ReportPayload }

export { PerformanceQuadrants, DcfSpreadCharts, PeersCharts }
