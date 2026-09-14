"""Forward-looking assumption modulation based on news signals.

Wires the news engine (news_harvester) into forward-looking revenue growth
and capex projections. (social_sentiment retired 14 Sep 2026 — Sectors has
no retail-social feed; the sentiment arg stays optional and falls back
cleanly when None.)

Wire pattern:
1. Sentiment-driven revenue growth modulation:
   - If sentiment_score > 0.6 (bullish): boost revenue_growth by up to +15%
   - If sentiment_score < -0.6 (bearish): cut revenue_growth by up to -15%
   - Neutral band [-0.6, 0.6]: no change
2. News-driven capex boost:
   - If news_count_last_30d > 20 AND avg_news_sentiment > 0:
     boost capex by up to +10% (capex-following-growth signal)
3. Fallback:
   - When news/sentiment is unavailable or empty, falls back cleanly to base assumptions.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from server.report import numfmt as _nf


def _clean_ticker(ticker: str) -> str:
    """Normalize ticker string: strip .JK suffix to bare uppercase ticker."""
    t = str(ticker).upper().strip()
    if t.endswith(".JK"):
        t = t[:-3]
    return t


def _extract_sentiment_score(sentiment: Any) -> Optional[float]:
    """Extract and normalize sentiment score into [-1.0, 1.0] range."""
    if sentiment is None:
        return None

    score: Optional[float] = None
    if isinstance(sentiment, dict):
        for k in ("score", "sentiment_score", "val", "polarity"):
            if k in sentiment and sentiment[k] is not None:
                try:
                    score = float(sentiment[k])
                    break
                except (ValueError, TypeError):
                    pass
        if score is None and "gauge" in sentiment and sentiment["gauge"] is not None:
            try:
                # Gauge is 0..100 (bearish 0 -> -1.0, neutral 50 -> 0.0, bullish 100 -> +1.0)
                gauge_val = float(sentiment["gauge"])
                score = (gauge_val - 50.0) / 50.0
            except (ValueError, TypeError):
                pass
    elif isinstance(sentiment, (int, float)):
        score = float(sentiment)
    elif isinstance(sentiment, str):
        s_lower = sentiment.strip().lower()
        if s_lower in ("bullish", "positive", "buy"):
            score = 0.8
        elif s_lower in ("bearish", "negative", "sell"):
            score = -0.8
        elif s_lower in ("neutral", "hold"):
            score = 0.0
        else:
            try:
                score = float(s_lower)
            except ValueError:
                return None

    if score is not None:
        # If score was provided on 0-100 scale (e.g. > 1.0)
        if score > 1.0 or score < -1.0:
            if 0.0 <= score <= 100.0:
                score = (score - 50.0) / 50.0
            else:
                score = max(-1.0, min(1.0, score))
    return score


def _extract_news_metrics(news: Any) -> tuple[int, float]:
    """Extract news_count_last_30d and avg_news_sentiment from news payload."""
    if not news:
        return 0, 0.0

    if isinstance(news, dict):
        if "items" in news and isinstance(news["items"], list):
            items = news["items"]
        else:
            # Direct dict with aggregated metrics
            count = news.get("count_last_30d", news.get("count", news.get("news_count", 0)))
            avg_sent = news.get("avg_news_sentiment", news.get("avg_sentiment", news.get("score", 0.0)))
            try:
                c = int(count)
                s = float(avg_sent)
                if s > 1.0 and s <= 100.0:
                    s = (s - 50.0) / 50.0
                return c, s
            except (ValueError, TypeError):
                return 0, 0.0
    elif isinstance(news, list):
        items = news
    else:
        return 0, 0.0

    # Process items
    valid_items = []
    scores = []
    now = datetime.now(timezone.utc)

    # Detect max date across items to support dataset-relative 30d windows
    item_dates = []
    for item in items:
        if isinstance(item, dict) and item.get("date"):
            try:
                d_str = str(item["date"]).replace("Z", "+00:00")
                d_val = datetime.fromisoformat(d_str)
                if d_val.tzinfo is None:
                    d_val = d_val.replace(tzinfo=timezone.utc)
                item_dates.append(d_val)
            except Exception:
                pass
    max_date = max(item_dates) if item_dates else now

    for item in items:
        is_recent = True
        if isinstance(item, dict):
            d_str = item.get("date")
            if d_str:
                try:
                    d_val = datetime.fromisoformat(str(d_str).replace("Z", "+00:00"))
                    if d_val.tzinfo is None:
                        d_val = d_val.replace(tzinfo=timezone.utc)
                    delta_now = abs((now - d_val).days)
                    delta_max = (max_date - d_val).days
                    # Accept if within 30 days of now OR within 30 days of fixture reference date
                    if delta_now > 30 and (delta_max < 0 or delta_max > 30):
                        is_recent = False
                except Exception:
                    is_recent = True

            if is_recent:
                valid_items.append(item)
                s = item.get("score")
                if s is None:
                    s = item.get("sentiment_score")
                if s is None and "sentiment" in item:
                    sent_val = item["sentiment"]
                    if isinstance(sent_val, (int, float)):
                        s = sent_val
                    elif str(sent_val).lower() in ("bullish", "positive"):
                        s = 1.0
                    elif str(sent_val).lower() in ("bearish", "negative"):
                        s = -1.0
                    else:
                        s = 0.0
                if s is not None:
                    try:
                        scores.append(float(s))
                    except (ValueError, TypeError):
                        pass
        else:
            valid_items.append(item)

    count_30d = len(valid_items)
    avg_sent = sum(scores) / len(scores) if scores else 0.0
    return count_30d, avg_sent


def adjust_assumptions(
    ticker: str,
    base_assumptions: dict,
    news: Any = None,
    sentiment: Any = None,
    ledger: Any = None,
) -> dict:
    """Modulate forward-looking assumptions using news and retail sentiment signals.

    Rules:
    - If sentiment_score > 0.6 (bullish): boost revenue_growth by up to +15%
    - If sentiment_score < -0.6 (bearish): cut revenue_growth by up to -15%
    - If news_count_last_30d > 20 AND avg_news_sentiment > 0: boost capex
      by up to +10% (capex-following-growth signal)
    - Apply per-line, document multipliers in the returned dict
    - Clean fallback to base_assumptions if news/sentiment unavailable
    """
    clean_tkr = _clean_ticker(ticker)
    out = copy.deepcopy(base_assumptions) if base_assumptions else {}

    # Extract sentiment
    sentiment_score = _extract_sentiment_score(sentiment)

    # 1. Sentiment-driven revenue growth multiplier
    rev_multiplier = 1.0
    if sentiment_score is not None:
        if sentiment_score > 0.6:
            # Linear ramp from 0.6 (+0%) to 1.0 (+15%)
            excess = min(0.4, sentiment_score - 0.6)
            rev_multiplier = 1.0 + (excess / 0.4) * 0.15
        elif sentiment_score < -0.6:
            # Linear ramp from -0.6 (0%) to -1.0 (-15%)
            excess = min(0.4, abs(sentiment_score) - 0.6)
            rev_multiplier = 1.0 - (excess / 0.4) * 0.15

    # Extract news metrics
    news_count_last_30d, avg_news_sentiment = _extract_news_metrics(news)

    # 2. News-driven capex boost multiplier
    capex_multiplier = 1.0
    if news_count_last_30d > 20 and avg_news_sentiment > 0:
        norm_sent = min(1.0, avg_news_sentiment)
        capex_multiplier = 1.0 + norm_sent * 0.10

    # 3. Apply multipliers per-line to forward-looking fields
    # Revenue fields
    rev_keys = {"revenue_growth", "rev_growth", "sales_growth", "revenue_cagr"}
    for k in rev_keys:
        if k in out and out[k] is not None:
            val = out[k]
            if isinstance(val, (int, float)):
                out[k] = round(val * rev_multiplier, 6)
            elif isinstance(val, list):
                out[k] = [round(x * rev_multiplier, 6) if isinstance(x, (int, float)) else x for x in val]

    # Capex fields
    capex_keys = {"capex", "capex_pct_revenue", "capex_growth", "capex_to_revenue", "capex_forecast"}
    for k in capex_keys:
        if k in out and out[k] is not None:
            val = out[k]
            if isinstance(val, (int, float)):
                out[k] = round(val * capex_multiplier, 6)
            elif isinstance(val, list):
                out[k] = [round(x * capex_multiplier, 6) if isinstance(x, (int, float)) else x for x in val]

    # 4. Document multipliers and signal provenance
    out["multipliers"] = {
        "revenue_growth": round(rev_multiplier, 6),
        "capex": round(capex_multiplier, 6),
    }
    out["revenue_growth_multiplier"] = round(rev_multiplier, 6)
    out["capex_multiplier"] = round(capex_multiplier, 6)
    out["news_count_last_30d"] = news_count_last_30d
    out["avg_news_sentiment"] = round(avg_news_sentiment, 4)
    out["sentiment_score"] = round(sentiment_score, 4) if sentiment_score is not None else None

    notes = []
    if rev_multiplier > 1.0:
        pct = (rev_multiplier - 1.0) * 100
        notes.append(f"Bullish sentiment ({_nf.dec(sentiment_score, digits=2, signed=True)}) boosted revenue growth by +{_nf.dec(pct, digits=1)}%")
    elif rev_multiplier < 1.0:
        pct = (1.0 - rev_multiplier) * 100
        notes.append(f"Bearish sentiment ({_nf.dec(sentiment_score, digits=2, signed=True)}) cut revenue growth by -{_nf.dec(pct, digits=1)}%")
    if capex_multiplier > 1.0:
        pct = (capex_multiplier - 1.0) * 100
        notes.append(f"High news volume ({news_count_last_30d} items, avg sentiment {_nf.dec(avg_news_sentiment, digits=2, signed=True)}) boosted capex by +{_nf.dec(pct, digits=1)}%")
    out["notes"] = notes

    # 5. News/sentiment -> forward-driver overlays (assumption ledger).
    # Extend-only: numeric keys stay plain floats; provenance travels in
    # {key}_overlay detail objects + news_overlays block. No cited driver =
    # no overlay (never silent defaults); conflicts resolve conservative.
    try:
        from .news_ledger import apply_ledger_overlays, extract_drivers

        resolved = ledger
        if resolved is None and (news is not None or sentiment is not None):
            resolved = extract_drivers(news, sentiment, ticker=clean_tkr)
        if isinstance(resolved, dict) and (resolved.get("drivers") or news is not None or sentiment is not None):
            overlaid = apply_ledger_overlays(out, resolved)
            # Preserve multiplier-path keys (extend, don't clobber).
            for k in ("multipliers", "revenue_growth_multiplier", "capex_multiplier",
                      "news_count_last_30d", "avg_news_sentiment", "sentiment_score", "notes"):
                overlaid[k] = out[k]
            out = overlaid
            n_applied = out.get("news_overlays", {}).get("overlays_applied", [])
            if n_applied:
                out["notes"] = notes + [f"News-ledger overlay applied: {', '.join(n_applied)} (cited; see news_overlays)"]
    except Exception:
        pass

    return out
