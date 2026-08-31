"""
verify_agents.py — T06 verification script for Collector + News Harvester + Social Sentiment agents.
Verifies:
1. agents.collector: ADK wrapper + idx_postgres / fallback + JSON schema + collector.json
2. agents.news_harvester: search_news + tier breakdown + key catalysts + news.json
3. agents.social_sentiment: search_social + gauge score 0-100 + top narratives + timeline + sentiment.json
4. Quintet coverage: RATU, CDIA, MTEL, BBCA, ADRO
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Set root
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from agents.collector import collect_company_data_sync, save_collector_output, collector_agent
from agents.news_harvester import search_news_sync, save_news_output, news_harvester_agent
from agents.social_sentiment import search_social_sync, save_sentiment_output, social_sentiment_agent

QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]

def verify_all():
    print("=== T06 AGENTS VERIFICATION ===")
    print(f"Working Directory: {_ROOT}")
    print()

    # 1. Verify Collector Agent
    print("--- 1. Testing Collector Agent ---")
    for ticker in QUINTET:
        data = collect_company_data_sync(ticker)
        assert data["ticker"] == ticker, f"Ticker mismatch: {data['ticker']} != {ticker}"
        assert "company_info" in data, f"Missing company_info for {ticker}"
        assert data["prices_count"] > 0, f"Prices count 0 for {ticker}"
        assert "operational_kpis" in data, f"Missing operational_kpis for {ticker}"
        assert "segment_breakdown" in data, f"Missing segment_breakdown for {ticker}"
        print(f"  ✓ Collector [{ticker}]: close={data.get('latest_close_price')}, prices={data['prices_count']}, sources={data['sources_used']}")

    # Save MTEL as default collector.json
    save_collector_output("MTEL")
    print("  ✓ Saved data/collector_MTEL.json and collector.json")
    print()

    # 2. Verify News Harvester Agent
    print("--- 2. Testing News Harvester Agent ---")
    for ticker in QUINTET:
        news_data = search_news_sync(ticker, days=30, max_articles=8)
        assert news_data["ticker"] == ticker, f"News ticker mismatch: {news_data['ticker']} != {ticker}"
        assert len(news_data["articles"]) > 0, f"No news articles for {ticker}"
        assert "tier_breakdown" in news_data, f"Missing tier_breakdown for {ticker}"
        assert "key_catalysts" in news_data, f"Missing key_catalysts for {ticker}"
        t1_count = news_data["tier_breakdown"].get("Tier1", 0)
        print(f"  ✓ News Harvester [{ticker}]: articles={news_data['total_count']}, Tier1={t1_count}, catalysts={len(news_data['key_catalysts'])}")

    # Save MTEL as default news.json
    save_news_output("MTEL")
    print("  ✓ Saved data/news_MTEL.json and news.json")
    print()

    # 3. Verify Social Sentiment Agent
    print("--- 3. Testing Social Sentiment Agent ---")
    for ticker in QUINTET:
        sent_data = search_social_sync(ticker, days=14, max_posts=8)
        assert sent_data["ticker"] == ticker, f"Sentiment ticker mismatch: {sent_data['ticker']} != {ticker}"
        assert 0 <= sent_data["gauge_score"] <= 100, f"Gauge score out of range: {sent_data['gauge_score']}"
        assert len(sent_data["top_narratives"]) >= 1, f"Missing narratives for {ticker}"
        assert len(sent_data["timeline_14d"]) == 14, f"Timeline must be 14 days, got {len(sent_data['timeline_14d'])}"
        assert "breakdown_by_platform" in sent_data, f"Missing platform breakdown for {ticker}"
        print(f"  ✓ Social Sentiment [{ticker}]: score={sent_data['gauge_score']}/100 ({sent_data['sentiment_label']}), narratives={len(sent_data['top_narratives'])}, posts={len(sent_data['posts'])}")

    # Save MTEL as default sentiment.json
    save_sentiment_output("MTEL")
    print("  ✓ Saved data/sentiment_MTEL.json and sentiment.json")
    print()

    # 4. Verify ADK Wrappers
    print("--- 4. Testing ADK Agent Wrappers ---")
    assert collector_agent.name == "collector"
    assert news_harvester_agent.name == "news_harvester"
    assert social_sentiment_agent.name == "social_sentiment"
    print("  ✓ All 3 ADK LlmAgent instances successfully initialized with FunctionTool")
    print()

    print("=== ALL T06 AGENTS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    verify_all()
