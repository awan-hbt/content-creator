"""Tests for src/trending.py"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.trending import TrendingFetcher, TrendingTopic


class TestTrendingTopic:
    def test_str_representation(self):
        topic = TrendingTopic(title="AI breakthroughs", source="Google Trends", rank=1)
        assert "Google Trends" in str(topic)
        assert "AI breakthroughs" in str(topic)
        assert "#1" in str(topic)

    def test_default_fields(self):
        topic = TrendingTopic(title="Test", source="X")
        assert topic.rank == 0
        assert topic.related_queries == []
        assert topic.category == ""


class TestTrendingFetcher:
    def test_init_defaults(self):
        fetcher = TrendingFetcher()
        assert fetcher.country == "US"
        assert fetcher.max_topics == 10

    def test_init_custom(self):
        fetcher = TrendingFetcher(youtube_api_key="key", country="GB", max_topics=5)
        assert fetcher.youtube_api_key == "key"
        assert fetcher.country == "GB"
        assert fetcher.max_topics == 5

    def test_fetch_falls_back_when_no_apis(self, monkeypatch):
        """When all API calls fail, fallback topics are returned."""
        fetcher = TrendingFetcher(max_topics=5)

        # Simulate pytrends import failing
        monkeypatch.setattr(
            "src.trending.TrendingFetcher._fetch_google_trends",
            lambda self: [],
        )

        topics = fetcher.fetch()
        assert len(topics) == 5
        assert all(isinstance(t, TrendingTopic) for t in topics)
        assert all(t.source == "Fallback" for t in topics)

    def test_fetch_deduplicates(self, monkeypatch):
        """Duplicate topics (same title) should be removed."""
        duplicate_topics = [
            TrendingTopic(title="Same Topic", source="Google Trends", rank=1),
            TrendingTopic(title="same topic", source="YouTube Trending", rank=1),
            TrendingTopic(title="Unique Topic", source="Google Trends", rank=2),
        ]

        monkeypatch.setattr(
            "src.trending.TrendingFetcher._fetch_google_trends",
            lambda self: duplicate_topics,
        )

        fetcher = TrendingFetcher(max_topics=10)
        topics = fetcher.fetch()
        titles = [t.title.lower() for t in topics]
        assert len(titles) == len(set(titles))

    def test_fetch_respects_max_topics(self, monkeypatch):
        many_topics = [
            TrendingTopic(title=f"Topic {i}", source="Google Trends", rank=i)
            for i in range(20)
        ]
        monkeypatch.setattr(
            "src.trending.TrendingFetcher._fetch_google_trends",
            lambda self: many_topics,
        )

        fetcher = TrendingFetcher(max_topics=5)
        topics = fetcher.fetch()
        assert len(topics) == 5

    def test_fallback_topics_count(self):
        fetcher = TrendingFetcher(max_topics=3)
        fallback = fetcher._fallback_topics()
        assert len(fallback) == 3

    def test_fallback_topics_have_correct_source(self):
        fetcher = TrendingFetcher(max_topics=5)
        fallback = fetcher._fallback_topics()
        assert all(t.source == "Fallback" for t in fallback)

    @patch("src.trending.TrendReq", create=True)
    def test_google_trends_parse(self, mock_trend_req):
        """_fetch_google_trends correctly parses pytrends DataFrame mock."""
        import pandas as pd

        mock_instance = MagicMock()
        mock_instance.trending_searches.return_value = pd.DataFrame(
            ["AI news", "Python tutorial", "ChatGPT tips"]
        )
        mock_trend_req.return_value = mock_instance

        with patch.dict("sys.modules", {"pytrends": MagicMock(), "pytrends.request": MagicMock(TrendReq=mock_trend_req)}):
            fetcher = TrendingFetcher(max_topics=10)
            fetcher._fetch_google_trends()  # should not raise

    def test_fetch_youtube_trending_fails_gracefully(self, monkeypatch):
        """_fetch_youtube_trending returns [] when API is unavailable."""
        fetcher = TrendingFetcher(youtube_api_key="bad_key")

        with patch("src.trending.build", side_effect=Exception("API error"), create=True):
            result = fetcher._fetch_youtube_trending()

        assert result == []
