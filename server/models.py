from pydantic import BaseModel, Field
from typing import Optional, Any, Literal


class HealthResponse(BaseModel):
    status: str
    uptime_s: float
    stockdata: dict
    cache: dict
    version: str = "t04-0.1.0"


class ValuationAssumptions(BaseModel):
    wacc: float = Field(examples=[0.084])
    beta: float = Field(examples=[0.7])
    rf: float = Field(examples=[0.0696])
    erp: float = Field(examples=[0.0689])
    coe: float = Field(examples=[0.10])
    cod: float = Field(examples=[0.035])
    g: float = Field(examples=[0.05])
    payout: float = Field(default=0.4)
    source: str = "sectors|assumptions/{ticker}.json"


class ValuationResult(BaseModel):
    method: str
    fair_value: float
    currency: str = "IDR"
    assumptions: ValuationAssumptions
    provenance: str


class ReportResponse(BaseModel):
    ticker: str
    template: Literal["single", "sotp", "infra", "strategy"]
    price: Optional[float] = None
    fair_value: Optional[float] = None
    upside_pct: Optional[float] = None
    rating: str = "HOLD"
    valuation: Optional[ValuationResult] = None
    thesis: Optional[str] = None
    risks: list[str] = []
    segments: Optional[Any] = None
    kpi: Optional[Any] = None
    source: str
    cached: bool = False
    generated_at: str


class NewsItem(BaseModel):
    url: str
    date: str
    title: str
    source: str
    snippet: str
    tier: Literal["T1", "T2", "T3"] = "T2"
    relevance: float = 0.8


class NewsResponse(BaseModel):
    ticker: Optional[str] = None
    items: list[NewsItem]
    cached: bool = False


class SentimentItem(BaseModel):
    platform: str
    url: str
    date: str
    text: str
    sentiment: Literal["bull", "bear", "neutral"]
    score: int = Field(ge=0, le=100)
    relevance: float = 0.8


class SentimentResponse(BaseModel):
    ticker: str
    gauge: int = Field(ge=0, le=100, description="0 bear -> 100 bull")
    confidence: float = 0.6
    top_narratives: list[str] = []
    timeline: list[dict] = []
    items: list[SentimentItem] = []
    disclaimer: str = "sentiment != advice — retail narrative tracker only"
    cached: bool = False


class ChallengeRequest(BaseModel):
    ticker: str = Field(examples=["RATU"])
    claim: str = Field(examples=["WACC 8.4% too low vs MTEL 10.1%?"])
    context: Optional[str] = None


class ChallengeResponse(BaseModel):
    verdict: Literal["defend", "concede"]
    evidence: str
    exhibit_ref: Optional[str] = None
    correction: Optional[dict] = None
    debate_id: str
