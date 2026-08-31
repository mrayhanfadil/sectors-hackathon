"""
agents package — Multi-Agent Institutional Equity Research System.
Provides:
- collector_agent, collect_company_data, collect_company_data_sync, save_collector_output
- news_harvester_agent, search_news, search_news_sync, save_news_output
- social_sentiment_agent, search_social, search_social_sync, save_sentiment_output
"""

from agents.collector import (
    CollectorAgent,
    collector_agent,
    collect_company_data,
    collect_company_data_sync,
    save_collector_output,
)
from agents.news_harvester import (
    NewsHarvesterAgent,
    news_harvester_agent,
    search_news,
    search_news_sync,
    save_news_output,
)
from agents.social_sentiment import (
    SocialSentimentAgent,
    social_sentiment_agent,
    search_social,
    search_social_sync,
    save_sentiment_output,
)

__all__ = [
    "CollectorAgent",
    "collector_agent",
    "collect_company_data",
    "collect_company_data_sync",
    "save_collector_output",
    "NewsHarvesterAgent",
    "news_harvester_agent",
    "search_news",
    "search_news_sync",
    "save_news_output",
    "SocialSentimentAgent",
    "social_sentiment_agent",
    "search_social",
    "search_social_sync",
    "save_sentiment_output",
]
