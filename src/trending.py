"""
Trending topics fetcher.

Retrieves current viral/trending topics from:
  - Google Trends (via pytrends)
  - YouTube Data API v3 (optional, requires YOUTUBE_API_KEY)
  - Fallback curated categories when APIs are unavailable
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrendingTopic:
    """Represents a single trending topic."""

    title: str
    source: str
    rank: int = 0
    related_queries: list[str] = field(default_factory=list)
    category: str = ""

    def __str__(self) -> str:
        return f"[{self.source}] #{self.rank} – {self.title}"


class TrendingFetcher:
    """Fetches trending topics from multiple sources."""

    def __init__(
        self,
        youtube_api_key: Optional[str] = None,
        country: str = "US",
        max_topics: int = 10,
    ) -> None:
        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY", "")
        self.country = country
        self.max_topics = max_topics

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> list[TrendingTopic]:
        """Return a deduplicated list of trending topics from all available sources."""
        topics: list[TrendingTopic] = []

        google_topics = self._fetch_google_trends()
        if google_topics:
            topics.extend(google_topics)
            logger.info("Fetched %d topics from Google Trends", len(google_topics))

        if self.youtube_api_key:
            yt_topics = self._fetch_youtube_trending()
            if yt_topics:
                topics.extend(yt_topics)
                logger.info(
                    "Fetched %d topics from YouTube Trending", len(yt_topics)
                )

        if not topics:
            logger.warning(
                "No topics fetched from external APIs; using fallback topics."
            )
            topics = self._fallback_topics()

        # Deduplicate by normalised title
        seen: set[str] = set()
        unique: list[TrendingTopic] = []
        for t in topics:
            key = t.title.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(t)

        return unique[: self.max_topics]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_google_trends(self) -> list[TrendingTopic]:
        """Fetch trending searches from Google Trends."""
        try:
            from pytrends.request import TrendReq  # type: ignore

            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            df = pytrends.trending_searches(pn=self.country.lower())

            topics: list[TrendingTopic] = []
            for rank, row in enumerate(df.values.tolist(), start=1):
                title = str(row[0]).strip()
                if title:
                    topics.append(
                        TrendingTopic(
                            title=title,
                            source="Google Trends",
                            rank=rank,
                        )
                    )
            return topics[: self.max_topics]

        except Exception as exc:
            logger.warning("Google Trends fetch failed: %s", exc)
            return []

    def _fetch_youtube_trending(self) -> list[TrendingTopic]:
        """Fetch trending videos from YouTube Data API."""
        try:
            from googleapiclient.discovery import build  # type: ignore

            youtube = build("youtube", "v3", developerKey=self.youtube_api_key)
            request = youtube.videos().list(
                part="snippet",
                chart="mostPopular",
                regionCode=self.country,
                maxResults=self.max_topics,
                videoCategoryId="",
            )
            response = request.execute()

            topics: list[TrendingTopic] = []
            for rank, item in enumerate(response.get("items", []), start=1):
                snippet = item.get("snippet", {})
                title = snippet.get("title", "").strip()
                category = snippet.get("categoryId", "")
                if title:
                    topics.append(
                        TrendingTopic(
                            title=title,
                            source="YouTube Trending",
                            rank=rank,
                            category=category,
                        )
                    )
            return topics

        except Exception as exc:
            logger.warning("YouTube Trending fetch failed: %s", exc)
            return []

    def _fallback_topics(self) -> list[TrendingTopic]:
        """Return a static set of currently popular evergreen categories as fallback."""
        fallback = [
            "Artificial Intelligence breakthroughs 2025",
            "How to make money online in 2025",
            "Latest smartphone review and comparison",
            "Home workout routine no equipment",
            "Easy recipes under 15 minutes",
            "Travel hacks and tips for budget travel",
            "Personal finance and investing for beginners",
            "Gaming news and new releases",
            "Mental health and productivity tips",
            "Electric vehicles and sustainable living",
        ]
        return [
            TrendingTopic(title=t, source="Fallback", rank=i + 1)
            for i, t in enumerate(fallback[: self.max_topics])
        ]
