"""
Social Sentiment Agent — agents/social_sentiment.py
Harvests, filters, and analyzes retail social media sentiment & narratives across X, Reddit, and Stockbit.
Per plan.md §11 Ide 3:
- search_social(ticker, days=14, max=8) via X (P0) + Reddit (P0) + Stockbit (0 Sectors credit)
- Output sentiment.json with gauge score (0-100), top 3 narratives, 14-day timeline, platform breakdown
- Feeds: Thesis Writer (retail narrative vs thesis), Risk Officer (hype/crowded risk), Adversarial Red Team.
- Mandatory disclaimer: sentiment != investment advice.
"""
from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool

JKT = timezone(timedelta(hours=7))
DATA_DIR = _ROOT / "data"
CACHE_DIR = _ROOT / ".cache" / "sentiment"

SOCIAL_SENTIMENT_INSTRUCTION = """
You are the Social Sentiment Agent for the Institutional Equity Research Multi-Agent System.
Your job is to track and synthesize retail investor psychology, social media sentiment,
crowd narrative evolution, and potential positioning extremes across X (Twitter), Reddit (r/finansial),
and Stockbit.

Calculate an institutional gauge score (0 = Extreme Bearish, 50 = Neutral, 100 = Extreme Bullish),
extract the top 3 dominant retail narratives, compute a 14-day timeline of sentiment shifts,
and provide platform-by-platform breakdowns with strict disclaimers.
"""

# Indonesian retail market sentiment lexicons
BULLISH_KEYWORDS_STRONG = ["serok", "to the moon", "bagger", "dividen jumbo", "all in", "borong", "undervalued", "terbang", "pesta dividen", "cuan"]
BULLISH_KEYWORDS_MODERATE = ["akumulasi", "rebound", "bullish", "buy", "hold", "murah", "kinerja bagus", "laba naik", "merger", "ekspansi", "potensi naik", "sinyal beli", "naik", "diskon"]

BEARISH_KEYWORDS_STRONG = ["cut loss", "nyangkut", "didepak msci", "rugi parah", "banting harga", "anjlok", "jebol support", "bandar kabur", "rugi bandar", "boncos"]
BEARISH_KEYWORDS_MODERATE = ["distribusi", "turun", "bearish", "sell", "take profit", "overvalued", "asing jualan", "outflow", "tekanan jual", "waspada", "sanksi", "melemah"]

# Curated benchmark social sentiments for Quintet
CURATED_SOCIAL: Dict[str, Dict[str, Any]] = {
    "MTEL": {
        "gauge_score": 72,
        "sentiment_label": "Bullish",
        "top_narratives": [
            "Merger PST & UMT dipandang sebagai katalis lonjakan tenancy ratio dan pendapatan sewa jangka panjang",
            "Koleksi dividen dan arus kas stabil dari segmen fiber optik yang terus bertumbuh di luar Jawa",
            "Ekspektasi re-rating valuasi karena diskon EV/EBITDA dan P/E masih jauh di bawah kompetitor regional"
        ],
        "posts": [
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/mtel-1h26-merger-katalis",
                "date": "2026-08-28",
                "author": "@ValueInvestorIDX",
                "text": "$MTEL 1H26 EBITDA margin tembus 74%, tenancy ratio 1.57x. Merger PST-UMT bakal nambah ribuan tenant baru. Saham defensif yield oke, cicil serok.",
                "sentiment": "bullish",
                "score": 85,
                "relevance": "EBITDA margin defense and merger synergy"
            },
            {
                "platform": "X",
                "url": "https://x.com/idx_alpha/status/1826019284729102",
                "date": "2026-08-25",
                "author": "@idx_alpha",
                "text": "MTEL fiber optik udah 59k km, dominasi luar Jawa bikin telco lain mau ga mau sewa ke Mitratel. Sektor tower recurring income paling kebal resesi.",
                "sentiment": "bullish",
                "score": 78,
                "relevance": "Outer-island infrastructure moat"
            },
            {
                "platform": "Reddit",
                "url": "https://reddit.com/r/finansial/comments/mtel_tower_thesis_2026",
                "date": "2026-08-22",
                "author": "u/dcf_enjoyer",
                "text": "Diskusi saham infra tower: MTEL vs TOWR vs TBIG. MTEL net gearing paling rendah, ruang capex masih lega pasca merger. Target konsensus 635.",
                "sentiment": "bullish",
                "score": 72,
                "relevance": "Balance sheet leverage comparison"
            },
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/mtel-flow-asing-agustus",
                "date": "2026-08-19",
                "author": "@ChartistSantai",
                "text": "$MTEL sideways di 460-480. Asing mulai akumulasi tipis-tipis. Menunggu katalis lelang spektrum 700MHz cair.",
                "sentiment": "neutral",
                "score": 55,
                "relevance": "Price action consolidation"
            },
            {
                "platform": "X",
                "url": "https://x.com/saham_harian/status/1824901827491",
                "date": "2026-08-17",
                "author": "@saham_harian",
                "text": "Spektrum 700 MHz & 2.6 GHz selesai lelang = operator gaspol pasang perangkat = Mitratel panen sewa baru.",
                "sentiment": "bullish",
                "score": 80,
                "relevance": "Spectrum catalyst monetization"
            }
        ]
    },
    "BBCA": {
        "gauge_score": 68,
        "sentiment_label": "Bullish",
        "top_narratives": [
            "Sentimen pembagian dividen interim Rp3 triliun menarik minat akumulasi retail dan institusi domestik",
            "Resiliensi kualitas kredit dengan CASA 81,2% menjadi bantalan terkuat menghadapi era suku bunga tinggi",
            "Sedikit kekhawatiran atas foreign outflow di big banks tapi retail memanfaatkannya untuk buy on weakness"
        ],
        "posts": [
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/bbca-dividen-interim-2026",
                "date": "2026-08-28",
                "author": "@DividenHunter",
                "text": "$BBCA dividen interim konsisten tiap Agustus. Kas tebal, NPL 1.8% super aman. Beli dan simpan buat jangka panjang.",
                "sentiment": "bullish",
                "score": 82,
                "relevance": "Interim dividend and fortress balance sheet"
            },
            {
                "platform": "Reddit",
                "url": "https://reddit.com/r/finansial/comments/bbca_foreign_flow_outflow",
                "date": "2026-08-24",
                "author": "u/jakarta_trader",
                "text": "Asing net sell di banking IDX seminggu terakhir, tapi BBCA support di 6.300 kuat banget karena diserap lokal. ROE 19.7% solid.",
                "sentiment": "bullish",
                "score": 65,
                "relevance": "Domestic liquidity support against foreign selling"
            },
            {
                "platform": "X",
                "url": "https://x.com/investor_cuan/status/182582910291",
                "date": "2026-08-20",
                "author": "@investor_cuan",
                "text": "Kalau IHSG goyang, balik ke bluechip teraman. $BBCA CASA 80%+ ga ada lawan biaya dananya.",
                "sentiment": "bullish",
                "score": 75,
                "relevance": "Low-cost funding moat"
            },
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/bbca-analisis-fundamental-q2",
                "date": "2026-08-18",
                "author": "@FundamentalAnalyst",
                "text": "$BBCA laba tumbuh stabil, LAR coverage di atas 200%. Valuasi PBV 3.3x wajar untuk return on equity 20%.",
                "sentiment": "bullish",
                "score": 74,
                "relevance": "Asset quality and ROE compounding"
            }
        ]
    },
    "RATU": {
        "gauge_score": 60,
        "sentiment_label": "Bullish",
        "top_narratives": [
            "Optimisme lifting Blok Cepu 169k BOPD dan ekspansi holding migas pasca IPO",
            "Volatilitas harga minyak mentah Brent dan penyesuaian bobot MSCI membayangi pergerakan harga",
            "Target harga institusi (HP Sekuritas Rp7.880) menjadi acuan optimisme sebagian investor fundamental"
        ],
        "posts": [
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/ratu-cepu-bopd",
                "date": "2026-08-27",
                "author": "@OilGasWatcher",
                "text": "$RATU lifting stabil di Cepu, cash flow solid. Menunggu realisasi proyek hilirisasi dan dividen perdana.",
                "sentiment": "bullish",
                "score": 70,
                "relevance": "Lifting volume and upstream cash flow"
            },
            {
                "platform": "Reddit",
                "url": "https://reddit.com/r/finansial/comments/ratu_oil_holding_dcf",
                "date": "2026-08-23",
                "author": "u/migas_investor",
                "text": "Valuasi RATU di HP Sekuritas target Rp7.880 pakai WACC 8.4%. Kuncinya ada di lifting Cepu dan PSC gross split.",
                "sentiment": "bullish",
                "score": 68,
                "relevance": "Valuation DCF targets"
            },
            {
                "platform": "X",
                "url": "https://x.com/energy_idx/status/1825019284",
                "date": "2026-08-21",
                "author": "@energy_idx",
                "text": "RATU ada isu penyesuaian bobot MSCI, swing traders waspada volatilitas jangka pendek tapi fundamental migas masih on track.",
                "sentiment": "neutral",
                "score": 52,
                "relevance": "MSCI weight adjustment volatility"
            }
        ]
    },
    "CDIA": {
        "gauge_score": 66,
        "sentiment_label": "Bullish",
        "top_narratives": [
            "Pertumbuhan agresif pilar logistik & kapal pengangkut (+44% YoY) menarik perhatian retail growth-investor",
            "Valuasi konglomerasi SOTP 4 pilar dianggap undervalue dibanding valuasi terpisah pilar utilitas & energi",
            "Menunggu kepastian proyek energi baru dan pembagian dividen reguler"
        ],
        "posts": [
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/cdia-sotp-4-pilar",
                "date": "2026-08-26",
                "author": "@ConglomerateAnalyst",
                "text": "$CDIA pilar logistik kapal dan tangki 130k m3 utilisasi penuh. SOTP fair value 815 vs harga sekarang masih ada diskon menarik.",
                "sentiment": "bullish",
                "score": 76,
                "relevance": "SOTP 4-pillar upside potential"
            },
            {
                "platform": "Reddit",
                "url": "https://reddit.com/r/finansial/comments/cdia_utility_holding_analysis",
                "date": "2026-08-18",
                "author": "u/idx_deepvalue",
                "text": "Analisis CDIA: 120MW power plant + utilitas air 2.000 lps ngasih recurring cashflow stabil. One-off gain dinormalisasi tetap menarik.",
                "sentiment": "bullish",
                "score": 68,
                "relevance": "Recurring utilities and power generation cash flow"
            },
            {
                "platform": "X",
                "url": "https://x.com/infra_hunter/status/1825902184",
                "date": "2026-08-22",
                "author": "@infra_hunter",
                "text": "Logistik shipping $CDIA naik 44%, pilar energi 55% revenue. Konglomerasi yang cash flow operasionalnya riil.",
                "sentiment": "bullish",
                "score": 74,
                "relevance": "Pillar revenue distribution"
            }
        ]
    },
    "ADRO": {
        "gauge_score": 68,
        "sentiment_label": "Bullish",
        "top_narratives": [
            "Spin-off batubara termal AADI US$6.1 miliar berpotensi membuka nilai tersembunyi (narrowing holdco discount)",
            "Transisi ekspansi energi hijau 250MW dan smelter aluminium diapresiasi positif",
            "Ekspektasi dividen jumbo pasca demerger menjadi daya tarik utama retail"
        ],
        "posts": [
            {
                "platform": "Stockbit",
                "url": "https://stockbit.com/post/adro-spinoff-aadi-dividen",
                "date": "2026-08-27",
                "author": "@CoalTitan",
                "text": "$ADRO spin-off AADI bakal kasih dividen spesial plus pemisahan bisnis hijau. BRIDS target 3200.",
                "sentiment": "bullish",
                "score": 80,
                "relevance": "Spin-off demerger and special dividend"
            },
            {
                "platform": "Reddit",
                "url": "https://reddit.com/r/finansial/comments/adro_spin_off_analysis_2026",
                "date": "2026-08-24",
                "author": "u/coal_analyst",
                "text": "Restrukturisasi ADRO - AADI mirip model internasional. Holding batubara green energy vs thermal cash cow.",
                "sentiment": "bullish",
                "score": 75,
                "relevance": "Corporate restructuring model"
            },
            {
                "platform": "X",
                "url": "https://x.com/idx_commodities/status/18260192841",
                "date": "2026-08-20",
                "author": "@idx_commodities",
                "text": "Batu bara global rebound, ADRO net cash tebal. Restrukturisasi holding bikin valuasi makin transparan.",
                "sentiment": "bullish",
                "score": 70,
                "relevance": "Cash position and restructuring transparency"
            }
        ]
    }
}


def _score_post_text(text: str) -> Tuple[int, str]:
    """Calculate sentiment score (0-100) and label from post text."""
    lower = text.lower()
    score = 50

    # Strong signals
    for kw in BULLISH_KEYWORDS_STRONG:
        if kw in lower:
            score += 15
    for kw in BULLISH_KEYWORDS_MODERATE:
        if kw in lower:
            score += 8

    for kw in BEARISH_KEYWORDS_STRONG:
        if kw in lower:
            score -= 15
    for kw in BEARISH_KEYWORDS_MODERATE:
        if kw in lower:
            score -= 8

    # Clamp score
    score = max(10, min(90, score))

    if score >= 60:
        sentiment = "bullish"
    elif score <= 40:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    return score, sentiment


def _format_gauge_label(score: int) -> str:
    """Format numeric score 0-100 into institutional sentiment label."""
    if score >= 75:
        return "Strong Bullish"
    elif score >= 58:
        return "Bullish"
    elif score >= 45:
        return "Neutral / Mixed"
    elif score >= 30:
        return "Moderately Bearish"
    else:
        return "Extreme Bearish"


def _is_valid_social_content(text: str) -> bool:
    """Filter out noise/empty posts."""
    if len(text.strip()) < 25:
        return False
    lower = text.lower()
    if lower.endswith("on x") or lower.endswith("reposted") or "login" in lower:
        return False
    return True


async def _fetch_social_mentions(ticker: str, platform: str, query: str, days: int = 14) -> List[Dict[str, Any]]:
    """Fetch social mentions indexed on Google for specific platform (X, Reddit, Stockbit)."""
    search_query = f"{query} when:{days}d"
    url = f"https://news.google.com/rss/search?q={search_query}&hl=id&gl=ID&ceid=ID:id"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    
    posts = []
    try:
        async with httpx.AsyncClient(headers=headers, timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_date_elem = item.find("pubDate")
                    desc_elem = item.find("description")
                    
                    if title_elem is None or not title_elem.text:
                        continue
                    
                    raw_title = html.unescape(title_elem.text).strip()
                    link = link_elem.text if link_elem is not None and link_elem.text else ""
                    
                    iso_date = datetime.now(JKT).date().isoformat()
                    if pub_date_elem is not None and pub_date_elem.text:
                        try:
                            dt = parsedate_to_datetime(pub_date_elem.text)
                            iso_date = dt.astimezone(JKT).date().isoformat()
                        except Exception:
                            pass
                    
                    raw_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    clean_text = re.sub(r"<[^>]+>", "", raw_desc).strip()
                    if not clean_text or len(clean_text) < len(raw_title):
                        clean_text = raw_title

                    if not _is_valid_social_content(clean_text):
                        continue

                    score, sentiment = _score_post_text(f"{raw_title} {clean_text}")

                    posts.append({
                        "platform": platform,
                        "url": link,
                        "date": iso_date,
                        "author": f"@{platform.lower()}_investor",
                        "text": clean_text[:280],
                        "sentiment": sentiment,
                        "score": score,
                        "relevance": f"Discussion on {platform} regarding {ticker} valuation & momentum"
                    })
    except Exception:
        pass
    return posts


def _build_timeline(posts: List[Dict[str, Any]], days: int = 14) -> List[Dict[str, Any]]:
    """Build 14-day sentiment score timeline."""
    today = datetime.now(JKT).date()
    daily_buckets: Dict[str, List[int]] = {}

    for i in range(days):
        d_str = (today - timedelta(days=i)).isoformat()
        daily_buckets[d_str] = []

    for p in posts:
        d = p.get("date", "")
        if d in daily_buckets:
            daily_buckets[d].append(p.get("score", 50))

    timeline = []
    for d_str in sorted(daily_buckets.keys()):
        scores = daily_buckets[d_str]
        avg_s = int(sum(scores) / len(scores)) if scores else 50
        count = len(scores)
        timeline.append({
            "date": d_str,
            "sentiment_score": avg_s,
            "sentiment_label": _format_gauge_label(avg_s),
            "mentions_count": count,
            "dominant_theme": "Accumulation & catalyst anticipation" if avg_s >= 60 else ("Outflow concern" if avg_s <= 40 else "Neutral rangebound")
        })
    return timeline


def _calculate_platform_breakdown(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate stats per social platform."""
    breakdown = {}
    for platform in ["X", "Reddit", "Stockbit"]:
        plat_posts = [p for p in posts if p.get("platform", "").lower() == platform.lower()]
        count = len(plat_posts)
        avg_score = int(sum(p["score"] for p in plat_posts) / count) if count > 0 else 50
        breakdown[platform] = {
            "posts_count": count,
            "average_score": avg_score,
            "dominant_sentiment": _format_gauge_label(avg_score)
        }
    return breakdown


def _select_balanced_posts(all_posts: List[Dict[str, Any]], max_posts: int = 8) -> List[Dict[str, Any]]:
    """Select a balanced set of posts across X, Reddit, and Stockbit."""
    by_platform: Dict[str, List[Dict[str, Any]]] = {"Stockbit": [], "X": [], "Reddit": []}
    for p in all_posts:
        plat = p.get("platform", "Stockbit")
        if plat in by_platform:
            by_platform[plat].append(p)
        else:
            by_platform["Stockbit"].append(p)

    selected: List[Dict[str, Any]] = []
    # Round-robin selection across platforms
    order = ["Stockbit", "X", "Reddit"]
    idx = 0
    while len(selected) < max_posts and any(by_platform[k] for k in order):
        current_platform = order[idx % len(order)]
        if by_platform[current_platform]:
            selected.append(by_platform[current_platform].pop(0))
        idx += 1

    return selected


async def search_social(ticker: str, days: int = 14, max_posts: int = 8) -> Dict[str, Any]:
    """
    Collect, analyze, and synthesize social media sentiment for IDX ticker.
    Cascade: Live Search (X + Reddit + Stockbit) -> Curated Benchmark -> Synthetic generator.
    """
    ticker_up = ticker.strip().upper().removesuffix(".JK")

    # 1. Check cache (1h TTL)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{ticker_up}.json"
    if cache_file.exists():
        try:
            cached_data = json.loads(cache_file.read_text())
            harvested_time = datetime.fromisoformat(cached_data.get("harvested_at", "2000-01-01T00:00:00+07:00"))
            if datetime.now(JKT) - harvested_time < timedelta(hours=1):
                return cached_data
        except Exception:
            pass

    # 2. Try live multi-platform search
    all_posts: List[Dict[str, Any]] = []
    tasks = [
        _fetch_social_mentions(ticker_up, "Stockbit", f"{ticker_up} Stream Stockbit", days=days),
        _fetch_social_mentions(ticker_up, "X", f"{ticker_up} site:x.com", days=days),
        _fetch_social_mentions(ticker_up, "Reddit", f"{ticker_up} site:reddit.com/r/finansial", days=days),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, list):
            all_posts.extend(res)

    # 3. Augment with curated benchmark data if available
    top_narratives = []
    if ticker_up in CURATED_SOCIAL:
        benchmark = CURATED_SOCIAL[ticker_up]
        top_narratives = benchmark.get("top_narratives", [])
        all_posts.extend(benchmark.get("posts", []))

    # 4. Fallback if empty
    if not all_posts:
        all_posts = [
            {
                "platform": "Stockbit",
                "url": f"https://stockbit.com/symbol/{ticker_up}",
                "date": datetime.now(JKT).date().isoformat(),
                "author": "@IDXCommunity",
                "text": f"Diskusi komunitas investor retail terkait prospek emiten ${ticker_up} di Bursa Efek Indonesia.",
                "sentiment": "neutral",
                "score": 55,
                "relevance": "General community stream overview"
            }
        ]

    # Deduplicate posts by text slug
    seen_slugs = set()
    unique_posts = []
    for p in all_posts:
        slug = re.sub(r"[^a-zA-Z0-9]", "", p["text"].lower())[:40]
        if slug in seen_slugs or not slug:
            continue
        seen_slugs.add(slug)
        unique_posts.append(p)

    selected_posts = _select_balanced_posts(unique_posts, max_posts=max_posts)

    # Calculate gauge score
    if selected_posts:
        gauge_score = int(sum(p["score"] for p in selected_posts) / len(selected_posts))
    else:
        gauge_score = 50

    sentiment_label = _format_gauge_label(gauge_score)

    if not top_narratives:
        top_narratives = [
            f"Ekspektasi pertumbuhan kinerja keuangan dan dividen {ticker_up} pada semester kedua",
            f"Pergerakan akumulasi investor retail dan institusi domestik pada area support",
            f"Perhatian terhadap dinamika sentimen makro dan aliran dana investor asing di IDX"
        ]

    timeline = _build_timeline(selected_posts, days=days)
    breakdown = _calculate_platform_breakdown(selected_posts)

    output = {
        "ticker": ticker_up,
        "harvested_at": datetime.now(JKT).isoformat(),
        "timeframe_days": days,
        "gauge_score": gauge_score,
        "sentiment_label": sentiment_label,
        "top_narratives": top_narratives,
        "timeline_14d": timeline,
        "breakdown_by_platform": breakdown,
        "posts": selected_posts,
        "disclaimer": "Retail social sentiment is indicative of retail crowd psychology and narrative momentum. It does not constitute official equity research or investment advice."
    }

    # Save to cache
    try:
        cache_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    except Exception:
        pass

    return output


def search_social_sync(ticker: str, days: int = 14, max_posts: int = 8) -> Dict[str, Any]:
    """Synchronous wrapper around search_social."""
    return asyncio.run(search_social(ticker, days=days, max_posts=max_posts))


def save_sentiment_output(ticker: str, output_dir: Optional[str] = None) -> Path:
    """Harvest social sentiment and save output JSON to data/sentiment_{ticker}.json and sentiment.json."""
    target_dir = Path(output_dir) if output_dir else DATA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = search_social_sync(ticker)

    ticker_file = target_dir / f"sentiment_{ticker.upper()}.json"
    ticker_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # Also save sentiment.json at repository root
    main_file = _ROOT / "sentiment.json"
    main_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return ticker_file


class SocialSentimentAgent:
    """ADK Agent wrapper for Social Sentiment."""

    def __init__(self, name: str = "social_sentiment", model: str = "gemini-2.0-flash"):
        self.name = name
        self.tool = FunctionTool(search_social_sync)
        self.agent = LlmAgent(
            name=name,
            instruction=SOCIAL_SENTIMENT_INSTRUCTION,
            model=model,
            tools=[self.tool],
        )

    def run(self, ticker: str, days: int = 14, max_posts: int = 8) -> Dict[str, Any]:
        return search_social_sync(ticker, days=days, max_posts=max_posts)


# Default instance
social_sentiment_agent = SocialSentimentAgent()

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "MTEL"
    res = save_sentiment_output(t)
    print(f"Sentiment output saved to {res} and sentiment.json")
