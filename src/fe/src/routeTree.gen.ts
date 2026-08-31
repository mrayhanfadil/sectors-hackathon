import { Route as RootRoute } from "./routes/__root"
import { Route as IndexRoute } from "./routes/index"
import { Route as OutlookRoute } from "./routes/outlook"
import { Route as ChallengeRoute } from "./routes/challenge"
import { Route as SentimentRoute } from "./routes/sentiment"
import { Route as ReportIndexRoute } from "./routes/report.$ticker.index"
import { Route as ReportChallengeRoute } from "./routes/report.$ticker.challenge"
import { Route as ReportSentimentRoute } from "./routes/report.$ticker.sentiment"

// @ts-ignore — TanStack types struggle with file-route union here; runtime is correct
export const routeTree = (RootRoute as any).addChildren([
  IndexRoute as any,
  OutlookRoute as any,
  ChallengeRoute as any,
  SentimentRoute as any,
  ReportIndexRoute as any,
  ReportChallengeRoute as any,
  ReportSentimentRoute as any,
])
